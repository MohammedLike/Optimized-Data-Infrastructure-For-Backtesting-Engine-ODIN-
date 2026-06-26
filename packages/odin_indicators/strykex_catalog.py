"""StrykeX Strategy Builder indicator catalog with quant entry/exit rule templates."""

from __future__ import annotations

from typing import Any

CatalogIndicator = dict[str, Any]
CatalogRule = dict[str, Any]


def _ma_rules(slug: str, label: str, period_param: str = "period") -> list[CatalogRule]:
    return [
        {
            "purpose": "entry_long",
            "rule_name": f"{label} bullish crossover",
            "left_operand": "close",
            "operator": "crosses_above",
            "right_operand": slug,
            "logic_notes": f"Price closes above {label} — trend-following long entry; confirm with volume or higher-TF trend.",
        },
        {
            "purpose": "entry_short",
            "rule_name": f"{label} bearish crossover",
            "left_operand": "close",
            "operator": "crosses_below",
            "right_operand": slug,
            "logic_notes": f"Price closes below {label} — trend-following short entry.",
        },
        {
            "purpose": "exit_long",
            "rule_name": f"{label} long exit",
            "left_operand": "close",
            "operator": "crosses_below",
            "right_operand": slug,
            "logic_notes": f"Exit long when price crosses back below {label}.",
        },
        {
            "purpose": "exit_short",
            "rule_name": f"{label} short exit",
            "left_operand": "close",
            "operator": "crosses_above",
            "right_operand": slug,
            "logic_notes": f"Exit short when price crosses back above {label}.",
        },
        {
            "purpose": "filter",
            "rule_name": f"{label} trend filter",
            "left_operand": slug,
            "operator": "greater_than",
            "right_operand": f"{slug}_slow",
            "logic_notes": f"Only take longs when fast {label} > slow {label} ({period_param} alignment).",
        },
    ]


def _oscillator_rules(
    slug: str,
    label: str,
    oversold: float,
    overbought: float,
    midline: float = 50.0,
) -> list[CatalogRule]:
    return [
        {
            "purpose": "entry_long",
            "rule_name": f"{label} oversold",
            "left_operand": slug,
            "operator": "less_than",
            "right_value": oversold,
            "logic_notes": f"{label} < {oversold}: mean-reversion long in range-bound markets; avoid catching falling knives in strong downtrends.",
        },
        {
            "purpose": "entry_short",
            "rule_name": f"{label} overbought",
            "left_operand": slug,
            "operator": "greater_than",
            "right_value": overbought,
            "logic_notes": f"{label} > {overbought}: mean-reversion short or profit-taking signal.",
        },
        {
            "purpose": "exit_long",
            "rule_name": f"{label} long take-profit",
            "left_operand": slug,
            "operator": "greater_than",
            "right_value": overbought,
            "logic_notes": f"Exit long into overbought territory ({overbought}+).",
        },
        {
            "purpose": "exit_short",
            "rule_name": f"{label} short cover",
            "left_operand": slug,
            "operator": "less_than",
            "right_value": oversold,
            "logic_notes": f"Cover short into oversold territory ({oversold}-).",
        },
        {
            "purpose": "filter",
            "rule_name": f"{label} midline bias",
            "left_operand": slug,
            "operator": "greater_than",
            "right_value": midline,
            "logic_notes": f"Bias long above {midline}, short below — momentum filter.",
        },
    ]


def _pattern_rules(slug: str, label: str, direction: str) -> list[CatalogRule]:
    is_bull = direction == "bullish"
    return [
        {
            "purpose": "entry_long" if is_bull else "entry_short",
            "rule_name": f"{label} pattern detected",
            "left_operand": slug,
            "operator": "equal",
            "right_value": 1.0,
            "logic_notes": f"Candle closes with {label} pattern — enter {'long' if is_bull else 'short'} next bar open; confirm at support/resistance.",
        },
        {
            "purpose": "exit_long" if is_bull else "exit_short",
            "rule_name": f"{label} pattern invalidation",
            "left_operand": "close",
            "operator": "less_than" if is_bull else "greater_than",
            "right_operand": "pattern_low" if is_bull else "pattern_high",
            "logic_notes": "Exit if pattern low/high is breached — structural stop.",
        },
        {
            "purpose": "stop_loss",
            "rule_name": f"{label} stop",
            "left_operand": "close",
            "operator": "less_than" if is_bull else "greater_than",
            "right_operand": "pattern_stop",
            "logic_notes": "Stop below pattern wick (bullish) or above wick (bearish).",
        },
    ]


def _channel_rules(slug: str, label: str) -> list[CatalogRule]:
    return [
        {
            "purpose": "entry_long",
            "rule_name": f"{label} lower band bounce",
            "left_operand": "close",
            "operator": "crosses_above",
            "right_operand": f"{slug}_lower",
            "logic_notes": f"Long on reclaim of {label} lower band — mean reversion.",
        },
        {
            "purpose": "entry_short",
            "rule_name": f"{label} upper band rejection",
            "left_operand": "close",
            "operator": "crosses_below",
            "right_operand": f"{slug}_upper",
            "logic_notes": f"Short on rejection from {label} upper band.",
        },
        {
            "purpose": "exit_long",
            "rule_name": f"{label} upper target",
            "left_operand": "close",
            "operator": "greater_than_or_equal",
            "right_operand": f"{slug}_upper",
            "logic_notes": "Take profit at upper channel.",
        },
        {
            "purpose": "exit_short",
            "rule_name": f"{label} lower target",
            "left_operand": "close",
            "operator": "less_than_or_equal",
            "right_operand": f"{slug}_lower",
            "logic_notes": "Cover short at lower channel.",
        },
    ]


def _candle_ref_rules(slug: str, label: str) -> list[CatalogRule]:
    return [
        {
            "purpose": "entry_long",
            "rule_name": f"Close above {label} high",
            "left_operand": "close",
            "operator": "greater_than",
            "right_operand": f"{slug}_high",
            "logic_notes": f"Breakout long above {label} candle high.",
        },
        {
            "purpose": "entry_short",
            "rule_name": f"Close below {label} low",
            "left_operand": "close",
            "operator": "less_than",
            "right_operand": f"{slug}_low",
            "logic_notes": f"Breakdown short below {label} candle low.",
        },
        {
            "purpose": "stop_loss",
            "rule_name": f"{label} structural stop",
            "left_operand": "close",
            "operator": "less_than",
            "right_operand": f"{slug}_low",
            "logic_notes": f"Stop long below {label} low.",
        },
    ]


