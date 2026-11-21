# Trend Navigator — TradingView indicator voor crypto

Overlay-indicator (Pine Script v6) die EMA-crosses, ADX/DMI, volume, RSI en een hogere-timeframe-filter combineert. Zo zie je **in één oogopslag** de trend en krijg je alleen **bevestigde** BUY/SELL-signalen met een ATR-trailing stop.

De standaardinstellingen zijn **gebacktest en getoetst buiten de trainingsdata** op **BTC, ETH, SOL en HYPE** (zie [Backtest](#backtest)).

| Bestand | Wat |
|---|---|
| [`TrendNavigator.pine`](TrendNavigator.pine) | De indicator: trendkleuren, signalen, stop, dashboard en alerts |
| [`TrendNavigatorStrategy.pine`](TrendNavigatorStrategy.pine) | Dezelfde logica als `strategy()` voor de Strategy Tester van TradingView |
| [`backtest/`](backtest) | Python-backtest: data ophalen, grid search, stresstest |

## Installeren

1. Open TradingView → **Pine Editor**.
2. Plak `TrendNavigator.pine` → **Opslaan** → **Toevoegen aan grafiek**.
3. Zet de chart op **4H** (beste timeframe uit de backtest).
4. Optioneel: plak ook `TrendNavigatorStrategy.pine` en open de **Strategy Tester** om de resultaten op je eigen exchange-data te zien.
5. Alerts: **Alert toevoegen** → *TrendNav* → *Any alert() function call* (melding bevat stop en score) of kies BUY / SELL / trendwissel.

## Wat zie je op de chart

| Element | Betekenis |
|---|---|
| **Candlekleur** | Fel groen = sterk bullish · lichtgroen = bullish · **grijs = zijwaarts (ADX laag): niet handelen** · lichtrood = bearish · fel rood = sterk bearish |
| **EMA-lint 9/21** | Groen gevuld = korte termijn omhoog, rood = omlaag |
| **EMA 50 (oranje) / 200 (paars)** | Hoofdtrend |
| **BUY / SELL** | Bevestigd signaal + trendscore (bv. `+5/6`) |
| **Rode stoplijn** | Start op 2× ATR en schuift mee op 3× ATR van de hoogste high (long) of laagste low (short) |
| **EXIT +x%** | Positie gesloten door de stop, met resultaat |
| **Oranje bol onder candle** | Long-liquidatiegolf (longs gedwongen gesloten). Grotere bol = heftiger |
| **Blauwe bol boven candle** | Short-liquidatiegolf (short squeeze) |
| **Oranje/blauwe lijnen** | Geschatte liquidatieniveaus van 25×/50×/100× posities. Dikker = lagere hefboom. Verdwijnen zodra de koers ze raakt |
| **Dashboard** | Trend, score, ADX, DI+/DI−, EMA's, volume, RSI, HTF-trend, laatste signaal + hit-rate, open positie, open interest 24u, laatste liquidatiegolf, dichtstbijzijnde liq-niveaus |

## Signaallogica

**BUY** (bij het sluiten van de candle, geen repaint) als alles klopt:

1. EMA 9 kruist boven EMA 21 (of deed dat ≤ 3 bars geleden)
2. ADX ≥ 15 en DI+ > DI−
3. Volume ≥ 1,0× het 20-bar gemiddelde
4. Koers boven EMA 200
5. Dagtrend (HTF = 1D) niet bearish
6. RSI < 70

**SELL** is het spiegelbeeld. Een tegengesteld signaal draait de positie om.

**Trendscore (−6 … +6):** koers vs EMA 50, EMA 9 vs 21, EMA 50 vs 200, DI+ vs DI−, RSI vs 50 en de HTF-trend tellen elk ±1.

## Liquidaties

Echte liquidatiedata is in Pine Script niet beschikbaar. TradingView levert voor crypto-perps wel **open interest** (`…USDT.P_OI`), en daar is de indicator op gebaseerd.

**1. Liquidatiegolven (bollen).** Bij liquidaties worden posities gedwongen gesloten, waardoor de open interest abnormaal snel daalt. Een daling van ≥ 2 standaardafwijkingen met een rode candle betekent dat longs geliquideerd zijn (oranje). Bij een groene candle zijn shorts geliquideerd (blauw).

*Gevalideerd* tegen ruim 24.000 echte liquidatieorders van OKX (24 uur, 5m, BTC/ETH/SOL/HYPE):
- correlatie tussen OI-daling en geliquideerd volume: −0,46 (BTC), −0,71 (ETH), −0,51 (SOL), −0,29 (HYPE)
- 59% van de gedetecteerde golven valt in de 10% zwaarste liquidatiebars (toeval: 10%)
- de richting (longs of shorts) klopt in **85%** van de gevallen

**2. Geschatte liquidatieniveaus (lijnen).** Vanaf candles met hoog volume (≥ 1,5× het gemiddelde) wordt berekend waar 25×, 50× en 100× posities geliquideerd worden: `entry × (1 ∓ 1/hefboom ± onderhoudsmarge)`. Raakt de koers een niveau, dan verdwijnt het. Niveaus die nog niet geraakt zijn, werken vaak als magneet. Dit is een **schatting**; echte posities en hefbomen zijn onbekend.

**Open interest-symbool.** Dit wordt automatisch gekozen (de perp op dezelfde exchange, bv. `BINANCE:BTCUSDT.P_OI`). Staat je chart op een exchange zonder perps (bv. Coinbase), vul dan bij *Liquidaties → Open-interest symbool* bijvoorbeeld `BINANCE:BTCUSDT.P_OI` in. Toont het dashboard "n.v.t.", dan is er geen OI-data voor dat symbool.

**Wat zegt het over de koers?** Event-studie op 4H, mrt–nov 2026, 4 munten:

| Na een… | n | +24u positief | +48u positief |
|---|---|---|---|
| Long-liquidatiegolf **in uptrend** (boven EMA 200) | 33 | 61% | 64% |
| Long-liquidatiegolf in downtrend | 60 | 47% | **28%** |
| Short squeeze in uptrend | 34 | 44% (+4u: 35%) | 50% |
| Basis (alle bars) | 5.625 | 50% | 48% |

Lees dit als *context*, niet als signaal: in een uptrend is een long-flush vaak een koopkans, in een downtrend zet de daling meestal door, en na een short squeeze kun je beter niet direct kopen. De aantallen zijn te klein om er een filter op te bouwen. Daarom **veranderen liquidaties de BUY/SELL-signalen niet**. Er zijn wel aparte alerts voor (*Long-liquidaties* / *Short-liquidaties*).

## Backtest

**Data:** OKX spot USDT, 4H, nov 2022 – nov 2026 (HYPE: nov 2025 – nov 2026). **Kosten:** 0,07% per kant. Entry op de open na het signaal, 100% van het kapitaal per trade, geen hefboom, long en short.

**Methode:** grid search over 1.800 combinaties per timeframe (EMA-paren, ADX, volume, filters, 5 exit-methodes, long-only of long+short). Er is alleen geoptimaliseerd op de **eerste 65%** van de data; de **laatste 35%** dient als ongeziene test. Gekozen is de configuratie die op de *slechtste* munt het best presteert, niet die met de hoogste winst op één munt.

### Resultaat standaardinstellingen (4H)

| Munt | Trades | Winrate | Profit factor | Rendement | Max DD | PF train | PF test (rendement) | Buy & hold |
|---|---|---|---|---|---|---|---|---|
| BTC  | 97  | 37% | 1.61 | +77%  | 23% | 1.66 | 1.56 (+24%)  | +244% |
| ETH  | 105 | 34% | 1.78 | +211% | 30% | 1.18 | 2.98 (+179%) | +34%  |
| SOL  | 102 | 41% | 1.27 | +44%  | 32% | 1.05 | 1.72 (+56%)  | +492% |
| HYPE | 29  | 52% | 2.20 | +83%  | 19% | 1.91 | 3.85 (+27%)  | +100% |

Testperiode: vanaf juni 2025 (HYPE: vanaf juli 2026).

### Wat de backtest leerde

- **4H werkt, lagere timeframes niet.** Op 1H verliest dezelfde logica op BTC en SOL, en op 15m werkt geen enkele configuratie buiten de trainingsdata (pure overfitting).
- **De exit is het belangrijkste onderdeel.** Een vast doel van 3× ATR sneed de grote crypto-trends af: de oorspronkelijke instellingen verloren op 10 van de 11 combinaties van munt en timeframe. Met een trailing stop van 3× ATR is dezelfde entry winstgevend.
- **Robuust:** als je ADX (10–20), stop (1,5–3×), trailing (3–3,5×), EMA's (10–12 / 21–30) of het venster (0–5) varieert, blijft de profit factor op alle munten boven 1.
- **EMA 200-filter:** zonder dit filter daalt de profit factor fors (SOL 1.05).
- **HTF 1D aan:** zelfde profit factor, lagere drawdown (SOL 32% in plaats van 46%). Deze keuze is gemaakt op de volledige periode.

### Eerlijke kanttekeningen

- In sterke bull-jaren verdien je **veel minder dan met buy & hold** (BTC 2023: +16% tegenover +156%). De kracht zit in bear-markten: in 2025–2026 bleef de strategie winstgevend terwijl de munten 35–46% daalden.
- Winrate ±35–50%: je hebt veel kleine verliezen en een paar grote winnaars. Dat vraagt discipline.
- HYPE heeft maar een jaar data en 29 trades, dus die cijfers zijn statistisch zwak.
- Resultaten uit het verleden bieden geen garantie. Dit is geen financieel advies.

### Zelf opnieuw draaien

```bash
cd backtest
python3 fetch.py          # haalt OKX-candles op naar backtest/data/
python3 grid.py 4H        # grid search (ook: 1H, 15m)
python3 analyze.py 4H 6   # top-configs met train/test-resultaten
python3 stress.py         # gevoeligheid + resultaten per jaar

# liquidaties
python3 fetch_oi.py && python3 fetch_liq.py
python3 validate_liq.py   # OI-daling vs echte liquidaties (5m)
python3 proxy_rule.py     # precisie van de detectieregel
python3 liq_event4h.py    # koersverloop na liquidatiegolven (4H)
```

## Aanbevolen instellingen per stijl

| Stijl | Chart | HTF | Opmerking |
|---|---|---|---|
| **Swing (aanbevolen)** | **4H** | **1D** | Getoetste standaardinstellingen |
| Positie | 1D | 1W | Niet getest; verwacht minder signalen |
| Daytrading | 1H | 4H | Backtest zwak; alleen als trendoverzicht gebruiken, niet voor signalen |
