# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-05-16

### Added
- Initial MVP release
- Technical Agent (RSI-based) for 5 hardcoded large-cap NSE stocks
- Market Sentiment Agent using Nifty 50, India VIX, and global cues via Claude Haiku
- Stock Sentiment Agent using Google News RSS + Claude Haiku
- Sentiment Fusion module combining market + stock sentiment with weighted rules
- Linear orchestrator coordinating all agents per run
- Email notifier via Gmail SMTP
- Google Sheets logger for signal history
- GitHub Actions workflow scheduling runs every 15 minutes during market hours
- Agent packaging convention: `skill.md` + `connectors.py` + `agent.py` + `subagents.py` per agent
- Design documentation: `architecture.md`, `contracts.md`, `decisions.md`