INDICATORS: list[CatalogIndicator] = [
    # ── Trend Indicators (1–18) ──────────────────────────────────────────────
    {
        "slug": "aroon",
        "display_name": "Aroon",
        "category": "Trend Indicators",
        "indicator_type": "numeric",
        "default_params": {"period": 14},
        "implementation_status": "planned",
        "description": "Measures time since highest high and lowest low; identifies trend emergence.",
        "rules": [
            {"purpose": "entry_long", "rule_name": "Aroon Up strong", "left_operand": "aroon_up", "operator": "greater_than", "right_value": 70, "logic_notes": "Aroon Up > 70 and Aroon Down < 30 — new uptrend forming."},
            {"purpose": "entry_short", "rule_name": "Aroon Down strong", "left_operand": "aroon_down", "operator": "greater_than", "right_value": 70, "logic_notes": "Aroon Down > 70 and Aroon Up < 30 — new downtrend."},
            {"purpose": "exit_long", "rule_name": "Aroon trend fade", "left_operand": "aroon_up", "operator": "less_than", "right_operand": "aroon_down", "logic_notes": "Exit long when Aroon Up falls below Aroon Down."},
            {"purpose": "exit_short", "rule_name": "Aroon short fade", "left_operand": "aroon_down", "operator": "less_than", "right_operand": "aroon_up", "logic_notes": "Exit short when Aroon Down falls below Aroon Up."},
        ],
    },
    {
        "slug": "aroon_oscillator",
        "display_name": "Aroon Oscillator",
        "category": "Trend Indicators",
        "indicator_type": "numeric",
        "default_params": {"period": 14},
        "implementation_status": "planned",
        "description": "Aroon Up minus Aroon Down; zero-line momentum of trend.",
        "rules": [
            {"purpose": "entry_long", "rule_name": "Aroon Osc zero cross up", "left_operand": "aroon_oscillator", "operator": "crosses_above", "right_value": 0, "logic_notes": "Oscillator crosses above 0 — bullish trend shift."},
            {"purpose": "entry_short", "rule_name": "Aroon Osc zero cross down", "left_operand": "aroon_oscillator", "operator": "crosses_below", "right_value": 0, "logic_notes": "Oscillator crosses below 0 — bearish trend shift."},
            {"purpose": "exit_long", "rule_name": "Aroon Osc bearish", "left_operand": "aroon_oscillator", "operator": "less_than", "right_value": 0, "logic_notes": "Exit long when oscillator turns negative."},
        ],
    },
    {
        "slug": "adx",
        "display_name": "ADX (Average Directional Index)",
        "category": "Trend Indicators",
        "indicator_type": "numeric",
        "default_params": {"period": 14},
        "implementation_status": "planned",
        "description": "Trend strength filter; does not indicate direction alone.",
        "rules": [
            {"purpose": "filter", "rule_name": "ADX trend strength", "left_operand": "adx", "operator": "greater_than", "right_value": 25, "logic_notes": "ADX > 25 confirms trending market — use with DI+/DI- for direction."},
            {"purpose": "entry_long", "rule_name": "ADX + DI+ dominant", "left_operand": "di_plus", "operator": "greater_than", "right_operand": "di_minus", "logic_notes": "DI+ > DI- with ADX rising — bullish trend entry."},
            {"purpose": "entry_short", "rule_name": "ADX + DI- dominant", "left_operand": "di_minus", "operator": "greater_than", "right_operand": "di_plus", "logic_notes": "DI- > DI+ with ADX rising — bearish trend entry."},
            {"purpose": "exit_long", "rule_name": "ADX weakening", "left_operand": "adx", "operator": "less_than", "right_value": 20, "logic_notes": "ADX < 20 — trend exhausted, exit trend positions."},
        ],
    },
    {
        "slug": "ema",
        "display_name": "EMA (Exponential Moving Average)",
        "category": "Trend Indicators",
        "indicator_type": "numeric",
        "default_params": {"period": 20},
        "implementation_status": "implemented",
        "precompute": True,
        "description": "Exponentially weighted moving average; responsive trend line.",
        "rules": _ma_rules("ema", "EMA"),
    },
    {
        "slug": "sma",
        "display_name": "SMA (Simple Moving Average)",
        "category": "Trend Indicators",
        "indicator_type": "numeric",
        "default_params": {"period": 20},
        "implementation_status": "implemented",
        "precompute": True,
        "description": "Arithmetic mean of close over N periods.",
        "rules": _ma_rules("sma", "SMA"),
    },
    {
        "slug": "wma",
        "display_name": "WMA (Weighted Moving Average)",
        "category": "Trend Indicators",
        "indicator_type": "numeric",
        "default_params": {"period": 20},
        "implementation_status": "planned",
        "description": "Linearly weighted MA giving more weight to recent prices.",
        "rules": _ma_rules("wma", "WMA"),
    },
    {
        "slug": "hma",
        "display_name": "HMA (Hull Moving Average)",
        "category": "Trend Indicators",
        "indicator_type": "numeric",
        "default_params": {"period": 20},
        "implementation_status": "planned",
        "description": "Low-lag smoothed MA using weighted MA of WMA.",
        "rules": _ma_rules("hma", "HMA"),
    },
    {
        "slug": "smma",
        "display_name": "SMMA (Smoothed Moving Average)",
        "category": "Trend Indicators",
        "indicator_type": "numeric",
        "default_params": {"period": 20},
        "implementation_status": "planned",
        "description": "Wilder-style smoothed moving average.",
        "rules": _ma_rules("smma", "SMMA"),
    },
    {
        "slug": "wilder_smoothing",
        "display_name": "Wilder Smoothing Average",
        "category": "Trend Indicators",
        "indicator_type": "numeric",
        "default_params": {"period": 14},
        "implementation_status": "planned",
        "description": "Wilder's smoothing method used in RSI/ATR calculations.",
        "rules": _ma_rules("wilder_smoothing", "Wilder MA"),
    },
    {
        "slug": "supertrend",
        "display_name": "Super Trend",
        "category": "Trend Indicators",
        "indicator_type": "numeric",
        "default_params": {"period": 10, "multiplier": 3},
        "implementation_status": "planned",
        "description": "ATR-based trailing trend line; flip on close cross.",
        "rules": [
            {"purpose": "entry_long", "rule_name": "SuperTrend bullish", "left_operand": "close", "operator": "greater_than", "right_operand": "supertrend", "logic_notes": "Close above SuperTrend line — long; line acts as trailing stop."},
            {"purpose": "entry_short", "rule_name": "SuperTrend bearish", "left_operand": "close", "operator": "less_than", "right_operand": "supertrend", "logic_notes": "Close below SuperTrend line — short."},
            {"purpose": "exit_long", "rule_name": "SuperTrend flip down", "left_operand": "close", "operator": "crosses_below", "right_operand": "supertrend", "logic_notes": "Exit long on SuperTrend bearish flip."},
            {"purpose": "stop_loss", "rule_name": "SuperTrend trail", "left_operand": "close", "operator": "less_than", "right_operand": "supertrend", "logic_notes": "Trailing stop at SuperTrend line."},
        ],
    },
    {
        "slug": "half_trend",
        "display_name": "Half Trend",
        "category": "Trend Indicators",
        "indicator_type": "numeric",
        "default_params": {"amplitude": 2, "channel_deviation": 2},
        "implementation_status": "planned",
        "description": "Reduced-lag trend indicator with amplitude channels.",
        "rules": [
            {"purpose": "entry_long", "rule_name": "Half Trend up", "left_operand": "half_trend", "operator": "equal", "right_value": 1, "logic_notes": "Half Trend turns bullish (value = 1)."},
            {"purpose": "entry_short", "rule_name": "Half Trend down", "left_operand": "half_trend", "operator": "equal", "right_value": -1, "logic_notes": "Half Trend turns bearish (value = -1)."},
            {"purpose": "exit_long", "rule_name": "Half Trend reversal", "left_operand": "half_trend", "operator": "crosses_below", "right_value": 0, "logic_notes": "Exit on trend color flip."},
        ],
    },
    {
        "slug": "ichimoku",
        "display_name": "Ichimoku Cloud",
        "category": "Trend Indicators",
        "indicator_type": "composite",
        "default_params": {"tenkan": 9, "kijun": 26, "senkou_b": 52},
        "implementation_status": "planned",
        "description": "Multi-component system: Tenkan, Kijun, Senkou spans, Chikou.",
        "rules": [
            {"purpose": "entry_long", "rule_name": "Price above cloud", "left_operand": "close", "operator": "greater_than", "right_operand": "senkou_span_a", "logic_notes": "Close above Kumo (cloud) — bullish bias."},
            {"purpose": "entry_long", "rule_name": "TK cross bullish", "left_operand": "tenkan", "operator": "crosses_above", "right_operand": "kijun", "logic_notes": "Tenkan crosses above Kijun — classic Ichimoku long signal."},
            {"purpose": "entry_short", "rule_name": "Price below cloud", "left_operand": "close", "operator": "less_than", "right_operand": "senkou_span_b", "logic_notes": "Close below Kumo — bearish bias."},
            {"purpose": "exit_long", "rule_name": "TK cross bearish", "left_operand": "tenkan", "operator": "crosses_below", "right_operand": "kijun", "logic_notes": "Tenkan crosses below Kijun — exit long."},
        ],
    },
    {
        "slug": "parabolic_sar",
        "display_name": "Parabolic SAR",
        "category": "Trend Indicators",
        "indicator_type": "numeric",
        "default_params": {"af_start": 0.02, "af_step": 0.02, "af_max": 0.2},
        "implementation_status": "planned",
        "description": "Stop-and-reverse trailing dots above/below price.",
        "rules": [
            {"purpose": "entry_long", "rule_name": "SAR below price", "left_operand": "parabolic_sar", "operator": "less_than", "right_operand": "close", "logic_notes": "SAR dots below price — bullish; enter on flip."},
            {"purpose": "entry_short", "rule_name": "SAR above price", "left_operand": "parabolic_sar", "operator": "greater_than", "right_operand": "close", "logic_notes": "SAR dots above price — bearish."},
            {"purpose": "stop_loss", "rule_name": "SAR trail stop", "left_operand": "close", "operator": "less_than", "right_operand": "parabolic_sar", "logic_notes": "Use SAR level as trailing stop for longs."},
        ],
    },
    {
        "slug": "trend_intensity_index",
        "display_name": "Trend Intensity Index",
        "category": "Trend Indicators",
        "indicator_type": "numeric",
        "default_params": {"period": 30},
        "implementation_status": "planned",
        "description": "Measures intensity of trend relative to volatility.",
        "rules": _oscillator_rules("tii", "TII", oversold=40, overbought=60),
    },
    {
        "slug": "coppock_curve",
        "display_name": "Coppock Curve",
        "category": "Trend Indicators",
        "indicator_type": "numeric",
        "default_params": {"roc1": 14, "roc2": 11, "wma": 10},
        "implementation_status": "planned",
        "description": "Long-term momentum oscillator for major bottoms.",
        "rules": [
            {"purpose": "entry_long", "rule_name": "Coppock zero cross up", "left_operand": "coppock_curve", "operator": "crosses_above", "right_value": 0, "logic_notes": "Coppock crosses above zero — long-term bullish momentum (monthly charts)."},
            {"purpose": "exit_long", "rule_name": "Coppock peak", "left_operand": "coppock_curve", "operator": "crosses_below", "right_operand": "coppock_signal", "logic_notes": "Exit when Coppock rolls over from peak."},
        ],
    },
    {
        "slug": "keltner_channel",
        "display_name": "Keltner Channel",
        "category": "Trend Indicators",
        "indicator_type": "composite",
        "default_params": {"period": 20, "atr_mult": 2},
        "implementation_status": "planned",
        "description": "EMA center line with ATR-based upper/lower bands.",
        "rules": _channel_rules("keltner_channel", "Keltner Channel"),
    },
    {
        "slug": "donchian_channel",
        "display_name": "Donchian Channel",
        "category": "Trend Indicators",
        "indicator_type": "composite",
        "default_params": {"period": 20},
        "implementation_status": "planned",
        "description": "Highest high / lowest low channel; Turtle trading breakout.",
        "rules": [
            {"purpose": "entry_long", "rule_name": "Donchian upper breakout", "left_operand": "close", "operator": "greater_than", "right_operand": "donchian_upper", "logic_notes": "Close above N-period high — classic breakout long (Turtle)."},
            {"purpose": "entry_short", "rule_name": "Donchian lower breakdown", "left_operand": "close", "operator": "less_than", "right_operand": "donchian_lower", "logic_notes": "Close below N-period low — breakout short."},
            {"purpose": "exit_long", "rule_name": "Donchian mid exit", "left_operand": "close", "operator": "less_than", "right_operand": "donchian_mid", "logic_notes": "Exit long below channel midpoint."},
            {"purpose": "stop_loss", "rule_name": "Donchian stop", "left_operand": "close", "operator": "less_than", "right_operand": "donchian_lower", "logic_notes": "Stop below lower Donchian band."},
        ],
    },
    {
        "slug": "mrc",
        "display_name": "MRC (Mean Reversion Channel)",
        "category": "Trend Indicators",
        "indicator_type": "composite",
        "default_params": {"period": 20, "std": 2},
        "implementation_status": "planned",
        "description": "Mean reversion bands around a central tendency line.",
        "rules": _channel_rules("mrc", "MRC"),
    },
    # ── Momentum Indicators (19–31) ──────────────────────────────────────────
    {
        "slug": "rsi",
        "display_name": "RSI (Relative Strength Index)",
        "category": "Momentum Indicators",
        "indicator_type": "numeric",
        "default_params": {"period": 14},
        "implementation_status": "implemented",
        "precompute": True,
        "description": "Relative strength oscillator 0–100; Wilder smoothing.",
        "rules": _oscillator_rules("rsi", "RSI", oversold=30, overbought=70),
    },
    {
        "slug": "stochastic",
        "display_name": "Stochastic Oscillator",
        "category": "Momentum Indicators",
        "indicator_type": "composite",
        "default_params": {"k_period": 14, "d_period": 3},
        "implementation_status": "planned",
        "description": "%K and %D momentum relative to high-low range.",
        "rules": [
            {"purpose": "entry_long", "rule_name": "Stoch oversold cross", "left_operand": "stoch_k", "operator": "crosses_above", "right_operand": "stoch_d", "logic_notes": "%K crosses above %D in oversold zone (<20) — bullish."},
            {"purpose": "entry_short", "rule_name": "Stoch overbought cross", "left_operand": "stoch_k", "operator": "crosses_below", "right_operand": "stoch_d", "logic_notes": "%K crosses below %D in overbought zone (>80) — bearish."},
            {"purpose": "exit_long", "rule_name": "Stoch overbought", "left_operand": "stoch_k", "operator": "greater_than", "right_value": 80, "logic_notes": "Exit long in overbought territory."},
        ],
    },
    {
        "slug": "stochastic_rsi",
        "display_name": "Stochastic RSI",
        "category": "Momentum Indicators",
        "indicator_type": "numeric",
        "default_params": {"rsi_period": 14, "stoch_period": 14, "k_smooth": 3, "d_smooth": 3},
        "implementation_status": "planned",
        "description": "Stochastic applied to RSI for finer momentum signals.",
        "rules": _oscillator_rules("stoch_rsi", "Stoch RSI", oversold=0.2, overbought=0.8),
    },
    {
        "slug": "cci",
        "display_name": "CCI (Commodity Channel Index)",
        "category": "Momentum Indicators",
        "indicator_type": "numeric",
        "default_params": {"period": 20},
        "implementation_status": "planned",
        "description": "Measures deviation from statistical mean.",
        "rules": [
            {"purpose": "entry_long", "rule_name": "CCI oversold", "left_operand": "cci", "operator": "less_than", "right_value": -100, "logic_notes": "CCI < -100 — oversold mean reversion long."},
            {"purpose": "entry_short", "rule_name": "CCI overbought", "left_operand": "cci", "operator": "greater_than", "right_value": 100, "logic_notes": "CCI > 100 — overbought short."},
            {"purpose": "exit_long", "rule_name": "CCI zero cross down", "left_operand": "cci", "operator": "crosses_below", "right_value": 0, "logic_notes": "Exit long when CCI crosses below zero."},
        ],
    },
    {
        "slug": "roc",
        "display_name": "ROC (Rate of Change)",
        "category": "Momentum Indicators",
        "indicator_type": "numeric",
        "default_params": {"period": 12},
        "implementation_status": "planned",
        "description": "Percentage change in price over N periods.",
        "rules": [
            {"purpose": "entry_long", "rule_name": "ROC positive", "left_operand": "roc", "operator": "crosses_above", "right_value": 0, "logic_notes": "ROC crosses above 0 — positive momentum."},
            {"purpose": "entry_short", "rule_name": "ROC negative", "left_operand": "roc", "operator": "crosses_below", "right_value": 0, "logic_notes": "ROC crosses below 0 — negative momentum."},
            {"purpose": "filter", "rule_name": "ROC acceleration", "left_operand": "roc", "operator": "greater_than", "right_operand": "roc_sma", "logic_notes": "ROC above its MA — accelerating momentum."},
        ],
    },
    {
        "slug": "williams_r",
        "display_name": "Williams %R",
        "category": "Momentum Indicators",
        "indicator_type": "numeric",
        "default_params": {"period": 14},
        "implementation_status": "planned",
        "description": "Inverted stochastic oscillator (-100 to 0).",
        "rules": _oscillator_rules("williams_r", "Williams %R", oversold=-80, overbought=-20),
    },
    {
        "slug": "fisher_transform",
        "display_name": "Fisher Transform (FT)",
        "category": "Momentum Indicators",
        "indicator_type": "numeric",
        "default_params": {"period": 10},
        "implementation_status": "planned",
        "description": "Gaussian normalization of price for sharp turning points.",
        "rules": [
            {"purpose": "entry_long", "rule_name": "Fisher cross up", "left_operand": "fisher", "operator": "crosses_above", "right_operand": "fisher_signal", "logic_notes": "Fisher crosses above signal line — bullish reversal."},
            {"purpose": "entry_short", "rule_name": "Fisher cross down", "left_operand": "fisher", "operator": "crosses_below", "right_operand": "fisher_signal", "logic_notes": "Fisher crosses below signal — bearish reversal."},
        ],
    },
    {
        "slug": "awesome_oscillator",
        "display_name": "Awesome Oscillator",
        "category": "Momentum Indicators",
        "indicator_type": "numeric",
        "default_params": {"fast": 5, "slow": 34},
        "implementation_status": "planned",
        "description": "Histogram of SMA(midpoint) fast minus slow.",
        "rules": [
            {"purpose": "entry_long", "rule_name": "AO zero cross up", "left_operand": "awesome_oscillator", "operator": "crosses_above", "right_value": 0, "logic_notes": "AO crosses above zero — bullish momentum."},
            {"purpose": "entry_short", "rule_name": "AO zero cross down", "left_operand": "awesome_oscillator", "operator": "crosses_below", "right_value": 0, "logic_notes": "AO crosses below zero — bearish."},
            {"purpose": "entry_long", "rule_name": "AO saucer", "left_operand": "awesome_oscillator", "operator": "greater_than", "right_operand": "awesome_oscillator_prev", "logic_notes": "Three-bar saucer pattern above zero — Bill Williams setup."},
        ],
    },
    {
        "slug": "qqe_signals",
        "display_name": "QQE Signals",
        "category": "Momentum Indicators",
        "indicator_type": "numeric",
        "default_params": {"rsi_period": 14, "sf": 5, "qqe_factor": 4.236},
        "implementation_status": "planned",
        "description": "Quantitative Qualitative Estimation — smoothed RSI with trailing levels.",
        "rules": [
            {"purpose": "entry_long", "rule_name": "QQE bullish", "left_operand": "qqe", "operator": "crosses_above", "right_operand": "qqe_signal", "logic_notes": "QQE line crosses above signal — long."},
            {"purpose": "entry_short", "rule_name": "QQE bearish", "left_operand": "qqe", "operator": "crosses_below", "right_operand": "qqe_signal", "logic_notes": "QQE crosses below signal — short."},
        ],
    },
    {
        "slug": "macd",
        "display_name": "MACD (Moving Average Convergence Divergence)",
        "category": "Momentum Indicators",
        "indicator_type": "composite",
        "default_params": {"fast": 12, "slow": 26, "signal": 9},
        "implementation_status": "implemented",
        "precompute": True,
        "description": "MACD line, signal line, and histogram.",
        "rules": [
            {"purpose": "entry_long", "rule_name": "MACD bullish cross", "left_operand": "macd_line", "operator": "crosses_above", "right_operand": "macd_signal", "logic_notes": "MACD line crosses above signal — classic bullish entry."},
            {"purpose": "entry_short", "rule_name": "MACD bearish cross", "left_operand": "macd_line", "operator": "crosses_below", "right_operand": "macd_signal", "logic_notes": "MACD crosses below signal — bearish."},
            {"purpose": "exit_long", "rule_name": "MACD histogram fade", "left_operand": "macd_histogram", "operator": "less_than", "right_value": 0, "logic_notes": "Histogram turns negative — momentum fading."},
            {"purpose": "filter", "rule_name": "MACD above zero", "left_operand": "macd_line", "operator": "greater_than", "right_value": 0, "logic_notes": "Only long when MACD above zero line."},
        ],
    },
    {
        "slug": "moving_avg_rsi",
        "display_name": "Moving Average for RSI",
        "category": "Momentum Indicators",
        "indicator_type": "numeric",
        "default_params": {"rsi_period": 14, "ma_period": 14},
        "implementation_status": "planned",
        "description": "SMA/EMA applied to RSI for smoothed momentum.",
        "rules": [
            {"purpose": "entry_long", "rule_name": "RSI above RSI-MA", "left_operand": "rsi", "operator": "crosses_above", "right_operand": "moving_avg_rsi", "logic_notes": "RSI crosses above its MA — bullish momentum."},
            {"purpose": "exit_long", "rule_name": "RSI below RSI-MA", "left_operand": "rsi", "operator": "crosses_below", "right_operand": "moving_avg_rsi", "logic_notes": "RSI crosses below its MA — exit long."},
        ],
    },
    {
        "slug": "moving_avg_atr",
        "display_name": "Moving Average for ATR",
        "category": "Momentum Indicators",
        "indicator_type": "numeric",
        "default_params": {"atr_period": 14, "ma_period": 14},
        "implementation_status": "planned",
        "description": "Smoothed ATR for volatility regime detection.",
        "rules": [
            {"purpose": "filter", "rule_name": "ATR expansion", "left_operand": "atr", "operator": "greater_than", "right_operand": "moving_avg_atr", "logic_notes": "ATR > ATR-MA — volatility expanding; favor breakout strategies."},
            {"purpose": "filter", "rule_name": "ATR contraction", "left_operand": "atr", "operator": "less_than", "right_operand": "moving_avg_atr", "logic_notes": "ATR < ATR-MA — low volatility; favor mean reversion."},
        ],
    },
    {
        "slug": "mfi",
        "display_name": "MFI (Money Flow Index)",
        "category": "Momentum Indicators",
        "indicator_type": "numeric",
        "default_params": {"period": 14},
        "implementation_status": "planned",
        "description": "Volume-weighted RSI; money flow pressure.",
        "rules": _oscillator_rules("mfi", "MFI", oversold=20, overbought=80),
    },
    # ── Volatility Indicators (32–33) ──────────────────────────────────────────
    {
        "slug": "atr",
        "display_name": "ATR (Average True Range)",
        "category": "Volatility Indicators",
        "indicator_type": "numeric",
        "default_params": {"period": 14},
        "implementation_status": "implemented",
        "precompute": True,
        "description": "Average true range; volatility and stop sizing.",
        "rules": [
            {"purpose": "stop_loss", "rule_name": "ATR stop long", "left_operand": "close", "operator": "less_than", "right_operand": "entry_price_minus_2atr", "logic_notes": "Stop long at entry - 2×ATR — standard volatility stop."},
            {"purpose": "take_profit", "rule_name": "ATR target long", "left_operand": "close", "operator": "greater_than", "right_operand": "entry_price_plus_3atr", "logic_notes": "Target at entry + 3×ATR (1.5:1 R:R with 2×ATR stop)."},
            {"purpose": "filter", "rule_name": "ATR breakout", "left_operand": "atr", "operator": "greater_than", "right_operand": "atr_sma", "logic_notes": "Volatility expansion — enable breakout entries."},
        ],
    },
    {
        "slug": "bollinger_band",
        "display_name": "Bollinger Band",
        "category": "Volatility Indicators",
        "indicator_type": "composite",
        "default_params": {"period": 20, "std": 2},
        "implementation_status": "implemented",
        "precompute": True,
        "description": "SMA ± standard deviation bands.",
        "rules": [
            {"purpose": "entry_long", "rule_name": "BB lower touch", "left_operand": "close", "operator": "less_than_or_equal", "right_operand": "bb_lower", "logic_notes": "Close at/below lower band — mean reversion long (range market)."},
            {"purpose": "entry_short", "rule_name": "BB upper touch", "left_operand": "close", "operator": "greater_than_or_equal", "right_operand": "bb_upper", "logic_notes": "Close at/above upper band — mean reversion short."},
            {"purpose": "entry_long", "rule_name": "BB squeeze breakout", "left_operand": "close", "operator": "crosses_above", "right_operand": "bb_upper", "logic_notes": "Breakout above upper band after squeeze — momentum long."},
            {"purpose": "exit_long", "rule_name": "BB mid reversion", "left_operand": "close", "operator": "greater_than_or_equal", "right_operand": "bb_mid", "logic_notes": "Exit mean-reversion long at middle band."},
        ],
    },
    # ── Volume & Price Indicators (34–38) ──────────────────────────────────────
    {
        "slug": "vwap",
        "display_name": "VWAP (Volume Weighted Average Price)",
        "category": "Volume & Price Indicators",
        "indicator_type": "numeric",
        "default_params": {"session": "daily"},
        "implementation_status": "planned",
        "description": "Session volume-weighted average price; institutional benchmark.",
        "rules": [
            {"purpose": "entry_long", "rule_name": "Price above VWAP", "left_operand": "close", "operator": "greater_than", "right_operand": "vwap", "logic_notes": "Close above VWAP — intraday bullish bias."},
            {"purpose": "entry_short", "rule_name": "Price below VWAP", "left_operand": "close", "operator": "less_than", "right_operand": "vwap", "logic_notes": "Close below VWAP — intraday bearish bias."},
            {"purpose": "exit_long", "rule_name": "VWAP rejection", "left_operand": "close", "operator": "crosses_below", "right_operand": "vwap", "logic_notes": "Exit long on VWAP loss."},
        ],
    },
    {
        "slug": "avwap",
        "display_name": "AVWAP (Anchored Volume Weighted Average Price)",
        "category": "Volume & Price Indicators",
        "indicator_type": "numeric",
        "default_params": {"anchor": "session_open"},
        "implementation_status": "planned",
        "description": "VWAP anchored to a user-defined event (earnings, swing low, etc.).",
        "rules": [
            {"purpose": "entry_long", "rule_name": "Above AVWAP", "left_operand": "close", "operator": "greater_than", "right_operand": "avwap", "logic_notes": "Price holds above anchored VWAP — bullish from anchor point."},
            {"purpose": "entry_short", "rule_name": "Below AVWAP", "left_operand": "close", "operator": "less_than", "right_operand": "avwap", "logic_notes": "Price below AVWAP — bearish from anchor."},
        ],
    },
    {
        "slug": "price_ratio",
        "display_name": "Price Ratio",
        "category": "Volume & Price Indicators",
        "indicator_type": "numeric",
        "default_params": {"numerator": "close", "denominator": "sma_20"},
        "implementation_status": "planned",
        "description": "Ratio of two price series (e.g. close / MA).",
        "rules": [
            {"purpose": "entry_long", "rule_name": "Price ratio expansion", "left_operand": "price_ratio", "operator": "greater_than", "right_value": 1.02, "logic_notes": "Price ratio > 1.02 — relative strength long."},
            {"purpose": "entry_short", "rule_name": "Price ratio contraction", "left_operand": "price_ratio", "operator": "less_than", "right_value": 0.98, "logic_notes": "Price ratio < 0.98 — relative weakness short."},
        ],
    },
    {
        "slug": "ratio",
        "display_name": "Ratio",
        "category": "Volume & Price Indicators",
        "indicator_type": "numeric",
        "default_params": {"leg_a": "symbol_a", "leg_b": "symbol_b"},
        "implementation_status": "planned",
        "description": "Inter-instrument ratio for pairs/spread strategies.",
        "rules": [
            {"purpose": "entry_long", "rule_name": "Ratio z-score low", "left_operand": "ratio_zscore", "operator": "less_than", "right_value": -2, "logic_notes": "Ratio 2σ below mean — long spread (mean reversion)."},
            {"purpose": "entry_short", "rule_name": "Ratio z-score high", "left_operand": "ratio_zscore", "operator": "greater_than", "right_value": 2, "logic_notes": "Ratio 2σ above mean — short spread."},
        ],
    },
    {
        "slug": "combined_premium",
        "display_name": "Combined Premium",
        "category": "Volume & Price Indicators",
        "indicator_type": "numeric",
        "default_params": {},
        "implementation_status": "planned",
        "description": "Sum of option premiums in a basket or straddle.",
        "rules": [
            {"purpose": "entry_long", "rule_name": "Premium expansion", "left_operand": "combined_premium", "operator": "greater_than", "right_operand": "combined_premium_ma", "logic_notes": "Rising combined premium — volatility/long gamma bias."},
            {"purpose": "exit_long", "rule_name": "Premium decay", "left_operand": "combined_premium", "operator": "less_than", "right_operand": "combined_premium_ma", "logic_notes": "Premium below MA — theta decay exit."},
        ],
    },
    # ── Pivot & Range Indicators (39–42) ───────────────────────────────────────
    {
        "slug": "pivot_points",
        "display_name": "Pivot Points",
        "category": "Pivot & Range Indicators",
        "indicator_type": "composite",
        "default_params": {"method": "standard"},
        "implementation_status": "planned",
        "description": "Classic floor pivot P, R1-R3, S1-S3 from prior session OHLC.",
        "rules": [
            {"purpose": "entry_long", "rule_name": "Pivot support bounce", "left_operand": "close", "operator": "crosses_above", "right_operand": "pivot_s1", "logic_notes": "Bounce off S1 support — intraday long."},
            {"purpose": "entry_short", "rule_name": "Pivot resistance reject", "left_operand": "close", "operator": "crosses_below", "right_operand": "pivot_r1", "logic_notes": "Rejection at R1 — intraday short."},
            {"purpose": "take_profit", "rule_name": "Pivot R2 target", "left_operand": "close", "operator": "greater_than_or_equal", "right_operand": "pivot_r2", "logic_notes": "Take profit at R2 resistance."},
        ],
    },
    {
        "slug": "cpr",
        "display_name": "CPR (Central Pivot Range)",
        "category": "Pivot & Range Indicators",
        "indicator_type": "composite",
        "default_params": {},
        "implementation_status": "planned",
        "description": "Central Pivot Range: TC, Pivot, BC from prior day.",
        "rules": [
            {"purpose": "entry_long", "rule_name": "CPR breakout up", "left_operand": "close", "operator": "greater_than", "right_operand": "cpr_tc", "logic_notes": "Close above CPR top — bullish day bias."},
            {"purpose": "entry_short", "rule_name": "CPR breakdown", "left_operand": "close", "operator": "less_than", "right_operand": "cpr_bc", "logic_notes": "Close below CPR bottom — bearish day bias."},
            {"purpose": "filter", "rule_name": "CPR narrow", "left_operand": "cpr_width", "operator": "less_than", "right_operand": "cpr_width_avg", "logic_notes": "Narrow CPR — expect trending day."},
        ],
    },
    {
        "slug": "orb",
        "display_name": "ORB (Opening Range Breakout)",
        "category": "Pivot & Range Indicators",
        "indicator_type": "composite",
        "default_params": {"minutes": 15},
        "implementation_status": "planned",
        "description": "First N minutes high/low define breakout range.",
        "rules": [
            {"purpose": "entry_long", "rule_name": "ORB high break", "left_operand": "close", "operator": "greater_than", "right_operand": "orb_high", "logic_notes": "Break above opening range high — momentum long."},
            {"purpose": "entry_short", "rule_name": "ORB low break", "left_operand": "close", "operator": "less_than", "right_operand": "orb_low", "logic_notes": "Break below opening range low — momentum short."},
            {"purpose": "stop_loss", "rule_name": "ORB midpoint stop", "left_operand": "close", "operator": "less_than", "right_operand": "orb_mid", "logic_notes": "Stop below ORB midpoint on failed breakout."},
        ],
    },
    {
        "slug": "range_breakout",
        "display_name": "Range Breakout",
        "category": "Pivot & Range Indicators",
        "indicator_type": "composite",
        "default_params": {"lookback": 20},
        "implementation_status": "planned",
        "description": "Breakout from N-bar consolidation range.",
        "rules": [
            {"purpose": "entry_long", "rule_name": "Range high break", "left_operand": "close", "operator": "greater_than", "right_operand": "range_high", "logic_notes": "Close above consolidation high — breakout long."},
            {"purpose": "entry_short", "rule_name": "Range low break", "left_operand": "close", "operator": "less_than", "right_operand": "range_low", "logic_notes": "Close below consolidation low — breakdown short."},
            {"purpose": "stop_loss", "rule_name": "Range stop", "left_operand": "close", "operator": "less_than", "right_operand": "range_mid", "logic_notes": "Stop at range midpoint."},
        ],
    },
]

