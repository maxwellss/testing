"""Main loop: find new Solana tokens, filter them, alert on the good ones.

Run from the repo root:
    python -m memebot.scanner          # keep scanning every POLL_SECONDS
    python -m memebot.scanner --once   # scan once and exit
    python -m memebot.scanner --verbose  # also show why tokens were skipped
"""

import argparse
import json
import time
from pathlib import Path

from . import sources
from .alerts import send_alert
from .config import Settings
from .filters import evaluate


def load_seen(data_dir):
    path = Path(data_dir) / "seen.json"
    if path.exists():
        try:
            return set(json.loads(path.read_text()))
        except ValueError:
            pass
    return set()


def save_seen(seen, data_dir):
    path = Path(data_dir) / "seen.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(seen)))


def scan_once(settings, seen, fetch=sources.get_json, alert=send_alert, verbose=False, now_ms=None):
    """One pass. Returns the list of token addresses that triggered an alert."""
    now_ms = now_ms or int(time.time() * 1000)
    addresses = [a for a in sources.latest_solana_tokens(fetch) if a not in seen]
    pairs = sources.best_pairs(addresses, fetch)
    alerted = []

    for addr, pair in pairs.items():
        symbol = (pair.get("baseToken") or {}).get("symbol", addr[:6])
        verdict = evaluate(pair, settings, now_ms)
        # Only call RugCheck for tokens that pass the cheap market checks first.
        if verdict.passed and settings.use_rugcheck:
            report = sources.rugcheck_summary(addr, fetch)
            verdict = evaluate(pair, settings, now_ms, rug_report=report)
            if report is None:
                verdict.warnings.append("RugCheck unavailable, safety not checked")
        if verdict.passed:
            alert(pair, verdict, settings)
            seen.add(addr)
            alerted.append(addr)
        elif verbose:
            print(f"skip {symbol}: {'; '.join(verdict.reasons)}")

    print(f"[{time.strftime('%H:%M:%S')}] checked {len(pairs)} tokens, {len(alerted)} alert(s)")
    return alerted


def main():
    parser = argparse.ArgumentParser(description="Solana meme coin alert scanner")
    parser.add_argument("--once", action="store_true", help="scan once and exit")
    parser.add_argument("--verbose", action="store_true", help="show why tokens were skipped")
    args = parser.parse_args()

    settings = Settings.from_env()
    seen = load_seen(settings.data_dir)
    print("Meme coin scanner started (alerts only, no trading). Ctrl+C to stop.")

    try:
        while True:
            scan_once(settings, seen, verbose=args.verbose)
            save_seen(seen, settings.data_dir)
            if args.once:
                break
            time.sleep(settings.poll_seconds)
    except KeyboardInterrupt:
        save_seen(seen, settings.data_dir)
        print("\nStopped.")


if __name__ == "__main__":
    main()
