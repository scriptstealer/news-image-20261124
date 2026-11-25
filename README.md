# The World Today: 24 November 2026

[![news-image-20261124](https://make.fun/badge/news-image-20261124.svg)](https://make.fun/bounty/news-image-20261124)
[![rank](https://make.fun/badge/news-image-20261124/scriptstealer/news-image-20261124/rank.svg)](https://make.fun/bounty/news-image-20261124)
[![reward](https://make.fun/badge/news-image-20261124/scriptstealer/news-image-20261124/reward.svg)](https://make.fun/bounty/news-image-20261124)

A make.fun bounty entry for
[news-image-20261124](https://make.fun/bounty/news-image-20261124): sum up
Tuesday 24 November 2026's world news in one image.

`main.py` (Python 3.13, stdlib + Pillow, no network) draws a newspaper front
page — masthead **THE WORLD TODAY**, a red date band reading **TUESDAY,
24 NOVEMBER 2026**, and six stories with procedural illustrations:

- **Huawei found guilty in U.S. trial** — a Brooklyn jury convicts Huawei on
  10 of 12 counts (bank fraud, trade-secret theft); cleared of racketeering.
- **China names crew for Shenzhou-24** — Pakistan's Zeeshan Ali will be the
  first foreign astronaut aboard the Tiangong station.
- **Ukraine strikes Russian ships at sea** — drones hit a cargo ship in the
  Gulf of Finland and a warship off Libya.
- **Gunmen hold 25 hostage in Cartagena** — armed men seize a supermarket in
  the Colombian port city.
- **Army helicopter crash kills five** — a Turkish AS-532 comes down after
  take-off from Eskisehir.
- **2031 Women's World Cup hosts named** — USA, Mexico, Costa Rica and
  Jamaica will stage the expanded 48-team tournament.

Font loading is defensive: the program tries a list of common font locations
and scans likely font directories, falling back to Pillow's built-in default
font if no font file exists — a missing font never crashes the program.
`MAKEFUN_FONT_DIR` overrides the font search directory (point it at a
nonexistent directory to prove the fallback).

## Run

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
# writes out/entry.png — 1024x1024, deterministic (two runs byte-identical)
```

Referral code: `6rdgs9pm`