# Candlestick patterns (43–62)
_CANDLE_PATTERNS = [
    ("bullish_engulfing", "Bullish Engulfing", "bullish"),
    ("bearish_engulfing", "Bearish Engulfing", "bearish"),
    ("bullish_hammer", "Bullish Hammer", "bullish"),
    ("bearish_hammer", "Bearish Hammer", "bearish"),
    ("bullish_inverted_hammer", "Bullish Inverted Hammer", "bullish"),
    ("bearish_inverted_hammer", "Bearish Inverted Hammer", "bearish"),
    ("bullish_marubozu", "Bullish Marubozu", "bullish"),
    ("bearish_marubozu", "Bearish Marubozu", "bearish"),
    ("bullish_spinning_top", "Bullish Spinning Top", "bullish"),
    ("bearish_spinning_top", "Bearish Spinning Top", "bearish"),
    ("doji", "Doji", "bullish"),
    ("dragon_fly_doji", "Dragon Fly Doji", "bullish"),
    ("grave_stone_doji", "Grave Stone Doji", "bearish"),
    ("long_legged_doji", "Long Legged Doji", "bullish"),
    ("morning_star", "Morning Star", "bullish"),
    ("evening_star", "Evening Star", "bearish"),
    ("piercing_line", "Piercing Line", "bullish"),
    ("dark_cloud_cover", "Dark Cloud Cover", "bearish"),
    ("three_white_soldiers", "Three White Soldiers", "bullish"),
    ("three_black_crows", "Three Black Crows", "bearish"),
]

