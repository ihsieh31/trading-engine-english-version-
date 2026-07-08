# Trading Engine — Automated US Stock Trading System

**v0.3.0** — Paper Trading Only

A fully automated S&P 500 trading system powered by **technical screening → LLM multi-agent analysis → risk-controlled execution → post-trade reflection learning**. Built with event-driven architecture, plugin system, MCP AI integration, and a built-in trading knowledge base.

> **Paper Trading Only** — Uses Alpaca Paper Trading API with $100K virtual money. No real capital at risk.

---

## Features

- **Automated Pipeline**: Screener → Deep Analysis → Monitor → Reflection (4 stages)
- **Multi-Agent LLM Architecture**: AnalystAgent, RiskAgent, ChairmanAgent vote-based decision making
- **Technical Screening**: MA20/50, RSI, MACD, volume ratio — pure pandas, no LLM cost
- **Regime Detection**: Automatically detects bull/bear/ranging/high_vol markets, adjusts position sizing
- **Risk Management**: Kelly Criterion sizing, circuit breaker, sector exposure limits, stop-loss/take-profit
- **Knowledge Base**: Built-in library of 60 trading & economics books (48 Gutenberg classics + 4 guides + 8 condensed classics)
- **Interactive Setup**: First run walks you through API configuration step by step (English/中文)
- **MCP Server**: 13 tools for AI assistant integration (Claude, etc.)
- **Web Dashboard**: Real-time monitoring on localhost:8899
- **Plugin System**: Dynamic loading via plugin manifest
- **Supports any OpenAI-compatible LLM**: OpenAI, Anthropic, DeepSeek, Groq, Google AI, OpenRouter, etc.

---

## Quick Start

```bash
git clone https://github.com/ihsieh31/trading-engine-english-version-.git
cd trading-engine-english-version-
./run.sh
```

The first run launches an interactive setup wizard:

1. Choose language (English / 中文)
2. Enter LLM API Key, Endpoint, and Model ID (any OpenAI-compatible provider)
3. Enter Alpaca API Key + Secret (free paper trading)
4. Enter News API key(s) — Tavily / Brave / SerpAPI (optional)
5. Enter Telegram Bot Token + Chat ID (optional)

It will automatically install dependencies, run a health check, and present the main menu.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     scheduler.py (Daemon)                        │
│   Schedules 4 stages sequentially + EventBus event-driven        │
│                                                                  │
│  STAGE 1 ── screener.py        Technical screening (no LLM)      │
│  STAGE 2 ── deep_analyzer.py   LLM multi-agent deep analysis     │
│  STAGE 3 ── monitor.py         Intraday monitoring (every 30s)   │
│  STAGE 4 ── reflection_agent.py Post-trade reflection + rule     │
│                                  extraction into knowledge base  │
└─────────────────────────────────────────────────────────────────┘
```

### Pipeline Flow

```
Every Monday pre-market
  Universe (S&P 500)
    │
    ▼ STAGE 1
  Screener (MA20/50, RSI, MACD, Volume → TOP 15)
    │
    ▼ STAGE 2
  Deep Analyzer (Multi-Agent LLM → AgentProposal)
    │  └─ Injects economics knowledge + trading experience
    │
    ▼ STAGE 3 (every 30s during trading hours)
  Monitor (Price check → Risk check → Chairman decision → Order)
    │
    ├── Entry: ChairmanAgent votes BUY + RiskAgent approves + technical confirm
    ├── Exit: Stop-loss -5% / Take-profit +15% / LLM turns SELL / Circuit breaker
    └── Circuit: Daily loss >3% or MDD >15%
    │
    ▼ Post-market (STAGE 4)
  Reflection (Analyze closed trades → Extract rules → Knowledge base)
```

---

## Requirements

- **Python 3.11+**
- **Alpaca Paper Trading account** — [Free signup](https://alpaca.markets)
- **LLM API** — Any OpenAI-compatible provider
- **News API** (optional) — Tavily / Brave / SerpAPI

---

## Configuration (.env)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `OPENAI_COMPATIBLE_API_KEY` | — | LLM API Key |
| `LLM_BACKEND_URL` | — | API endpoint (e.g. `https://api.openai.com/v1`) |
| `DEEP_THINK_MODEL` | — | Model ID for deep analysis |
| `QUICK_THINK_MODEL` | — | Model ID for quick tasks |
| `ALPACA_API_KEY` | — | Alpaca Paper API Key |
| `ALPACA_API_SECRET` | — | Alpaca Paper Secret |
| `IS_PAPER` | `true` | Paper trading mode |
| `TAVILY_API_KEYS` | — | News API keys |
| `INITIAL_CAPITAL` | `100000` | Virtual capital |
| `MAX_POSITION_PCT` | `0.10` | Max position size (10%) |
| `STOP_LOSS_PCT` | `0.05` | Stop loss |
| `TAKE_PROFIT_PCT` | `0.15` | Take profit |
| `OBSIDIAN_VAULT_PATH` | `./knowledge` | Knowledge base path |

