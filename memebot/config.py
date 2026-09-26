"""Settings, read from environment variables or a local .env file."""

import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv(path=".env"):
    """Load KEY=VALUE lines from a .env file into os.environ (existing vars win)."""
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _float(name, default):
    return float(os.environ.get(name, default))


def _bool(name, default):
    return os.environ.get(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


@dataclass
class Settings:
    # Filters: a token must pass all of these to trigger an alert.
    min_liquidity_usd: float = 10_000
    min_volume_1h_usd: float = 5_000
    min_buys_1h: float = 20
    min_buy_sell_ratio: float = 1.0
    min_age_minutes: float = 5
    max_age_hours: float = 24
    max_market_cap_usd: float = 5_000_000
    use_rugcheck: bool = True

    # Loop and output.
    poll_seconds: float = 60
    data_dir: str = "data"

    # Optional Telegram alerts.
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    @classmethod
    def from_env(cls):
        load_dotenv()
        return cls(
            min_liquidity_usd=_float("MIN_LIQUIDITY_USD", cls.min_liquidity_usd),
            min_volume_1h_usd=_float("MIN_VOLUME_1H_USD", cls.min_volume_1h_usd),
            min_buys_1h=_float("MIN_BUYS_1H", cls.min_buys_1h),
            min_buy_sell_ratio=_float("MIN_BUY_SELL_RATIO", cls.min_buy_sell_ratio),
            min_age_minutes=_float("MIN_AGE_MINUTES", cls.min_age_minutes),
            max_age_hours=_float("MAX_AGE_HOURS", cls.max_age_hours),
            max_market_cap_usd=_float("MAX_MARKET_CAP_USD", cls.max_market_cap_usd),
            use_rugcheck=_bool("USE_RUGCHECK", cls.use_rugcheck),
            poll_seconds=_float("POLL_SECONDS", cls.poll_seconds),
            data_dir=os.environ.get("DATA_DIR", cls.data_dir),
            telegram_bot_token=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=os.environ.get("TELEGRAM_CHAT_ID", ""),
        )