for slug, name, direction in _CANDLE_PATTERNS:
    INDICATORS.append({
        "slug": slug,
        "display_name": name,
        "category": "Candlestick Patterns",
        "indicator_type": "pattern",
        "default_params": {},
        "implementation_status": "planned",
        "description": f"Candlestick pattern: {name}.",
        "rules": _pattern_rules(slug, name, direction),
    })

# Heikin Ashi (63–68)
_HEIKIN_PATTERNS = [
    ("heikinashi_bullish", "Heikinashi Bullish", "bullish"),
    ("heikinashi_very_bullish", "Heikinashi Very Bullish", "bullish"),
    ("heikinashi_bullish_indecision", "Heikinashi Bullish Indecision", "bullish"),
    ("heikinashi_bearish", "Heikinashi Bearish", "bearish"),
    ("heikinashi_very_bearish", "Heikinashi Very Bearish", "bearish"),
    ("heikinashi_bearish_indecision", "Heikinashi Bearish Indecision", "bearish"),
]

for slug, name, direction in _HEIKIN_PATTERNS:
    INDICATORS.append({
        "slug": slug,
        "display_name": name,
        "category": "Heikin Ashi Patterns",
        "indicator_type": "pattern",
        "default_params": {},
        "implementation_status": "planned",
        "description": f"Heikin Ashi pattern: {name}.",
        "rules": _pattern_rules(slug, name, direction),
    })

