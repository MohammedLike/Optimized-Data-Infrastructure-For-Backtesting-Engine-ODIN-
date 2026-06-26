# StrykeX Indicator Catalog

Full catalog of **96 StrykeX Strategy Builder indicators** with quant/trader **entry, exit, stop-loss, take-profit, and filter** rule templates.

## Seed the database

```bash
python scripts/init_database.py
python scripts/seed_indicator_catalog.py
```

## Tables

| Table | Purpose |
|-------|---------|
| `odin.indicator_catalog` | All 96 indicators with category, type, default params, implementation status |
| `odin.condition_rule_templates` | Entry/exit/SL/TP/filter rules per indicator |
| `odin.indicator_catalog_summary` | View with rule counts |

## Rule purposes

| Purpose | Use |
|---------|-----|
| `entry_long` | Open long position |
| `entry_short` | Open short position |
| `exit_long` | Close long |
| `exit_short` | Close short |
| `stop_loss` | Hard stop |
| `take_profit` | Profit target |
| `filter` | Trend/volatility gate — must pass before entry |

## Categories (96 total)

| Category | Count | Examples |
|----------|-------|----------|
| Trend Indicators | 18 | Aroon, ADX, EMA, SuperTrend, Ichimoku |
| Momentum Indicators | 13 | RSI, MACD, Stochastic, CCI |
| Volatility Indicators | 2 | ATR, Bollinger Band |
| Volume & Price | 5 | VWAP, AVWAP, Combined Premium |
| Pivot & Range | 4 | Pivot Points, CPR, ORB |
| Candlestick Patterns | 20 | Engulfing, Doji, Morning Star |
| Heikin Ashi | 6 | Bullish/Bearish HA patterns |
| F&O Indicators | 5 | Long/Short Buildup, Covering |
| Candle Reference | 10 | Current/Previous/Yesterday candle |
| Utility / Logic | 13 | Signal, Math, StopLoss, TradingView |

## API

```http
GET /v1/indicators
GET /v1/indicators?category=Momentum%20Indicators
GET /v1/indicators/rsi/rules
```

## Example query

```sql
SELECT c.display_name, r.rule_purpose, r.rule_name, r.logic_notes
FROM odin.indicator_catalog c
JOIN odin.condition_rule_templates r ON c.slug = r.indicator_slug
WHERE c.slug = 'macd'
ORDER BY r.priority;
```

## Implementation status

- **implemented** — compute engine available (EMA, SMA, RSI, ATR, Bollinger, MACD)
- **planned** — catalog + rules seeded; compute coming in next phases

Source of truth: `packages/odin_indicators/strykex_catalog.py`