Full list in [.env.example](.env.example).

---

## Knowledge Base

The system includes a built-in knowledge base of **60 trading books and guides**:

| Source | Count | Description |
|--------|-------|-------------|
| **Project Gutenberg** | 48 | Public domain economics & finance classics |
| **Trading Guides** | 4 | Rules cheatsheet, options guide, learning path, SEC EDGAR guide |
| **Classic Trading Books** | 8 | Condensed principles from Wyckoff, Gann, Loeb, Thorp, Hamilton, Nelson, NYSE history |

Located in `knowledge/` — no setup needed. The system automatically indexes and injects relevant knowledge into LLM analysis prompts.

---

## Safety Mechanisms

| Mechanism | Description |
|-----------|-------------|
| **Circuit Breaker** | Daily loss >3% or MDD >15% auto-trips |
| **Kill Switch** | `touch data/.kill` to stop all trading |
| **Sector Exposure** | Max 25% per sector |
| **Stop-Loss/Take-Profit** | Automatic OCO bracket orders |
| **Rating Freshness** | Ratings expire after 7 days |
| **Technical Confirmation** | Requires MA trend + RSI confirmation even on BUY rating |
| **Agent Confidence Calibration** | ChairmanAgent adjusts vote weights by historical accuracy |
| **Risk Veto** | RiskAgent can veto any trade based on regime/exposure/Kelly |

---

## Usage

```bash
# Full automated pipeline
python scheduler.py

# One-time deep analysis
python deep_analyzer.py

# Web dashboard
python dashboard.py

# Backtest
python backtest.py

# MCP server (AI assistant integration)
python mcp_server.py

# Health check
python dry_run.py
```

---

## V2 Multi-Agent Architecture

The system features a complete multi-agent collaboration framework:

```
  AnalystAgent ──┐
  ScreenerAgent ──┤
  ExecutionAgent ─┤
                  │  AgentProposals
                  ▼
            RiskAgent ──── RiskAssessment
                  │
                  ▼
           ChairmanAgent ──── ChairmanDecision
                  │
                  ▼
           ExecutionAgent ──── Order
                  │
                  ▼
           EventBus ──── Persistence + WorkflowEngine
```

| Agent | Role | Input | Output |
|-------|------|-------|--------|
| **AnalystAgent** | LLM analysis (fundamental + technical + sentiment) | `AnalysisContext` | `AgentProposal` |
| **ScreenerAgent** | Quantitative screening (no LLM) | `PortfolioState` | `AgentProposal` |
| **ExecutionAgent** | Order execution + retry | `ChairmanDecision` | — |
| **RiskAgent** | Risk: Regime gate, Kelly sizing, sector/exposure limits | Market data + portfolio | `RiskAssessment` |
| **ChairmanAgent** | Aggregation: weighted voting → rule override → risk veto → LLM arbitration | Proposals + RiskAssessment | `ChairmanDecision` |

---

## Tech Stack

- **Python 3.11+**
- **Alpaca Trading API** (`alpaca-py`)
- **LLM**: OpenAI-compatible (any provider)
- **Vector DB**: chromadb + sentence-transformers
- **Web Dashboard**: Flask
- **Persistence**: SQLite (WAL mode) + JSONL dual-write
- **Plugin System**: Dynamic importlib loading
- **AI Integration**: MCP (Model Context Protocol) JSON-RPC 2.0

---

## Security

- All API keys stored in `.env` (git-ignored)
- Dashboard generates random auth token on startup
- CORS restricted to localhost
- MCP server over stdio (not exposed as network service)
- GitHub Action only triggers for repo owner
- No hardcoded secrets in codebase

---

## Knowledge Base Credits

- **Project Gutenberg** — [gutenberg.org](https://www.gutenberg.org) (48 public domain books)
- **Internet Archive** — [archive.org](https://archive.org) (classic trading book summaries)
- **Original guides** — Trading rules, options, SEC EDGAR, learning path

---

## Disclaimer

This is an **experimental automated trading system** operating in **Paper Trading** mode only. No real capital is at risk. The authors assume no responsibility for any financial losses incurred from using this software in live trading.

---

## License

MIT
