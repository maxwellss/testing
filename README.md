testing
=======

This is a test

Just figuring out how to use this thing. Web developer from Whangarei, Northland, New Zealand

## What's here

- `memebot/`: Solana meme coin **alert** scanner (stage 1). It watches for new tokens and alerts you. It does **not** trade.
- `plan.md`: the product plan. Update it as decisions are made.
- `index.html`: a starter landing page (for later, if this becomes a product).

## Meme coin alert bot

### What it does
Every minute (by default) it:
1. Gets the latest Solana tokens listed on [DexScreener](https://dexscreener.com).
2. Checks each one's liquidity, 1-hour volume, buys vs sells, age and market cap.
3. For tokens that pass, asks [RugCheck](https://rugcheck.xyz) for scam red flags
   (for example: the creator can still mint more coins or freeze your wallet).
4. Alerts you about tokens that pass every check: in the terminal, in `data/alerts.csv`,
   and optionally on Telegram.

It only needs Python 3.9+, with nothing to install and no API keys.

### Run it on your computer
```bash
git clone https://github.com/maxwellss/testing.git
cd testing
git checkout claude/100-dollar-credit-location-qn5sr9

cp .env.example .env              # optional: adjust filters / add Telegram
python3 -m memebot.scanner --once --verbose   # one scan, shows why tokens were skipped
python3 -m memebot.scanner                    # keep scanning; Ctrl+C to stop
```
On Windows, use `python` instead of `python3`, and `copy` instead of `cp`.

### Tuning
All filters are in `.env` (see `.env.example` for the list). Too many alerts? Raise
`MIN_LIQUIDITY_USD` and `MIN_VOLUME_1H_USD`. Too few? Lower them.

`data/alerts.csv` keeps every alert, including the price at alert time. That becomes
the data for checking whether the alerts would have made money (the paper-trading stage).

### Tests
```bash
python3 -m unittest discover tests
```

### Limits to know
- DexScreener's "latest" feeds show tokens that recently added a profile or paid for
  a boost, not every single launch. That's fine for stage 1. A pump.fun or Raydium
  launch feed can be added later.
- Passing every check does **not** make a token safe. It only filters out the most obvious traps.
- Not financial advice. Only ever risk money you can afford to lose.
