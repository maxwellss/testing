"""Send alerts: always to the console and a CSV log, optionally to Telegram."""

import csv
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CSV_FIELDS = [
    "time_utc", "symbol", "name", "token_address", "price_usd", "liquidity_usd",
    "volume_1h_usd", "buys_1h", "sells_1h", "market_cap_usd", "warnings", "url",
]


def alert_row(pair, verdict, now=None):
    now = now or datetime.now(timezone.utc)
    base = pair.get("baseToken") or {}
    txns = (pair.get("txns") or {}).get("h1") or {}
    return {
        "time_utc": now.strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": base.get("symbol", "?"),
        "name": base.get("name", "?"),
        "token_address": base.get("address", ""),
        "price_usd": pair.get("priceUsd", ""),
        "liquidity_usd": (pair.get("liquidity") or {}).get("usd", ""),
        "volume_1h_usd": (pair.get("volume") or {}).get("h1", ""),
        "buys_1h": txns.get("buys", ""),
        "sells_1h": txns.get("sells", ""),
        "market_cap_usd": pair.get("marketCap") or pair.get("fdv") or "",
        "warnings": "; ".join(verdict.warnings),
        "url": pair.get("url", ""),
    }


def format_message(row):
    lines = [
        f"🚨 {row['symbol']} ({row['name']})",
        f"Price: ${row['price_usd']}",
        f"Liquidity: ${float(row['liquidity_usd'] or 0):,.0f}",
        f"1h volume: ${float(row['volume_1h_usd'] or 0):,.0f}",
        f"1h buys/sells: {row['buys_1h']}/{row['sells_1h']}",
        f"Market cap: ${float(row['market_cap_usd'] or 0):,.0f}",
    ]
    if row["warnings"]:
        lines.append(f"⚠️ {row['warnings']}")
    lines += [row["url"], f"Token: {row['token_address']}"]
    return "\n".join(lines)


def log_csv(row, data_dir):
    path = Path(data_dir) / "alerts.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()
    with path.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if new_file:
            writer.writeheader()
        writer.writerow(row)


def send_telegram(text, bot_token, chat_id):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    body = urllib.parse.urlencode({"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=body), timeout=15) as resp:
            return json.loads(resp.read().decode()).get("ok", False)
    except Exception as e:  # never let a failed alert crash the scanner
        print(f"[warn] Telegram send failed: {e}")
        return False


def send_alert(pair, verdict, settings):
    row = alert_row(pair, verdict)
    message = format_message(row)
    print("\n" + message + "\n")
    log_csv(row, settings.data_dir)
    if settings.telegram_bot_token and settings.telegram_chat_id:
        send_telegram(message, settings.telegram_bot_token, settings.telegram_chat_id)