# F&O indicators (69–73)
_FO_INDICATORS = [
    ("long_buildup", "Long Buildup", [
        {"purpose": "entry_long", "rule_name": "Long buildup", "left_operand": "oi_change", "operator": "greater_than", "right_value": 0, "logic_notes": "Rising OI + rising price — fresh longs entering; bullish continuation."},
        {"purpose": "filter", "rule_name": "Volume confirm", "left_operand": "volume", "operator": "greater_than", "right_operand": "volume_sma", "logic_notes": "Confirm buildup with above-average volume."},
    ]),
    ("short_buildup", "Short Buildup", [
        {"purpose": "entry_short", "rule_name": "Short buildup", "left_operand": "oi_change", "operator": "greater_than", "right_value": 0, "logic_notes": "Rising OI + falling price — fresh shorts; bearish continuation."},
    ]),
    ("long_unwinding", "Long Unwinding", [
        {"purpose": "exit_long", "rule_name": "Long unwinding", "left_operand": "oi_change", "operator": "less_than", "right_value": 0, "logic_notes": "Falling OI + falling price — longs exiting; avoid new longs."},
        {"purpose": "entry_short", "rule_name": "Unwind short", "left_operand": "oi_change", "operator": "less_than", "right_value": 0, "logic_notes": "Long unwinding after rally — tactical short."},
    ]),
    ("short_covering", "Short Covering", [
        {"purpose": "exit_short", "rule_name": "Short covering", "left_operand": "oi_change", "operator": "less_than", "right_value": 0, "logic_notes": "Falling OI + rising price — shorts covering; squeeze rally."},
        {"purpose": "entry_long", "rule_name": "Covering rally", "left_operand": "oi_change", "operator": "less_than", "right_value": 0, "logic_notes": "Short covering momentum long."},
    ]),
    ("options_basket", "Options Basket", [
        {"purpose": "entry_long", "rule_name": "Basket delta positive", "left_operand": "basket_delta", "operator": "greater_than", "right_value": 0, "logic_notes": "Net positive delta basket — bullish hedge overlay."},
        {"purpose": "entry_short", "rule_name": "Basket delta negative", "left_operand": "basket_delta", "operator": "less_than", "right_value": 0, "logic_notes": "Net negative delta — bearish overlay."},
    ]),
]

