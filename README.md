# Trend Navigator — TradingView indicator

Eén overlay-indicator (Pine Script v6) die EMA-crosses, ADX/DMI, volume, RSI en een hogere-timeframe-filter combineert, zodat je **in één oogopslag** de trend ziet en alleen **bevestigde** BUY/SELL-signalen krijgt.

## Installeren

1. Open TradingView → **Pine Editor** (onderaan de chart).
2. Plak de inhoud van [`TrendNavigator.pine`](TrendNavigator.pine).
3. Klik **Opslaan** en daarna **Toevoegen aan grafiek**.
4. Alerts: rechtsklik op de chart → **Alert toevoegen** → kies *TrendNav* → *Any alert() function call* (met SL/TP in de melding) of een van de losse condities.

## Wat zie je op de chart

| Element | Betekenis |
|---|---|
| **Candlekleur** | Fel groen = sterk bullish · lichtgroen = bullish · grijs = zijwaarts/geen trend (ADX laag) · lichtrood = bearish · fel rood = sterk bearish |
| **EMA-lint 9/21** | Groen gevuld = korte termijn omhoog, rood = omlaag |
| **EMA 50 (oranje) / 200 (paars)** | Hoofdtrend; 50 boven 200 = golden cross |
| **BUY / SELL label** | Bevestigd signaal + trendscore (bv. `+5/6`) |
| **SL / TP / Entry lijnen** | ATR-stop (1,5×) en doel (3×) = risk/reward 1:2 |
| **TP ✓ / SL ✗** | Wanneer het doel of de stop geraakt werd |
| **Dashboard** | Trend, score, ADX, DI+/DI−, EMA's, relatief volume, RSI, HTF-trend, laatste signaal en hit-rate |

## Signaallogica

Een **BUY** verschijnt (bij het sluiten van de candle, dus geen repaint) als:

1. EMA 9 kruist boven EMA 21 (of deed dat maximaal *N* bars geleden — instelbaar, standaard 3);
2. **ADX ≥ 20** (er is een trend) en **DI+ > DI−**;
3. **Volume ≥ 1,2×** het 20-bar gemiddelde (overgeslagen als het symbool geen volume heeft);
4. Prijs **boven EMA 200**;
5. **Hogere timeframe** (standaard 4H) is niet bearish;
6. **RSI < 70** (niet kopen in overbought).

**SELL** is het spiegelbeeld. Per EMA-cross komt maximaal één signaal.

### Trendscore (−6 … +6)

Elk onderdeel telt +1 (bullish) of −1 (bearish): prijs vs EMA 50, EMA 9 vs 21, EMA 50 vs 200, DI+ vs DI−, RSI vs 50, HTF-trend. Score ≥ +2 = bullish, ≥ +4 met ADX ≥ 30 = sterk bullish. Als de ADX onder 20 zit is de markt **zijwaarts** (grijs), ongeacht de score.

## Aanbevolen instellingen

| Stijl | Chart TF | HTF | EMA's | Opmerking |
|---|---|---|---|---|
| Scalping | 1–5m | 15m–1H | 9/21 · 50/200 | Volume-filter 1,5× |
| Daytrading | 15m | 1H–4H | 9/21 · 50/200 | Standaard |
| Swing | 4H | 1D | 20/50 · 100/200 | ADX-min 22–25 |
| Positie | 1D | 1W | 20/50 · 100/200 | Venster 5 bars |

## Belangrijk

- Geen enkele indicator is "perfect": in zijwaartse markten geven trendvolgende systemen altijd valse signalen. De ADX-, volume- en HTF-filters verminderen dat, maar halen het niet weg.
- De hit-rate in het dashboard is een **ruwe schatting** (geen commissie of slippage, en geen echte backtest). Test elke markt en timeframe eerst.
- Dit is geen financieel advies.
