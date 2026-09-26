"""Run with:  python -m unittest discover tests"""

import csv
import tempfile
import unittest
from pathlib import Path

from memebot import sources
from memebot.alerts import alert_row, format_message, log_csv
from memebot.config import Settings
from memebot.filters import evaluate
from memebot.scanner import load_seen, save_seen, scan_once

NOW_MS = 1_760_000_000_000
HOUR_MS = 3_600_000
GOOD = "GoodMint111111111111111111111111111111111111"
RUG = "RugMint1111111111111111111111111111111111111"
SMALL = "SmallMint11111111111111111111111111111111111"


def make_pair(address, symbol="MEME", liquidity=50_000, volume_1h=20_000, buys=120, sells=60,
              market_cap=800_000, age_hours=2.0):
    return {
        "chainId": "solana",
        "dexId": "raydium",
        "url": f"https://dexscreener.com/solana/{address.lower()}",
        "baseToken": {"address": address, "name": f"{symbol} Coin", "symbol": symbol},
        "priceUsd": "0.00123",
        "txns": {"h1": {"buys": buys, "sells": sells}},
        "volume": {"h1": volume_1h},
        "liquidity": {"usd": liquidity},
        "marketCap": market_cap,
        "pairCreatedAt": NOW_MS - int(age_hours * HOUR_MS),
    }


def fake_fetch(responses):
    """Return a fetch() that serves canned JSON by URL substring."""
    calls = []

    def fetch(url):
        calls.append(url)
        for key, value in responses.items():
            if key in url:
                return value
        raise ValueError(f"no fake response for {url}")

    fetch.calls = calls
    return fetch


class EvaluateTests(unittest.TestCase):
    def setUp(self):
        self.s = Settings()

    def test_healthy_token_passes(self):
        v = evaluate(make_pair(GOOD), self.s, NOW_MS)
        self.assertTrue(v.passed, v.reasons)

    def test_low_liquidity_fails(self):
        v = evaluate(make_pair(GOOD, liquidity=2_000), self.s, NOW_MS)
        self.assertFalse(v.passed)
        self.assertIn("liquidity", v.reasons[0])

    def test_more_sells_than_buys_fails(self):
        v = evaluate(make_pair(GOOD, buys=30, sells=90), self.s, NOW_MS)
        self.assertTrue(any("buy/sell" in r for r in v.reasons))

    def test_age_limits(self):
        self.assertFalse(evaluate(make_pair(GOOD, age_hours=0.01), self.s, NOW_MS).passed)
        self.assertFalse(evaluate(make_pair(GOOD, age_hours=48), self.s, NOW_MS).passed)

    def test_missing_fields_do_not_crash(self):
        v = evaluate({"baseToken": {"address": GOOD}}, self.s, NOW_MS)
        self.assertFalse(v.passed)

    def test_rugcheck_danger_fails_and_warn_is_kept(self):
        report = {"risks": [
            {"name": "Mint Authority still enabled", "level": "danger"},
            {"name": "Low amount of LP Providers", "level": "warn"},
        ]}
        v = evaluate(make_pair(GOOD), self.s, NOW_MS, rug_report=report)
        self.assertFalse(v.passed)
        self.assertIn("RugCheck danger: Mint Authority still enabled", v.reasons)
        self.assertIn("RugCheck warning: Low amount of LP Providers", v.warnings)


class SourcesTests(unittest.TestCase):
    def test_latest_tokens_solana_only_and_deduped(self):
        fetch = fake_fetch({
            "token-profiles": [
                {"chainId": "solana", "tokenAddress": GOOD},
                {"chainId": "ethereum", "tokenAddress": "0xabc"},
            ],
            "token-boosts": [{"chainId": "solana", "tokenAddress": GOOD},
                             {"chainId": "solana", "tokenAddress": RUG}],
        })
        self.assertEqual(sources.latest_solana_tokens(fetch), [GOOD, RUG])

    def test_best_pair_is_most_liquid(self):
        fetch = fake_fetch({"/tokens/v1/solana/": [
            make_pair(GOOD, liquidity=5_000),
            make_pair(GOOD, liquidity=90_000),
        ]})
        best = sources.best_pairs([GOOD], fetch)
        self.assertEqual(best[GOOD]["liquidity"]["usd"], 90_000)

    def test_api_failure_returns_empty(self):
        self.assertEqual(sources.latest_solana_tokens(fake_fetch({})), [])


class ScanOnceTests(unittest.TestCase):
    def test_only_safe_token_alerts_and_is_not_repeated(self):
        fetch = fake_fetch({
            "token-profiles": [{"chainId": "solana", "tokenAddress": a} for a in (GOOD, RUG, SMALL)],
            "token-boosts": [],
            "/tokens/v1/solana/": [make_pair(GOOD), make_pair(RUG, symbol="RUG"),
                                   make_pair(SMALL, symbol="TINY", liquidity=500)],
            f"/tokens/{GOOD}/report": {"risks": []},
            f"/tokens/{RUG}/report": {"risks": [{"name": "Freeze Authority", "level": "danger"}]},
        })
        alerts = []
        seen = set()
        settings = Settings()

        result = scan_once(settings, seen, fetch=fetch, alert=lambda p, v, s: alerts.append(p), now_ms=NOW_MS)
        self.assertEqual(result, [GOOD])
        self.assertEqual(len(alerts), 1)
        # RugCheck is skipped for tokens that already failed the market filters.
        self.assertFalse(any(SMALL in url and "rugcheck" in url for url in fetch.calls))

        again = scan_once(settings, seen, fetch=fetch, alert=lambda p, v, s: alerts.append(p), now_ms=NOW_MS)
        self.assertEqual(again, [])
        self.assertEqual(len(alerts), 1)


class OutputTests(unittest.TestCase):
    def test_csv_log_and_message(self):
        from memebot.filters import Verdict
        row = alert_row(make_pair(GOOD), Verdict(True, warnings=["RugCheck warning: x"]))
        msg = format_message(row)
        self.assertIn("MEME", msg)
        self.assertIn("RugCheck warning: x", msg)
        with tempfile.TemporaryDirectory() as d:
            log_csv(row, d)
            log_csv(row, d)
            with (Path(d) / "alerts.csv").open() as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["token_address"], GOOD)

    def test_seen_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            save_seen({GOOD, RUG}, d)
            self.assertEqual(load_seen(d), {GOOD, RUG})


if __name__ == "__main__":
    unittest.main()
