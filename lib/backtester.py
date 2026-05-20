"""
Backtester using vectorbt.

Replays the agent stack against historical daily data for a list of symbols
and produces per-agent and aggregated performance metrics.

Note: This is a simplification — historical replay uses daily candles, not
the 15-min candles the live system uses. Results indicate directional
hypothesis quality, not exact production replay.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import yfinance as yf

from agents.rsi import analyze as rsi_analyze
from agents.macd import analyze as macd_analyze
from agents.bollinger import analyze as bb_analyze
from agents.vwap import analyze as vwap_analyze
from lib.aggregator import aggregate as aggregate_signals
from lib.contracts import (
    Signal, ACTION_BUY, ACTION_SELL, ACTION_HOLD,
)

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    symbol: str
    days: int
    n_signals: int
    n_buy: int
    n_sell: int
    n_hold: int
    total_return_pct: float
    win_rate_pct: float
    sharpe_proxy: float
    max_drawdown_pct: float
    per_agent_hit_rate: dict   # {agent: hit_rate}


def _neutral_sentiment_signal(symbol: str) -> Signal:
    """Backtests don't replay news — use a neutral sentiment placeholder."""
    return Signal(
        agent="sentiment_fusion",
        symbol=symbol,
        action=ACTION_HOLD,
        confidence=0.5,
        reason="backtest: no historical news",
        metrics={},
    )


def _signal_to_position(action: str) -> int:
    """BUY=+1, SELL=-1, HOLD=0."""
    if action == ACTION_BUY:
        return 1
    if action == ACTION_SELL:
        return -1
    return 0


def backtest_symbol(symbol: str, days: int = 90, include_sentiment: bool = False) -> Optional[BacktestResult]:
    """
    Replay agents day-by-day against daily candles for the given symbol.

    Args:
      symbol: e.g. "RELIANCE.NS"
      days: how many trading days of history to replay
      include_sentiment: if False (default), uses neutral sentiment placeholder.
                        Backtesting real news sentiment requires historical news
                        which we don't have access to here.

    Returns:
      BacktestResult with aggregate metrics. None on failure.
    """
    try:
        # Pull extra history so indicators have warmup data
        warmup_buffer = 60
        period_days = days + warmup_buffer + 15  # extra for weekends/holidays
        df = yf.download(symbol, period=f"{period_days}d", interval="1d",
                         progress=False, auto_adjust=True)
        if df is None or df.empty:
            logger.warning(f"No data for {symbol}")
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
    except Exception as e:
        logger.error(f"Failed to fetch history for {symbol}: {e}")
        return None

    if len(df) < warmup_buffer + 10:
        logger.warning(f"Not enough history for {symbol}: only {len(df)} rows")
        return None

    closes = df["Close"]
    actions = []
    scores = []
    per_agent_actions = {"rsi": [], "macd": [], "bollinger": [], "vwap": []}

    # Slide a window through history; for each day, agents see only data up to that day
    for i in range(warmup_buffer, len(df) - 1):  # leave 1 day at end for forward return
        window = df.iloc[: i + 1]

        rsi_sig = rsi_analyze(symbol, window)
        macd_sig = macd_analyze(symbol, window)
        bb_sig = bb_analyze(symbol, window)
        vwap_sig = vwap_analyze(symbol, window)
        sent_sig = _neutral_sentiment_signal(symbol)

        per_agent = {
            "rsi": rsi_sig,
            "macd": macd_sig,
            "bollinger": bb_sig,
            "vwap": vwap_sig,
            "sentiment_fusion": sent_sig,
        }

        final_action, _, raw_score = aggregate_signals(per_agent)
        actions.append(final_action)
        scores.append(raw_score)
        per_agent_actions["rsi"].append(rsi_sig.action)
        per_agent_actions["macd"].append(macd_sig.action)
        per_agent_actions["bollinger"].append(bb_sig.action)
        per_agent_actions["vwap"].append(vwap_sig.action)

    # Forward returns: next-day return for each signal
    fwd_returns = closes.pct_change().shift(-1).iloc[warmup_buffer: len(df) - 1]
    fwd_returns = fwd_returns.reset_index(drop=True)

    # Aggregate metrics
    n_signals = len(actions)
    n_buy = actions.count(ACTION_BUY)
    n_sell = actions.count(ACTION_SELL)
    n_hold = actions.count(ACTION_HOLD)

    # Strategy returns: BUY captures forward return; SELL captures -forward return; HOLD = 0
    positions = pd.Series([_signal_to_position(a) for a in actions])
    strategy_returns = positions * fwd_returns
    strategy_returns = strategy_returns.dropna()

    # Total return (cumulative, simple)
    total_return = strategy_returns.sum() * 100
    # Sharpe proxy: mean/std (annualized would multiply by sqrt(252))
    sharpe = (strategy_returns.mean() / strategy_returns.std()) if strategy_returns.std() > 0 else 0.0
    sharpe_annual = sharpe * (252 ** 0.5)

    # Max drawdown on cumulative equity
    equity = (1 + strategy_returns).cumprod()
    drawdown = (equity / equity.cummax() - 1) * 100
    max_dd = float(drawdown.min())

    # Win rate among directional bets
    directional_idx = positions != 0
    wins = (strategy_returns[directional_idx] > 0).sum()
    total_directional = directional_idx.sum()
    win_rate = (wins / total_directional * 100) if total_directional > 0 else 0.0

    # Per-agent hit rate
    per_agent_hit = {}
    for agent_name, agent_actions in per_agent_actions.items():
        agent_positions = pd.Series([_signal_to_position(a) for a in agent_actions])
        agent_returns = agent_positions * fwd_returns
        directional = agent_positions != 0
        if directional.sum() > 0:
            agent_wins = (agent_returns[directional] > 0).sum()
            per_agent_hit[agent_name] = round(agent_wins / directional.sum() * 100, 1)
        else:
            per_agent_hit[agent_name] = 0.0

    return BacktestResult(
        symbol=symbol,
        days=days,
        n_signals=n_signals,
        n_buy=n_buy,
        n_sell=n_sell,
        n_hold=n_hold,
        total_return_pct=round(total_return, 2),
        win_rate_pct=round(win_rate, 1),
        sharpe_proxy=round(sharpe_annual, 2),
        max_drawdown_pct=round(max_dd, 2),
        per_agent_hit_rate=per_agent_hit,
    )


def print_result(r: BacktestResult) -> None:
    print(f"\n=== {r.symbol} ({r.days}d backtest) ===")
    print(f"Signals: {r.n_signals}   BUY={r.n_buy}  SELL={r.n_sell}  HOLD={r.n_hold}")
    print(f"Total return: {r.total_return_pct:+.2f}%")
    print(f"Win rate (directional): {r.win_rate_pct:.1f}%")
    print(f"Sharpe (annual proxy): {r.sharpe_proxy:.2f}")
    print(f"Max drawdown: {r.max_drawdown_pct:.2f}%")
    print(f"Per-agent hit rate:")
    for agent, rate in r.per_agent_hit_rate.items():
        print(f"  {agent:12s} {rate:5.1f}%")
