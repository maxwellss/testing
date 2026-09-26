"""Fetch token data from free public APIs (no API keys needed).

- DexScreener: newly listed token profiles, plus price/liquidity/volume per pair.
  Docs: https://docs.dexscreener.com/api/reference
- RugCheck: Solana token risk report (mint authority, LP lock, holder spread...).
  Docs: https://api.rugcheck.xyz/swagger/index.html
"""

import json
import urllib.error
import urllib.request

DEXSCREENER = "https://api.dexscreener.com"
RUGCHECK = "https://api.rugcheck.xyz/v1"
CHAIN = "solana"
USER_AGENT = "memebot/0.1"


def get_json(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def latest_solana_tokens(fetch=get_json):
    """Addresses of Solana tokens that recently got a DexScreener profile or boost."""
    addresses = []
    for path in ("/token-profiles/latest/v1", "/token-boosts/latest/v1"):
        try:
            items = fetch(DEXSCREENER + path)
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            print(f"[warn] DexScreener {path} failed: {e}")
            continue
        for item in items or []:
            addr = item.get("tokenAddress")
            if item.get("chainId") == CHAIN and addr and addr not in addresses:
                addresses.append(addr)
    return addresses


def best_pairs(addresses, fetch=get_json):
    """Map token address -> its most liquid trading pair (DexScreener pair dict)."""
    best = {}
    for i in range(0, len(addresses), 30):  # API accepts up to 30 addresses per call
        batch = addresses[i:i + 30]
        try:
            pairs = fetch(f"{DEXSCREENER}/tokens/v1/{CHAIN}/{','.join(batch)}")
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            print(f"[warn] DexScreener pairs lookup failed: {e}")
            continue
        for pair in pairs or []:
            addr = (pair.get("baseToken") or {}).get("address")
            if addr not in batch:
                continue
            liq = (pair.get("liquidity") or {}).get("usd") or 0
            current = best.get(addr)
            if current is None or liq > ((current.get("liquidity") or {}).get("usd") or 0):
                best[addr] = pair
    return best


def rugcheck_summary(address, fetch=get_json):
    """RugCheck summary report for a token, or None if unavailable."""
    try:
        return fetch(f"{RUGCHECK}/tokens/{address}/report/summary")
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        print(f"[warn] RugCheck failed for {address}: {e}")
        return None