for slug, name, rules in _FO_INDICATORS:
    INDICATORS.append({
        "slug": slug,
        "display_name": name,
        "category": "Futures & Options Indicators",
        "indicator_type": "composite",
        "default_params": {},
        "implementation_status": "planned",
        "description": f"F&O flow indicator: {name}.",
        "rules": rules,
    })

# Candle reference (74–83)
_CANDLE_REFS = [
    ("current_candle", "Current Candle"),
    ("today_candle", "Today Candle"),
    ("yesterday_candle", "Yesterday Candle"),
    ("previous_candle", "Previous Candle"),
    ("previous_day_candle", "Previous Day Candle"),
    ("previous_nth_candle", "Previous Nth Candle"),
    ("last_n_candles", "Last N Candles"),
    ("entry_candle", "Entry Candle"),
    ("signal_candle", "Signal Candle"),
    ("candle_at", "CandleAt"),
]

for slug, name in _CANDLE_REFS:
    extra = []
    if slug == "previous_nth_candle":
        extra.append({"purpose": "filter", "rule_name": "Nth candle offset", "left_operand": "candle_offset", "operator": "equal", "right_value": 2, "logic_notes": "Compare against candle N bars ago (parameterized)."})
    if slug == "last_n_candles":
        extra.append({"purpose": "filter", "rule_name": "N-bar condition", "left_operand": "last_n_candles_all", "operator": "equal", "right_value": 1, "logic_notes": "All last N candles satisfy sub-condition (AND logic)."})
    INDICATORS.append({
        "slug": slug,
        "display_name": name,
        "category": "Candle Reference Conditions",
        "indicator_type": "reference",
        "default_params": {"offset": 1} if "nth" in slug or slug == "candle_at" else {},
        "implementation_status": "planned",
        "description": f"Reference candle for comparative conditions: {name}.",
        "rules": _candle_ref_rules(slug, name) + extra,
    })

