# Product Plan

Fill this in and keep it updated. Claude Code reads this file at the start of a
session so it knows what you're building.

## The idea
A trading bot for meme coins, for my own use (stage 1). It watches newly
launched Solana tokens, filters out the obvious scams, and alerts me. Automatic
trading comes later.

## Open decisions
- [x] **Who is it for?** Just me for stage 1. Maybe a product later.
- [x] **Which blockchain?** Solana first. Possibly Robinhood later (look into what it offers for crypto and API access).
- [x] **What does the bot do?** Alerts first; automatic trading later.

## Target customer
<!-- Only needed if this becomes a product for others. -->

## How it makes money
Two routes, with very different risk:
1. **Trading profits.** High risk. Most meme coins go to zero, and new launches
   are full of rug pulls and faster bots.
2. **Selling tools.** For example a token safety checker, a new-launch scanner
   or a paid alert channel. You earn from subscriptions whether or not the coins go up.
   Check the rules first: in New Zealand, anything that looks like financial advice
   or managing other people's money may fall under the FMA.

## Build order
1. **Scanner:** detect new tokens and pull price, liquidity and holder data.
2. **Safety filter:** flag red flags (mint authority still enabled, liquidity
   not locked, a few wallets holding most of the supply).
3. **Paper trading:** run the strategy with pretend money and log every trade.
4. **Real trading:** only if paper results hold up, from a separate wallet
   holding a small amount you can afford to lose.

## Safety rules
- Never commit private keys, seed phrases or API keys to this repo.
  Keep them in a `.env` file that's listed in `.gitignore`.
- Use a dedicated bot wallet, never your main wallet.
- Set hard limits on the maximum spend per trade and the maximum loss per day.

## Must-have features (version 1)
- [x] New token scanner (DexScreener) → `memebot/`
- [x] Safety check for each token (market filters + RugCheck)
- [x] Alerts: console, `data/alerts.csv`, optional Telegram
- [ ] Paper trading: track the price after each alert and measure would-be profit/loss

## Later / nice to have
- Faster launch feed (pump.fun / Raydium new pools)
- Live trading
- Robinhood support
- Web dashboard (could reuse `index.html`)

## Progress log
- 2026-09-26: Repo set up with `plan.md` and a starter landing page (`index.html`).
- 2026-09-26: Product direction set: meme coin trading bot. Plan drafted.
- 2026-09-26: Decisions: just me, Solana first, alerts before automation. Built the stage 1 alert scanner.
