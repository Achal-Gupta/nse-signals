# Universe Agent — Skill Definition

## Role

Dynamically select the watchlist of stocks the system analyzes today.

In v0.2.0 this was hardcoded to 5 stocks. v0.3.0 expands to 40 stocks chosen
by composition: **20 Nifty 100 large-caps + 20 news-trending stocks**.

## When It Runs

Once per day at the first cycle after 9:15 AM IST (market open). The selected
universe is cached for the rest of the day and used by every subsequent run
until the next morning's refresh.

## Selection Logic

### Pool 1: Nifty 100 Baseline (20 stocks)

From `data/nifty_100_baseline.yaml`:
- Filter by:
  - Average daily volume over last 5 days > threshold (default ₹50 crore notional)
  - Price > ₹100 (excludes ultra-low-priced)
- Rank by average daily traded value
- Take top 20

### Pool 2: News-Hybrid (20 stocks)

Combines two streams:
- **News mentions:** Scrape Google News for Indian stock market headlines.
  Extract company names mentioned. Keep distinct companies.
- **Market movers:** Take top gainers + top losers from yfinance for Nifty 100
  + Nifty Midcap 100 lists.

Deduplicate, filter to NSE-listed only, take top 20.

### Final Set

Union of Pool 1 and Pool 2, deduplicated. If overlap reduces total below 40,
fill from Pool 1 by next-ranked stocks.

## Fallback

If any pool fails to produce results, fall back to a static safe list
(5 large caps from v0.1.0). Universe must never be empty.

## Output

Returns a `Universe` dataclass (see lib/contracts.py):

```python
@dataclass
class Universe:
    timestamp_ist: str
    stocks: list[dict]      # [{symbol, name, source: "nifty100" | "news_hybrid" | "fallback"}]
    pool1_size: int
    pool2_size: int
    overlaps: int           # how many were in both pools
    errors: list[str]       # any pool failures
```

The `source` field is logged to the Universe tab in Sheets so we can later
analyze whether news-hybrid stocks produce better signals than baseline.