# Utility / Logic (84–96)
_UTILITY = [
    ("signal", "Signal", "logic", "External boolean signal trigger."),
    ("external_signal", "External Signal", "logic", "Webhook or API-fed signal."),
    ("condition", "Condition", "logic", "Nested AND/OR condition group."),
    ("math", "Math", "logic", "Arithmetic expression on indicators."),
    ("previous_value", "Previous Value (PV)", "logic", "Prior bar value of any indicator."),
    ("previous_indecision", "Previous Indecision", "logic", "Prior bar indecision state."),
    ("previous_value_indecision", "Previous Value Indecision", "logic", "PV with indecision filter."),
    ("manual_trigger", "Manual Trigger", "logic", "User-initiated one-shot entry."),
    ("transaction_stoploss", "Transaction StopLoss", "logic", "Per-trade fixed stop loss."),
    ("basket", "Basket", "logic", "Multi-leg basket condition."),
    ("tradingview", "TradingView", "logic", "TradingView alert webhook signal."),
    ("chartink", "Chartink", "logic", "Chartink scanner signal."),
    ("more_options", "More Options", "logic", "Extended StrykeX condition options."),
]

for slug, name, itype, desc in _UTILITY:
    rules: list[CatalogRule] = []
    if slug == "transaction_stoploss":
        rules = [
            {"purpose": "stop_loss", "rule_name": "Fixed % stop", "left_operand": "close", "operator": "less_than", "right_operand": "entry_price_stop_pct", "logic_notes": "Exit when loss exceeds configured % from entry."},
            {"purpose": "stop_loss", "rule_name": "Fixed points stop", "left_operand": "close", "operator": "less_than", "right_value": None, "right_operand": "entry_price_minus_points", "logic_notes": "Exit when price falls N points below entry."},
        ]
    elif slug == "math":
        rules = [
            {"purpose": "filter", "rule_name": "Math expression", "left_operand": "math_result", "operator": "greater_than", "right_value": 0, "logic_notes": "Custom formula e.g. (close - open) / atr > 1."},
        ]
    elif slug == "condition":
        rules = [
            {"purpose": "filter", "rule_name": "AND group", "left_operand": "condition_group", "operator": "equal", "right_value": 1, "logic_notes": "All nested conditions must be true."},
            {"purpose": "filter", "rule_name": "OR group", "left_operand": "condition_group", "operator": "equal", "right_value": 1, "logic_notes": "Any nested condition true (set logic=or)."},
        ]
    elif slug in ("signal", "external_signal", "tradingview", "chartink"):
        rules = [
            {"purpose": "entry_long", "rule_name": f"{name} fire", "left_operand": slug, "operator": "equal", "right_value": 1, "logic_notes": f"{name} = 1 triggers entry on next bar."},
            {"purpose": "exit_long", "rule_name": f"{name} exit", "left_operand": f"{slug}_exit", "operator": "equal", "right_value": 1, "logic_notes": f"{name} exit signal closes position."},
        ]
    elif slug == "previous_value":
        rules = [
            {"purpose": "entry_long", "rule_name": "PV cross", "left_operand": "indicator", "operator": "crosses_above", "right_operand": "previous_value", "logic_notes": "Current value crosses above prior bar value."},
        ]
    elif slug == "basket":
        rules = [
            {"purpose": "entry_long", "rule_name": "Basket all long", "left_operand": "basket_signal", "operator": "equal", "right_value": 1, "logic_notes": "All legs in basket satisfy long condition."},
        ]
    else:
        rules = [
            {"purpose": "filter", "rule_name": f"{name} active", "left_operand": slug, "operator": "equal", "right_value": 1, "logic_notes": f"{desc}"},
        ]
    INDICATORS.append({
        "slug": slug,
        "display_name": name,
        "category": "Utility / Logic Conditions",
        "indicator_type": itype,
        "default_params": {},
        "implementation_status": "planned",
        "description": desc,
        "rules": rules,
    })


