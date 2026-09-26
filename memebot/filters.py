"""Decide whether a token is worth an alert. Pure functions, easy to test."""

from dataclasses import dataclass, field


@dataclass
class Verdict:
    passed: bool
    reasons: list = field(default_factory=list)  # why it failed (empty if passed)
    warnings: list = field(default_factory=list)  # passed, but worth knowing


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def evaluate(pair, settings, now_ms, rug_report=None):
    """Check one DexScreener pair (and optional RugCheck report) against the filters."""
    reasons = []
    warnings = []

    liquidity = _num((pair.get("liquidity") or {}).get("usd"))
    volume_1h = _num((pair.get("volume") or {}).get("h1"))
    txns_1h = (pair.get("txns") or {}).get("h1") or {}
    buys = _num(txns_1h.get("buys"))
    sells = _num(txns_1h.get("sells"))
    market_cap = _num(pair.get("marketCap") or pair.get("fdv"))
    created_ms = pair.get("pairCreatedAt")

    if liquidity < settings.min_liquidity_usd:
        reasons.append(f"liquidity ${liquidity:,.0f} < ${settings.min_liquidity_usd:,.0f}")
    if volume_1h < settings.min_volume_1h_usd:
        reasons.append(f"1h volume ${volume_1h:,.0f} < ${settings.min_volume_1h_usd:,.0f}")
    if buys < settings.min_buys_1h:
        reasons.append(f"1h buys {buys:.0f} < {settings.min_buys_1h:.0f}")
    ratio = buys / sells if sells else buys
    if ratio < settings.min_buy_sell_ratio:
        reasons.append(f"buy/sell ratio {ratio:.2f} < {settings.min_buy_sell_ratio:.2f}")
    if market_cap and market_cap > settings.max_market_cap_usd:
        reasons.append(f"market cap ${market_cap:,.0f} > ${settings.max_market_cap_usd:,.0f}")

    if not created_ms:
        reasons.append("unknown pair age")
    else:
        age_min = (now_ms - created_ms) / 60_000
        if age_min < settings.min_age_minutes:
            reasons.append(f"too new ({age_min:.0f} min)")
        elif age_min > settings.max_age_hours * 60:
            reasons.append(f"too old ({age_min / 60:.1f} h)")

    if rug_report is not None:
        for risk in rug_report.get("risks") or []:
            name = risk.get("name", "unknown risk")
            level = (risk.get("level") or "").lower()
            if level == "danger":
                reasons.append(f"RugCheck danger: {name}")
            elif level == "warn":
                warnings.append(f"RugCheck warning: {name}")

    return Verdict(passed=not reasons, reasons=reasons, warnings=warnings)
