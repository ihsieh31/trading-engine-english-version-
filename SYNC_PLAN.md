# Sync Plan — Chinese ↔ English Repo

## Repos

| Language | Repo |
|----------|------|
| 🇨🇳 Chinese (Primary) | [github.com/ihsieh31/trading-engine](https://github.com/ihsieh31/trading-engine) |
| 🇬🇧 English (Mirror) | [github.com/ihsieh31/trading-engine-english-version-](https://github.com/ihsieh31/trading-engine-english-version-) |

## Strategy: Manual Cherry-Pick (Recommended)

The Chinese repo is the source of truth for code. The English repo gets **selective translations only** — not a full codebase mirror.

### What to sync

| Component | Sync? | Method |
|-----------|-------|--------|
| **Code** (`.py`, `.yaml`, `.sh`, etc.) | ❌ No | Keep Chinese originals only |
| **README.md** | ✅ Yes | Retranslate on significant structural changes |
| **docs/*.md** | ✅ Yes | Translate when new docs added |
| **CLI strings** (`run.sh` i18n) | ✅ Yes | Already bilingual — update both `zh`/`en` blocks together |
| **Log messages, comments, docstrings** | ❌ No | Chinese-only, not worth translating |
| **`plugin.json` descriptions** | ✅ Yes | Translate description field |

### Sync workflow (manual steps)

1. **Code change** → commit to `trading-engine` (Chinese repo) only.
2. **README change** → if structure changed, retranslate `README.md` → push to English repo.
3. **Docs change** → if `docs/*.md` files changed, retranslate → push to English repo.
4. **CLI string change** → update both `zh` dict and `en` dict in `run.sh`.
5. **Configuration change** → update `.env.example` in both repos.

### Reference

- English README was translated from Chinese README commit `56e42ee` (v0.3.0)
- Use `git diff` on the Chinese repo to detect what needs translation

### Cross-references

Both READMEs link to each other at the top:

- Chinese: `[English Version](https://github.com/ihsieh31/trading-engine-english-version-)`
- English: `[中文版](https://github.com/ihsieh31/trading-engine)`

Update these links if the repos move.