def load_catalog() -> list[CatalogIndicator]:
    return INDICATORS


def catalog_by_slug() -> dict[str, CatalogIndicator]:
    return {item["slug"]: item for item in INDICATORS}


def parameter_map() -> dict[str, str]:
    """Map StrykeX display names and aliases to internal slugs."""
    mapping: dict[str, str] = {
        "close": "close",
        "open": "open",
        "high": "high",
        "low": "low",
        "current close": "current_close",
        "current_close": "current_close",
        "current candle": "current_candle",
    }
    for item in INDICATORS:
        slug = item["slug"]
        name = item["display_name"]
        mapping[slug] = slug
        mapping[name.lower()] = slug
        mapping[name.lower().replace(" ", "_")] = slug
        mapping[name.lower().replace(" (", "_").replace(")", "").replace(" ", "_")] = slug
    mapping.update({
        "ema 20": "ema",
        "ema 9": "ema",
        "ema_20": "ema_20",
        "ema_9": "ema_9",
        "rsi": "rsi",
        "rsi 14": "rsi",
        "bollinger band": "bollinger_band",
        "bollinger": "bollinger_band",
    })
    return mapping


def rule_count() -> int:
    return sum(len(item.get("rules", [])) for item in INDICATORS)


def indicator_count() -> int:
    return len(INDICATORS)
