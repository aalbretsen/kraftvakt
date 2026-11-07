<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="custom_components/kraftvakt/brand/dark_logo@2x.png">
    <img src="custom_components/kraftvakt/brand/logo@2x.png" alt="Kraftvakt" height="128">
  </picture>
</p>

# Kraftvakt: prioritert effektstyring for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/docs/faq/custom_repositories)
[![Validate](https://github.com/aalbretsen/kraftvakt/actions/workflows/validate.yml/badge.svg)](https://github.com/aalbretsen/kraftvakt/actions/workflows/validate.yml)
[![CI](https://github.com/aalbretsen/kraftvakt/actions/workflows/ci.yml/badge.svg)](https://github.com/aalbretsen/kraftvakt/actions/workflows/ci.yml)

Kraftvakt styrer hvilke effektkrevende apparater som får bruke strøm, i
prioritert rekkefølge. Eksempler er varmtvannsbereder, varmekabler og
elbillader. Den er rettet mot det norske strømmarkedet og holder forbruket
like under et valgt kWh-mål per time, slik at du unngår et dyrere trinn i
kapasitetsleddet i nettleien. Konfigureres fra et eget panel i sidemenyen.

> **Status:** Tidlig utvikling. Integrasjonen måler foreløpig bare effekten og
> viser snittene. Den styrer ingen apparater ennå.

## Krav

- Home Assistant 2026.10 eller nyere

## Installasjon

### HACS (anbefalt)

1. Åpne HACS → ⋮ → **Egendefinerte repositorier**.
2. Legg til `https://github.com/aalbretsen/kraftvakt` med kategori **Integrasjon**.
3. Installer **Kraftvakt** og start Home Assistant på nytt.

### Manuelt

Kopier `custom_components/kraftvakt` til `config/custom_components/` i
Home Assistant og start på nytt.

## Oppsett

1. Gå til **Innstillinger → Enheter og tjenester → Legg til integrasjon**.
2. Søk etter **Kraftvakt** og fullfør oppsettet.
3. Åpne **Kraftvakt** i sidemenyen for å sette effektmål og apparater.

## Entiteter

Alle entitetene hører til tjenesteenheten **Kraftvakt**.

| Entitet | Beskrivelse |
|---|---|
| `sensor.kraftvakt_regulation_average` (Reguleringssnitt) | Gjennomsnittlig effekt i kW over siste reguleringsvindu. Oppdateres hver gang et vindu lukkes. |
| `sensor.kraftvakt_average_consumption` (Snittforbruk) | Gjennomsnittlig effekt i kW over siste time, glidende. Oppdateres hver gang et reguleringsvindu lukkes. |

Entitets-ID-ene over gjelder når Home Assistant er satt opp på engelsk. Med
norsk språk får de norske navn, for eksempel `sensor.kraftvakt_reguleringssnitt`.

Effektsensoren kan oppgi effekt i W eller kW. En sensor uten enhet leses som W.
Snittsensorene er utilgjengelige til første reguleringsvindu er lukket, og når
effektsensoren har vært uten gyldig verdi da to vinduer på rad ble lukket.
Når effektsensoren gir en gyldig verdi igjen, brukes den verdien bakover i tid
i begge snittene.

## Utvikling

Krever Python 3.14, som Home Assistant 2026.3 og nyere bruker.

```bash
uv venv --python 3.14
uv pip install -r requirements_dev.txt
uv run pytest
uv run ruff check .
```

Panelet skal bygges med Node.js. Versjonen står i `.nvmrc`, og den samme
versjonen brukes av Home Assistant-frontenden. Installer og aktiver den med
[nvm](https://github.com/nvm-sh/nvm) eller
[nvm.fish](https://github.com/jorgebucaran/nvm.fish):

```bash
nvm install
```

```bash
nvm use
```

Kjør en lokal Home Assistant mot repoet:

```bash
ln -s ../custom_components config/custom_components
uv run hass -c config
```

### Logo og ikon

Kildene ligger i `assets/brand/`. PNG-filene i
`custom_components/kraftvakt/brand/` (lastes direkte av Home Assistant
fra 2026.3) bygges med:

```bash
uv run --with cairosvg --with pillow scripts/build_brand.py
```

## Lisens

[MIT](LICENSE)
