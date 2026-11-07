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

> **Status:** Tidlig utvikling. Integrasjonen måler effekten og regulerer
> vanlige apparater og elbilladere, med straff og sikker tilstand. Panelet for
> konfigurasjon mangler ennå, så konfigurasjonen kan foreløpig ikke settes opp
> fra brukergrensesnittet.

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
| `switch.kraftvakt_regulation` (Regulering) | Er på mens reguleringen kjører. Slå av for å stoppe reguleringen og på for å starte den igjen. |
| `binary_sensor.kraftvakt_safe_state` (Sikker tilstand) | Er på mens reguleringen er i sikker tilstand fordi effektsensoren mangler gyldig verdi. Kan brukes som utløser i automasjoner for å varsle. |
| `switch.kraftvakt_<lader>_excluded_from_regulation` (‹lader› utenfor regulering) | Én per elbillader. Slå på for å ta elbilladeren ut av reguleringen. Da lader bilen aldri. |
| `switch.kraftvakt_<lader>_override_charging_window` (‹lader› overstyr ladetidsrom) | Én per elbillader. Slå på for å la elbilladeren lade utenfor ladetidsrommet. Slås av av seg selv når neste ladetidsrom har startet. |

Entitets-ID-ene over gjelder når Home Assistant er satt opp på engelsk. Med
norsk språk får de norske navn, for eksempel `sensor.kraftvakt_reguleringssnitt`
og `switch.kraftvakt_regulering`.

Effektsensoren kan oppgi effekt i W eller kW. En sensor uten enhet leses som W.
Snittsensorene er utilgjengelige til første reguleringsvindu er lukket, og når
effektsensoren har vært uten gyldig verdi da to vinduer på rad ble lukket.
Når effektsensoren gir en gyldig verdi igjen, brukes den verdien bakover i tid
i begge snittene.

## Start og stopp

Reguleringen starter av seg selv når Home Assistant eller integrasjonen
starter, forutsatt at konfigurasjonen er fullstendig: effektsensor er valgt, og
hvert apparat har entitet og handlinger for å slå på og av. Når billadestyring
er aktivert, må hver elbillader i tillegg ha entitet, handlinger for å aktivere,
deaktivere og sette ladestrøm, og sensor for ladeeffekt. Ved hver start slås
alle apparatene av og alle elbilladerne deaktiveres med en gang. Deretter slår
reguleringen dem på ett og ett i prioritert rekkefølge. Første avgjørelse tas
når et helt reguleringsintervall har gått etter starten.

Bryteren **Regulering** stopper og starter reguleringen. Når reguleringen
stoppes, slås alle apparatene av, og ingenting slås på før den startes igjen.
Er konfigurasjonen ikke fullstendig, blir bryteren stående av, og forsøket
skrives til loggen. Bryteren har ingen lagret stilling. Etter en omstart kjører
reguleringen igjen.

Har effektsensoren vært uten gyldig verdi da to reguleringsvinduer på rad ble
lukket, går reguleringen i sikker tilstand. Da slås alle apparatene av, og
sensoren **Sikker tilstand** blir på. Når effektsensoren gir en gyldig verdi
igjen, starter reguleringen på nytt med alle apparater avslått.

Handlingene for apparatene kan være standardhandlingen for entitetens domene
(for eksempel `switch.turn_on` og `switch.turn_off`) eller egendefinerte
handlinger. Egendefinerte handlinger og maler får variablene `entity_id` og
`entity` (tilstanden til apparatets entitet). Mislykkes en handling, skrives
feilen til loggen, og reguleringen fortsetter uten å prøve igjen.

## Elbillading

Når billadestyring er aktivert, styrer Kraftvakt ladestrømmen til hver
elbillader trinnvis, ett ampere om gangen, etter hvor mye effekt som er ledig.
Plasseringen av «Elbillading» i prioritetslisten bestemmer hvor i rekkefølgen
elbilladerne ligger. En elbillader lader bare når Kraftvakt har aktivert den,
så en bil som kobles til, begynner ikke å lade av seg selv. Før elbilladeren
aktiveres eller deaktiveres, settes ladestrømmen til minste ladestrøm.

- Ladeeffekten leses ved hver avgjørelse. Over 100 W regnes elbilladeren som
  aktivt ladende. Er sensoren utilgjengelig, regnes den også som ladende.
- En elbillader som ikke trekker strøm, fordi bilen ikke er tilkoblet eller
  ikke lader to reguleringsvinduer etter at den ble aktivert, blir forbigått.
  Den begrenses til minste ladestrøm, beholdes aktivert og står ikke i veien
  for andre elbilladere.
- Kan bare én elbillader lade om gangen, får en elbillader som lader aktivt,
  fortsette til den er ferdig. De andre venter.
- Utenfor ladetidsrommet lader ikke elbilladeren. Ladetidsrommet kan gå over
  midnatt og gjelder i Home Assistants tidssone.

Bryterne **‹lader› utenfor regulering** og **‹lader› overstyr ladetidsrom**
kan brukes mens reguleringen kjører, og endringen gjelder fra neste
avgjørelse. Stillingen lagres med en gang og beholdes over omstart. Mens
billadestyring er deaktivert, er bryterne utilgjengelige, men stillingen
beholdes.

Handlingen for ladestrøm får i tillegg variablene `current`, `min_current` og
`max_current`. `current` ligger alltid mellom minste og største ladestrøm.

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
