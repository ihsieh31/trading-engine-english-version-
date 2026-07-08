# Trading Engine — Automated US Stock Trading System <br><sub>v0.3.0</sub>

> **🌐 中文版**：[github.com/ihsieh31/trading-engine](https://github.com/ihsieh31/trading-engine)  
> **English Version**: This repo — [trading-engine-english-version](https://github.com/ihsieh31/trading-engine-english-version-)

A fully automated S&P 500 trading system built on **Technical Screening → LLM Multi-Agent Deep Analysis → Multi-Agent Risk Control & Decision Making → Intraday Monitoring → Auto Execution → Post-Trade Reflection Learning**. Features event-driven architecture, plugin system, MCP AI integration, and a built-in trading knowledge base.

> **Paper Trading Only** — Uses Alpaca Paper Trading API, 100% virtual capital, no real money at risk.

> **Setup**: First run `./run.sh` — choose English or 中文, interactive wizard guides you through API key configuration (OpenAI-compatible LLM, Alpaca, News APIs), auto-installs dependencies and runs health check.

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        scheduler.py (Daemon Controller)                    │
│  Schedules 4 stages sequentially + EventBus event-driven                  │
│                                                                          │
│  STAGE 1 ── screener.py        Technical screening (no LLM)              │
│                │                                                         │
│                ├── universe.py          S&P 500 / NASDAQ 100 constituents│
│                └── trading_calendar.py  NYSE trading calendar            │
│                                                                          │
│  STAGE 2 ── deep_analyzer.py    LLM Multi-Agent Deep Analysis            │
│                │                                                         │
│                ├── agents/             AnalystAgent (LLM fundamentals)   │
│                │                       ScreenerAgent (quantitative)      │
│                ├── news_service.py     Multi-source news                 │
│                ├── economics_kb.py     Economics knowledge (1,457 srcs)   │
│                └── knowledge_base.py   Trading experience/rule injection │
│                                                                          │
│  STAGE 3 ── monitor.py          Intraday Monitoring Engine (every 30s)   │
│                │                                                         │
│                ├── container.py       DI container: injects dependencies │
│                ├── agents/            RiskAgent (risk control)           │
│                │                      ChairmanAgent (decision agg.)      │
│                │                      ExecutionAgent (order execution)   │
│                ├── portfolio_manager  Capital mgmt + sector control      │
│                ├── order_manager      Order lifecycle                    │
│                ├── performance        Performance tracking               │
│                ├── safety             Circuit breaker                    │
│                └── strategy           Stop-loss/take-profit strategies   │
│                                                                          │
│  STAGE 4 ── reflection_agent.py Post-Trade Reflection + Rule Extraction  │
│                └── knowledge_base.py  chromadb vector storage             │
│                                                                          │
│    dashboard.py (optional) — Web monitoring panel (Flask, port 8899)     │
│    mcp_server.py (optional) — MCP AI integration server (13 tools)       │
│    plugin_host.py (optional) — Dynamic plugin loading system             │
└──────────────────────────────────────────────────────────────────────────┘
```

### Pipeline Flow

```
Every Monday Pre-Market
  Universe (S&P 500)
    │
    ▼ STAGE 1
  Screener (MA20/50, RSI, MACD, Volume Ratio → TOP 15)
    │
    ▼ STAGE 2
  Deep Analyzer (TradingAgents + Multi-Agent → AgentProposal)
    │  └─ Injects economics knowledge + trading experience + historical rules
    │
    ▼ STAGE 3 (every 30s during trading hours)
  Monitor (Price check → Risk check → Chairman decision → Auto order)
    │
    ├── Entry: ChairmanAgent votes BUY + RiskAgent approves + technical confirm
    ├── Exit: Stop-loss -5% / Take-profit +15% / LLM turns SELL / Circuit breaker
    └── Circuit breaker: Daily loss >3% or MDD >15%
    │
    ▼ After hours (STAGE 4)
  Reflection (Analyze closed trades → Extract trading rules → Knowledge base)
```

---

## V2 Multi-Agent Architecture

The system adds a complete multi-agent collaboration framework on top of the V1 Pipeline:

```
  AnalystAgent ──┐
  ScreenerAgent ──┤
  ExecutionAgent ─┤
  (Plugin) ───────┤
                  │  AgentProposals
                  ▼
            RiskAgent ──── RiskAssessment
                  │
                  ▼
           ChairmanAgent ──── ChairmanDecision
                  │
                  ▼
           ExecutionAgent ──── Order Execution
                  │
                  ▼
           EventBus ──── Event Persistence + WorkflowEngine State Machine
```

### Agent Descriptions

| Agent | Role | Input | Output |
|-------|------|-------|--------|
| **AnalystAgent** | LLM fundamental + technical + sentiment analysis | `AnalysisContext` (indicators, news, econ knowledge) | `AgentProposal` (rating, confidence, price_target) |
| **ScreenerAgent** | Quantitative screening (no LLM) | `PortfolioState` | `AgentProposal` (score >= 3 → BUY) |
| **ExecutionAgent** | Order execution + retry logic | `ChairmanDecision` | — |
| **RiskAgent** | Risk: Regime gate, Kelly sizing, sector exposure, total exposure | Market data + portfolio | `RiskAssessment` (approved, position_pct, veto_reason) |
| **ChairmanAgent** | Decision aggregation: weighted vote → rule override → risk veto → LLM arbitration (opt) | Proposals + RiskAssessment | `ChairmanDecision` (final_action, position_pct, vote_breakdown) |

### ChairmanAgent 4-Step Algorithm

1. **Confidence Calibration**: Adjust agent weights based on rolling historical accuracy from DB
2. **Weighted Voting**: weight = calibrated_confidence, compute weighted majority
3. **Rule Override**: Check MemoryService for high-confidence rules that override
4. **Risk Veto**: Force HOLD when RiskAgent's veto_reason is not None
5. **LLM Arbitration** (optional): If weighted majority < 60%, LLM breaks the tie

---

## Event-Driven Architecture (EventBus V2)

The system is fully event-driven. All modules communicate loosely through `EventBus`.

| Event Type | Trigger | Payload |
|-----------|---------|---------|
| `screener.candidates_ready` | Technical screening complete | `{count, tickers[]}` |
| `analyst.proposal_created` | Single ticker analyzed | `{ticker, rating, confidence}` |
| `analyst.batch_completed` | Batch analysis complete | `{count}` |
| `risk.assessment_created` | Risk assessment complete | `{ticker, approved}` |
| `chairman.decision_made` | Chairman decision complete | `{ticker, action}` |
| `order.submitted` | Order submitted | `{ticker, qty, order_id}` |
| `order.filled` | Order filled | `{ticker, qty, price}` |
| `order.failed` | Order failed | `{ticker, error}` |
| `circuit_breaker.tripped` | Circuit breaker triggered | `{reason}` |
| `position.closed` | Position closed | `{ticker, pnl}` |
| `reflection.completed` | Reflection complete | `{rule_id}` |
| `memory.rule_added` | New trading rule written | `{rule_id}` |
| `memory.rule_conflict_detected` | Rule conflict detected | `{existing_rule, new_rule}` |
| `workflow.state_changed` | Workflow state transition | `{from_state, to_state}` |
| `system.health_degraded` | System health degraded | `{metric, value}` |

All events are persisted to SQLite, queryable by `trace_id` / `workflow_id` for audit trails.

---

## Plugin System

Supports dynamic loading of third-party plugins via `plugin.json` manifest:

```json
{
  "id": "my_provider",
  "name": "My Custom News Provider",
  "version": "1.0.0",
  "entrypoint": "plugin.py:MyPlugin",
  "interfaces_implemented": ["INewsProvider"]
}
```

| Interface | Description |
|-----------|-------------|
| `INewsProvider` | News data source (search/search_market_news) |
| `INewsProviderPlugin` | Plugin-form news source |
| `IStrategyPlugin` | Custom trading strategy (evaluate) |

---

## MCP AI Integration (Model Context Protocol)

`mcp_server.py` exposes 13 tools over stdio JSON-RPC 2.0 for AI assistants (Claude, etc.) to query system state:

| Tool | Description |
|------|-------------|
| `get_account` | Account info (cash, equity, buying power) |
| `get_positions` | Current positions (qty, avg price, unrealized P&L) |
| `get_regime` | Market regime (bull/bear/ranging/high_vol) |
| `get_ratings` | LLM ratings list |
| `portfolio_stats` | Portfolio stats (Sharpe, MDD, win rate) |
| `recent_trades` | Recent trade history |
| `knowledge_stats` | Knowledge base stats |
| `query_rules` | Query trading rules |
| `get_knowledge` | Semantic search knowledge base |
| `get_config` | System config (sensitive fields hidden) |
| `get_workflow_status` | Workflow status list |
| `get_decision_trail` | Decision trail (by trace_id or ticker) |
| `get_agent_accuracy` | Agent accuracy stats |

---

## Requirements

- **OS**: macOS or Linux (Windows untested)
- **Python**: 3.11+
- **Account**: [Alpaca Paper Trading](https://alpaca.markets) (free)
- **LLM API**: Any OpenAI-compatible API (OpenAI, Anthropic, Groq, DeepSeek, Google AI, OpenRouter, etc.)
- **News API**: Tavily / Brave / SerpAPI (any one)

### Installation

```bash
git clone https://github.com/ihsieh31/trading-engine-english-version-.git
cd trading-engine-english-version-
./run.sh
```

First run launches the setup menu:

1. Choose language (English / 中文)
2. Enter LLM API Key, API Endpoint, Model ID (any OpenAI-format)
3. Enter Alpaca API Key + Secret (free Paper Trading)
4. Enter News API Keys (Tavily / Brave / SerpAPI, optional)
5. Enter Telegram Token + Chat ID (optional)

After setup, dependencies auto-install, health check runs, and the main menu appears.

To reconfigure: select **5) Setup / Reconfigure** from menu or edit `.env` manually.

---

## Configuration (.env)

### Broker Connection (Required)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ALPACA_API_KEY` | — | Alpaca Paper Trading API Key |
| `ALPACA_API_SECRET` | — | Alpaca Paper Trading API Secret |
| `IS_PAPER` | `true` | Paper trading switch (set false for live) |

### LLM (Required)

Compatible with any OpenAI-format LLM API (OpenAI, Anthropic, Groq, DeepSeek, Google AI, OpenRouter, etc.).

| Parameter | Default | Description |
|-----------|---------|-------------|
| `OPENAI_COMPATIBLE_API_KEY` | — | API Key |
| `LLM_BACKEND_URL` | — | API endpoint, e.g. `https://api.openai.com/v1` |
| `DEEP_THINK_MODEL` | — | Model ID for deep analysis |
| `QUICK_THINK_MODEL` | — | Model ID for quick tasks |

### News Service (At least one)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `TAVILY_API_KEYS` | — | Comma-separated, auto round-robin |
| `BRAVE_API_KEYS` | — | Comma-separated |
| `SERPAPI_API_KEYS` | — | Comma-separated |
| `FMP_API_KEYS` | — | Financial Modeling Prep (optional, price/news fallback) |

### Screening & Scheduling

| Parameter | Default | Description |
|-----------|---------|-------------|
| `UNIVERSE_SOURCE` | `sp500` | `sp500` or `nasdaq100` |
| `SCREENER_TOP_N` | `15` | Top N from technical screening |
| `SCREENER_WORKERS` | `10` | Screening parallelism |
| `MONITOR_INTERVAL_SECONDS` | `30` | Price check frequency during trading hours |
| `BUY_COOLDOWN_SECONDS` | `3600` | Cooldown after selling (seconds) |

### Capital & Risk Management

| Parameter | Default | Description |
|-----------|---------|-------------|
| `INITIAL_CAPITAL` | `100000` | Initial virtual capital |
| `MAX_POSITION_PCT` | `0.10` | Max position size (10%) |
| `MAX_TOTAL_EXPOSURE` | `0.50` | Max total exposure (50%) |
| `MAX_SECTOR_PCT` | `0.25` | Max sector exposure (25%) |
| `STOP_LOSS_PCT` | `0.05` | Stop loss -5% |
| `TAKE_PROFIT_PCT` | `0.15` | Take profit +15% |
| `KELLY_FRACTION` | `0.25` | Kelly conservative fraction |
| `MIN_POSITION_PCT` | `0.02` | Min position size (2%) |
| `MAX_DAILY_LOSS_PCT` | `0.03` | Daily loss >3% triggers circuit breaker |
| `MAX_DRAWDOWN_PCT` | `0.15` | Drawdown >15% triggers circuit breaker |
| `GAP_ALERT_PCT` | `0.08` | Gap alert threshold |

### Order Management

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ORDER_MAX_RETRIES` | `3` | Max retry count for unfilled orders |
| `ORDER_RETRY_DELAY_SEC` | `10` | Retry interval (seconds) |
| `ORDER_FILL_TIMEOUT_SEC` | `300` | Order timeout (seconds) |

### Dashboard

| Parameter | Default | Description |
|-----------|---------|-------------|
| `DASHBOARD_PORT` | `8899` | Web panel port |
| `DASHBOARD_TOKEN` | auto-generated | Optional auth token |

### Notifications

| Parameter | Default | Description |
|-----------|---------|-------------|
| `HEALTHCHECK_URL` | — | healthchecks.io ping URL |
| `TELEGRAM_BOT_TOKEN` | — | Telegram Bot Token |
| `TELEGRAM_CHAT_ID` | — | Telegram Chat ID |

### Knowledge Base

| Parameter | Default | Description |
|-----------|---------|-------------|
| `OBSIDIAN_VAULT_PATH` | `./knowledge` | Obsidian vault path. Auto-scanned on startup for chromadb indexing. Skipped if directory missing. |
| `DATA_DIR` | `./data` | Data and log storage directory |

---

## Module Reference

### Core Pipeline

| Module | Description |
|--------|-------------|
| `scheduler.py` | Daemon controller. Executes STAGE 1-4 pipeline sequentially: technical screening → LLM analysis → intraday monitoring → offline learning. Uses PID file to prevent duplicate starts. |
| `screener.py` | Technical screener. Computes MA20/50, RSI, MACD, volume ratio (5 indicators) from yfinance. Pure pandas, no LLM cost. |
| `deep_analyzer.py` | LLM multi-agent deep analysis. Uses TradingAgents framework for fundamental + technical + sentiment analysis via multi-agent debate. Produces BUY/HOLD/SELL ratings with price targets. Auto-injects economics knowledge, trading experience, and historical rules before analysis. |
| `monitor.py` | Intraday monitoring engine. Checks position prices every N seconds during trading hours, auto-triggers risk checks, Chairman decision aggregation, stop-loss/take-profit exits, new entries, and circuit breaker checks. |
| `portfolio_manager.py` | Capital management module. Kelly Criterion position sizing, portfolio rebalancing, sector exposure control, knowledge rule query for position multiplier adjustment, technical entry confirmation. |
| `order_manager.py` | Order lifecycle management. Submission confirmation, partial fill handling, auto retry (max 3), cancel-replace, bracket orders, EOD cleanup. Dual-write to SQLite + JSONL. |
| `performance.py` | Performance tracking. Computes Sharpe Ratio, Sortino Ratio, Max Drawdown, win rate, Profit Factor, Weighted Average Cost (WAC). Daily auto-snapshot. |
| `regime.py` | Market regime detection. Determines bull/bear/ranging/high_vol based on SPY price vs MA50/MA200 and ATR percentile. Dynamically adjusts position multiplier. |
| `safety.py` | Circuit breaker protection. Daily loss >3% (cross-checked with unrealized P&L to avoid false triggers). MDD >15% forces breaker. State persisted in `.breaker` file. |
| `strategy.py` | Strategy layer. `RatingStrategy` (LLM rating-based), `StopLossTakeProfitStrategy` (OCO bracket), `CompositeStrategy` (multi-strategy combo). |
| `container.py` | DI container. All modules register here as singletons, avoiding duplicate TradingClient creation. PriceMonitor / Scheduler / Dashboard all resolve dependencies through container. |

### V2 Multi-Agent System

| Module | Description |
|--------|-------------|
| `agents/base.py` | Agent base classes. `AnalystAgent` (LLM financial analysis), `ScreenerAgent` (quantitative screening), `ExecutionAgent` (order execution), `ReflectionAgent` (post-trade reflection). |
| `agents/risk_agent.py` | Risk agent. Regime gate, Kelly position calculation, sector exposure limits, total exposure cap. Outputs `RiskAssessment`. |
| `agents/chairman_agent.py` | Chairman agent. Weighted voting to aggregate multi-agent proposals, confidence calibration, rule override, risk veto, LLM arbitration. Outputs `ChairmanDecision`. |
| `core/workflow_engine.py` | Workflow engine. 12-state state machine, event-driven state transitions, supports resume / circuit_breaker / retry. |
| `memory/memory_service.py` | Memory service. Three tiers: working (in-memory), episodic (trade history), semantic (vector knowledge base). Supports decay, conflict detection, graph expansion. |
| `event_bus.py` | Event bus. Singleton pub/sub + SQLite persistence. All events carry event_id / trace_id / workflow_id for audit trail. |
| `interfaces_v2.py` | V2 abstract interfaces. `IAgent`, `IRiskAgent`, `IChairmanAgent`, `IWorkflowEngine`, `IMemoryService`, `IPlugin`, `INewsProvider`. |
| `plugin_host.py` | Plugin host. Auto-discovers plugins via `plugin.json`, dynamic loading, interface validation, lifecycle management. |
| `mcp_server.py` | MCP server. 13 tools over JSON-RPC 2.0 for system status queries. For AI assistant integration. |

### Broker Abstraction Layer

| Module | Description |
|--------|-------------|
| `interfaces.py` | V1 abstract interfaces: `IPriceProvider`, `IAccountProvider`, `IOrderExecutor`, `ITradeRecorder`. |
| `adapters.py` | Alpaca implementation. 3-tier price fallback (Alpaca → FMP → yfinance). Account queries and orders all wrapped via Alpaca REST API. |

### Data Sources

| Module | Description |
|--------|-------------|
| `universe.py` | Stock universe definition. Auto-fetches S&P 500 or NASDAQ-100 constituents from FMP/Wikipedia. Built-in static fallback list. |
| `news_service.py` | Multi-provider news service. Supports Tavily / Brave / SerpAPI / FMP. Auto round-robin for multiple API keys + usage tracking. |
| `fmp_client.py` | Financial Modeling Prep API client. Multi-key round-robin, rate limit backoff, usage stats. |
| `trading_calendar.py` | US stock trading calendar. Uses `exchange_calendars` for precise NYSE trading day and pre-market/market/after-hours detection. |
| `sector_map.py` | S&P 500 sector classification (238 stocks mapped to 11 sectors). Supports FMP/yfinance dynamic lookup. |

### Learning System

| Module | Description |
|--------|-------------|
| `reflection_agent.py` | Post-trade reflection engine. Automatically queues closed trades for analysis. During non-trading hours, LLM analyzes profit/loss reasons and extracts trading rules. |
| `knowledge_base.py` | Obsidian vault knowledge base + chromadb vector storage. Supports wikilink bidirectional graph, semantic search, tag filtering. |
| `economics_kb.py` | Economics knowledge base loader. Loads from `economics-knowledge.yaml` (1,457 sources, 100+ classic texts). Filters by regime + sector for relevant knowledge injection. |

### Monitoring & Notifications

| Module | Description |
|--------|-------------|
| `dashboard.py` | Web monitoring panel. Flask REST API (8 endpoints) + HTML frontend showing positions, cash, performance curve, orders, ratings. |
| `notifier.py` | Telegram notifications. Circuit breaker alerts, daily close reports, emergency events. |
| `health.py` | External monitoring ping. Periodic HTTP GET to healthchecks.io. |

### Utilities

| Module | Description |
|--------|-------------|
| `backtest.py` | Historical backtesting. Uses yfinance historical data with pluggable strategies. **Backtest strategy differs from live — for reference only.** |
| `file_utils.py` | Atomic file I/O. `atomic_write_json`, `atomic_write_text`, `read_json`. |
| `db.py` | SQLite persistence layer. WAL mode + thread-local connections. Stores orders / trades / ratings / performance / events / workflows / agent confidence. |

---

## Usage

### Starting the System

```bash
cd ~/trading_engine
source .venv/bin/activate

# Full auto pipeline (recommended)
python scheduler.py

# Or start dashboard separately (optional)
python dashboard.py

# Or start MCP server (for AI assistant integration)
python mcp_server.py
```

### One-Click Script

```bash
./run.sh    # Auto install + menu: Backtest / Analysis / Monitor / Dashboard
```

### Monitoring Dashboard

Open browser: `http://localhost:8899`

Dashboard features:
- **System Status** — Daemon status, uptime, monitor PID
- **Market Regime** — Current bull/bear/ranging/high_vol with SPY price vs MA50/MA200
- **Account Overview** — Cash, equity, unrealized P&L, sector exposure distribution
- **Ratings List** — Latest LLM BUY/HOLD/SELL ratings with price targets
- **Order History** — Historical order timeline
- **Trade Log** — Per-trade records
- **Performance Curve** — Equity curve, Sharpe, Sortino, MDD, win rate
- **Analysis Queue** — Deep analysis progress (pending / completed)

### Dashboard API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/status` | System status (state, pid, uptime) |
| `GET /api/regime` | Market regime (regime, SPY MA position, ATR percentile) |
| `GET /api/account` | Account info (cash, equity, unrealized P&L, sector breakdown, positions) |
| `GET /api/ratings` | LLM ratings (with analyze_at timestamps) |
| `GET /api/orders` | Historical orders |
| `GET /api/trades` | Trade records |
| `GET /api/performance` | Performance metrics (Sharpe, Sortino, MDD, win rate, Profit Factor) |
| `GET /api/analysis-queue` | Analysis queue status |

### Auto-Start on macOS (launchd)

```bash
# One-click install (auto-replaces paths, loads launchd)
./scripts/setup_launchd.sh

# Manual control
launchctl stop com.tradingengine.scheduler
launchctl start com.tradingengine.scheduler
launchctl unload ~/Library/LaunchAgents/com.tradingengine.scheduler.plist
```

### Backtest

```bash
source .venv/bin/activate
python backtest.py
```

---

## Safety Mechanisms

| Mechanism | Description |
|-----------|-------------|
| **Circuit Breaker** | Daily loss >3% **and** unrealized P&L positive → no breaker (prevents false triggers). MDD >15% forces breaker. State persisted in `data/.breaker`, survives restart. |
| **Kill Switch** | `touch data/.kill` immediately stops all trading. Delete `.kill` to resume. |
| **Duplicate Start Prevention** | PID file check prevents multiple scheduler instances. |
| **Duplicate Order Protection** | `has_open_order` cache + buy cooldown (default 3600s) + order dedup. |
| **Sector Exposure Control** | Single sector total must not exceed `MAX_SECTOR_PCT` (default 25%), enforced by RiskAgent. |
| **Stop-Loss / Take-Profit** | Each position gets automatic OCO bracket order (-5% / +15%). Adding to position rebuilds protection orders. |
| **Partial Fill Handling** | Unfilled orders auto-retry up to 3 times. |
| **Rating Freshness** | Ratings older than 7 days auto-decay in weight, triggering re-analysis. |
| **Technical Entry Confirmation** | Even with LLM BUY rating, requires MA trend up + RSI not overbought to enter. |
| **Gap & Tradability** | Skip stocks with gap >8% at open or insufficient intraday liquidity. |
| **Agent Confidence Calibration** | ChairmanAgent dynamically adjusts agent vote weights based on historical accuracy. |
| **Risk Veto Power** | RiskAgent can veto any trade based on Regime / Exposure / Kelly results. |
| **External Monitoring** | Healthchecks.io periodic ping, alerts immediately on scheduler stop. |

### Emergency Operations

```bash
# Check system status
tail -f data/scheduler.log

# Emergency stop (no restart needed)
touch data/.kill

# Restore from kill switch
rm data/.kill

# Resume after circuit breaker (confirm risk is controlled)
rm data/.breaker
```

---

## Learning System

### Post-Trade Reflection (Reflection Agent)

Every closed trade (stop-loss/take-profit) is automatically queued for reflection. During non-trading hours (STAGE 4), LLM analyzes:
- Why the trade won or lost (Outcome Analysis)
- What lesson was learned (Lesson Extracted)
- Extracted into reusable trading rule (Trading Rule)
- Rule stored in chromadb `trading_rules` collection

### Memory Service (MemoryService)

Three-tier memory architecture for trading rule lifecycle management:

| Tier | Storage | Purpose | Characteristics |
|------|---------|---------|-----------------|
| **Working** | In-memory dict | Current workflow context | Per workflow_id, cleared at stage end |
| **Episodic** | SQLite trades table | Historical trade records | Query past profit/loss patterns |
| **Semantic** | chromadb + SQLite rules | Vectorized knowledge + trading rules | Semantic search, decay, graph expansion |

- `decay_score`: Rules not reinforced decay exponentially over time (lambda = 0.01)
- `detect_conflict`: Alerts when new rules overlap tags with existing rules
- `expand_graph`: Expands related rules via wikilink bidirectional links
- `reinforce`: Increases confidence when a rule is validated

### Knowledge Base

Built-in Obsidian vault-format markdown trading knowledge base used by LLM analysis for injecting relevant trading experience and rules.

#### Data Sources (60 `.md` files)

| Source | Count | Description |
|--------|-------|-------------|
| **Project Gutenberg Classics** | 48 | Economics & finance classics (Ricardo, Mill, Keynes, etc.), text-only, cleaned of copyright notices and prefaces |
| **Trading Guides** | 4 | `trading_rules_cheatsheet.md`, `options_trading_guide.md`, `learning_path.md`, `sec_edgar_guide.md` |
| **Classic Trading Summaries** | 8 | Wyckoff, Gann, Loeb, Thorp, Hamilton, Nelson, NYSE history — condensed to core rules and principles |

#### Usage

1. **Set vault path**: Specify `OBSIDIAN_VAULT_PATH` in `.env` (default `./knowledge`)
2. **Auto-load**: `knowledge_base.py` scans directory on startup, parses wikilink bidirectional links, vectorizes with sentence-transformers into chromadb
3. **Query injection**: `deep_analyzer.py` and `portfolio_manager.py` auto-query relevant knowledge and inject into LLM prompts

The vault is built-in at `knowledge/` — available immediately after clone. To use your own Obsidian vault, point `OBSIDIAN_VAULT_PATH` in `.env` to your vault directory.

#### Re-downloading / Rebuilding Knowledge Base

```bash
# Download 8 classic trading books from Archive.org (requires Archive.org access)
python scripts/convert_books_to_kb.py

# Clean frontmatter/header/intro from all .md files (keep pure content)
python scripts/clean_and_rebuild_kb.py

# Full chromadb index rebuild (delete old collection, recreate)
python -c "from knowledge_base import KnowledgeBase; kb=KnowledgeBase(); kb.rebuild_all()"
```

### Economics Knowledge Base

Built-in `economics-knowledge.yaml` (1,457 sources):
- 100+ classic economics texts (Marx, Keynes, Livermore, Graham, etc.)
- IMF working papers (financial accelerator, trade fragmentation, fiscal theory)
- Academic journals (Real-World Economics Review)
- Auto-filters relevant knowledge by ticker sector + market regime for analysis injection

---

## Data Files

All data stored in `DATA_DIR` (default `./data/`):

| File | Description |
|------|-------------|
| `trading.db` | SQLite database (orders, trades, ratings, events, workflows, rules) |
| `trades.jsonl` | Trade records (dual-write backup) |
| `ratings.json` | LLM deep analysis ratings |
| `performance.json` | Latest performance snapshot |
| `performance_history.json` | Performance history curve |
| `portfolio_snapshot.json` | Real-time portfolio snapshot |
| `recap_YYYY-MM-DD.json` | Daily close report |
| `.breaker` | Circuit breaker marker |
| `.kill` | Kill switch marker |
| `.shortlist.json` | Current screening shortlist |
| `.scheduler_status.json` | Scheduler status |
| `fmp_api_usage.json` | FMP API usage stats |
| `scheduler.log` | Scheduler log |
| `monitor.log` | Monitoring log |
| `deep_analyzer.log` | Deep analysis log |
| `dashboard.log` | Dashboard log |

Logs use `RotatingFileHandler` (10MB rotation, 5 backups).

---

## First Run Flow

1. **STAGE 1: Screener** — Scans all S&P 500 constituents, computes 5 technical indicators, ~15-30 min
2. **STAGE 2: Deep Analysis** — LLM multi-agent deep analysis on TOP N candidates, ~30-60 min
3. **STAGE 3: Monitor** — Intraday monitoring loop, checks prices every 30s, triggers RiskAgent → ChairmanAgent → ExecutionAgent flow
4. **STAGE 4: Offline Learning** — Every 6 hours after market close: knowledge base sync + reflection queue processing

---

## Tech Stack

- **Language**: Python 3.11+
- **Trading API**: Alpaca Trading API (`alpaca-py`)
- **LLM Framework**: [TradingAgents](https://github.com/TauricResearch/TradingAgents) multi-agent analysis
- **LLM Provider**: Any OpenAI-compatible API
- **Data Sources**: yfinance / Financial Modeling Prep / Tavily / Brave / SerpAPI
- **Vector DB**: chromadb + sentence-transformers
- **Calendar**: exchange-calendars
- **Web Panel**: Flask
- **Persistence**: SQLite (WAL mode) + JSONL dual-write
- **Plugin System**: Plugin manifest + importlib dynamic loading
- **AI Integration**: MCP (Model Context Protocol) JSON-RPC 2.0

---

## Knowledge Base Credits

Knowledge base books come from these public sources:

- **Project Gutenberg** (48 books): [gutenberg.org](https://www.gutenberg.org) — Public domain economics & finance classics
- **Archive.org** (8 classic trading summaries): [archive.org](https://archive.org) — Cornell University Library public domain scans
- **Original guides** (4): Condensed trading rules, options strategies, SEC EDGAR guide, learning path

Due to Archive.org access restrictions on some items, the 8 classic trading books are stored as condensed summaries rather than full OCR text.

## Acknowledgements

- [daily_stock_analysis](https://github.com/ZhuLinsen/daily_stock_analysis) — Stock analysis workflow reference
- [TradingAgents](https://github.com/TauricResearch/TradingAgents) — LLM multi-agent trading analysis framework
- `economics-knowledge.yaml` — Integrates 100+ classic texts, IMF papers, academic journals (1,457 total sources)

## Disclaimer

This is an experimental automated trading system operating in **Paper Trading** mode only. No real capital is at risk. The authors assume no responsibility for any financial losses incurred from using this software in live trading.
