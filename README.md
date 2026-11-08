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
elbillader. Den er rettet mot det norske strømmarkedet og holder
snittforbruket siste time rett under en valgt effektgrense, slik at du unngår
et dyrere trinn i kapasitetsleddet i nettleien. Alt settes opp i et eget panel
i sidemenyen. Kraftvakt kjører helt lokalt, uten skytjenester.

> **Status:** Alle kravene i [kravspesifikasjonen](REQUIREMENTS.md) er
> implementert: måling, regulering av apparater med varianter, elbillading,
> straff, sikker tilstand og panelet. Kraftvakt er testet automatisk og manuelt
> mot Home Assistant 2026.10.4, men har ennå lite erfaring fra virkelig drift.

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
2. Søk etter **Kraftvakt** og fullfør oppsettet. Det er ingen innstillinger her.
3. Åpne **Kraftvakt** i sidemenyen, eller trykk på tannhjulet for integrasjonen,
   og sett opp effektsensor, effektgrense, apparater og eventuelt elbilladere.
4. Trykk **Lagre**, gå til **Status** og trykk **Start regulering**.

Effektsensoren er en sensor fra en annen integrasjon som måler husets totale
effekt, typisk fra HAN-porten på strømmåleren.

## Slik virker det

- **Effektgrense:** høyeste tillatte gjennomsnittseffekt, for eksempel 10 kW.
  Den tilsvarer trinnet i kapasitetsleddet du vil holde deg under.
- **Reguleringssnitt:** gjennomsnittet av effektsensoren over et kort
  reguleringsvindu, standard 60 sekunder. Det styrer reguleringen.
- **Snittforbruk:** glidende gjennomsnitt over siste time. Det er dette
  nettselskapet måler, og det som skal holdes under effektgrensen.
- **Avgjørelser:** Ved hvert reguleringsintervall avgjør reguleringen om et
  apparat skal slås på eller av. Er reguleringssnittet over effektgrensen,
  slås det lavest prioriterte apparatet som er på, av. Er det ledig effekt,
  slås det neste apparatet i prioritetslisten på, ett om gangen og etter en
  ventetid. Ventetiden er kortere jo lavere reguleringssnittet er, og den øker
  når det samme apparatet slås av og på gang på gang.
- **Effektreserve:** valgfri ledig effekt som må finnes før et apparat slås på,
  for eksempel 4 kW for en bassengvarmer som trekker mye straks den slås på.
- **Varianter:** Et apparat kan ha varianter med en annen plass i
  prioritetslisten, for eksempel høyere prioritet om morgenen.
- **Straff:** Går snittforbruket over effektgrensen pluss straffeterskelen,
  slås alle apparater av til overforbruket er hentet inn. Straffen er en
  sikkerhetsventil og skal normalt aldri inntre.
- **Sikker tilstand:** Mangler effektsensoren gyldig verdi, slås alle
  apparater av til den kommer tilbake.

Kraftvakt vet ikke hva et apparat faktisk bruker, og leser ikke om det står på.
Den regner med at apparatene står slik Kraftvakt sist bestemte. Ikke slå
regulerte apparater av eller på utenom Kraftvakt, for det kan forstyrre
reguleringen, gå ut over apparater med høyere prioritet og utløse straff.
Unntaket er elbilladere, der Kraftvakt leser ladeeffekt og om en bil er
tilkoblet.

## Konfigurasjon i panelet

Panelet har en meny øverst med statussiden og tre konfigurasjonssider. Bare
administratorer har tilgang.

- **Generelt:** effektsensor, effektgrense, reguleringsvindu,
  reguleringsintervall, ventetid ved effektgrensen og straffeterskel.
  Hjelpeteksten under hvert felt viser gyldig område og standardverdi.
- **Apparater:** prioritetslisten, med det viktigste apparatet øverst. Dra i
  håndtaket for å endre rekkefølgen. **Legg til apparat** og blyanten åpner en
  dialog med entitet, handlinger for å slå på og av, valgfri effektreserve og
  varianter. En variant har en merkelapp og et uttrykk, enten en boolsk entitet
  eller en mal. Varianten står som en egen oppføring i prioritetslisten, og det
  øverste sanne uttrykket gjelder. Under malen vises hva den gir nå.
  Når billadestyring er på, står **Elbillading** i listen og kan flyttes som et
  apparat.
- **Billading:** billadestyring av og på, én elbillader om gangen, og
  elbilladerne i ladeprioritering. Dialogen for en elbillader har entitet,
  handlinger for å aktivere, deaktivere og sette ladestrøm, minste og største
  ladestrøm, sensor for ladeeffekt, effektreserve, bil tilkoblet og ladetidsrom.
  Når billadestyring er av, beholdes elbilladerne, men de kan bare vises.

For handlingene kan du velge **Standard** når entitetens domene har en
standardhandling, ellers lager du en egendefinert handling med HAs
handlingsredigerer. Entiteter som allerede brukes av et annet apparat eller en
elbillader, kan ikke velges.

Endringene samles i et utkast. **Lagre** lagrer alt på én gang, og **Forkast**
går tilbake til det som er lagret. Feil vises ved feltet, og panelet lagrer
ikke før de er rettet. Panelet spør før ulagrede endringer forkastes.

Konfigurasjonen kan bare endres mens reguleringen er stoppet. Mens den kjører,
er konfigurasjonssidene låst og viser knappen **Stopp regulering**. En lagret
konfigurasjon tas i bruk neste gang reguleringen startes.

## Statussiden

Statussiden viser om reguleringen kjører, og har knappen for å starte og stoppe
den. Er konfigurasjonen ikke fullstendig, står det hva som mangler, med lenke
til siden der det rettes. Mens reguleringen kjører, viser den i tillegg:

- reguleringssnittet og snittforbruket mot effektgrensen, og tid til neste
  avgjørelse,
- om reguleringen er i sikker tilstand, og om en straffeperiode pågår, med
  gjenstående overforbruk,
- apparatene i prioritert rekkefølge, om de er på eller av, gjeldende variant
  og hvor lenge apparatet som står for tur, venter,
- elbilladerne i gjeldende ladeprioritering, om de er aktivert, ladestrømmen,
  og om de er forbigått, ventende, utenfor regulering eller utenfor
  ladetidsrommet.

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

## Eksempler på maler og handlinger

Maler skrives med Home Assistants malspråk (Jinja2), og handlinger er de samme
som i automasjoner og skript. I handlingsredigereren kan du bytte til YAML via
menyen ⋮ og lime inn eksemplene. Alle maler og handlinger får variablene
`entity_id` (apparatets eller elbilladerens entitet) og `entity` (tilstanden
til entiteten, for eksempel `entity.state` og `entity.attributes`). Byttes
entiteten ut, virker malene fortsatt.

En mal er sann bare når den gir den boolske verdien sann. Alt annet, også en
feil i malen, regnes som usann. En entitet er sann bare når den er `on`.

**Variant «Morgen»** som gir varmtvannsberederen høyere prioritet mellom
klokken 05 og 08:

```jinja
{{ 5 <= now().hour < 8 }}
```

**Variant «Kaldt»** for en varmepumpe når det er under 18 grader inne. `entity`
er apparatets egen entitet:

```jinja
{{ entity.attributes.current_temperature | float(99) < 18 }}
```

**Bil tilkoblet** ut fra statussensoren til laderen:

```jinja
{{ states('sensor.lader_garasje_status') in ['connected', 'charging', 'awaiting_start'] }}
```

**Slå på** et apparat ved å sette en temperatur i stedet for å slå det på:

```yaml
- action: climate.set_temperature
  target:
    entity_id: "{{ entity_id }}"
  data:
    temperature: 22
```

**Slå av** det samme apparatet ved å sette det til frostsikring:

```yaml
- action: climate.set_temperature
  target:
    entity_id: "{{ entity_id }}"
  data:
    temperature: 8
```

**Sett ladestrøm** når laderen har en egen `number`-entitet for ladestrøm:

```yaml
- action: number.set_value
  target:
    entity_id: number.lader_garasje_ladestrom
  data:
    value: "{{ current }}"
```

**Sett ladestrøm** med en tjeneste fra laderens integrasjon, som tar
strømmen per fase:

```yaml
- action: min_lader.set_current
  data:
    charger_id: garasje
    phase1: "{{ current }}"
    phase2: "{{ current }}"
    phase3: "{{ current }}"
```

`min_lader.set_current` er et eksempel. Bruk tjenesten og feltene laderens
integrasjon har.

## Utvikling

Krever Python 3.14.2 eller nyere, som Home Assistant 2026.10.4 krever.

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

### Panelet

Panelet er skrevet i Lit og TypeScript og ligger i `frontend/`. Den ferdige
bundlen, `custom_components/kraftvakt/frontend/kraftvakt-panel.js`, sjekkes
inn, fordi HACS installerer rett fra repoet. Bygg den på nytt etter hver
endring i `frontend/`, og sjekk inn kilden og bundlen sammen. CI feiler hvis
den innsjekkede bundlen ikke stemmer med kilden.

```bash
cd frontend
npm ci
npm run typecheck
npm run build
```

`npm run watch` bygger på nytt ved hver endring. Bundlen lastes med versjonen
fra `manifest.json` i URL-en, så nettleseren kan bruke en gammel bundle etter
et nytt bygg. Last da siden på nytt uten hurtigbuffer. Tekstene i panelet ligger i
`frontend/src/translations/` (engelsk og norsk) og velges ut fra språket til
brukeren i Home Assistant.

Kjør en lokal Home Assistant mot repoet:

```bash
ln -s ../custom_components config/custom_components
uv run hass -c config
```

For å teste uten HAN-port kan effektsensoren simuleres med en `input_number`
og en mal-sensor i `config/configuration.yaml`. Bruk `input_boolean` som
apparater, og endre effekten for å se reguleringen slå apparatene av og på:

```yaml
input_number:
  husets_effekt:
    name: Husets effekt
    min: 0
    max: 20000
    step: 100
    unit_of_measurement: W
    mode: box

input_boolean:
  varmtvannsbereder:
    name: Varmtvannsbereder

template:
  - sensor:
      - name: HAN effekt
        unit_of_measurement: W
        device_class: power
        state_class: measurement
        state: "{{ states('input_number.husets_effekt') }}"
```

### WebSocket-API

Panelet snakker med integrasjonen over egne WebSocket-kommandoer. Alle krever
administrator.

| Kommando | Gjør |
|---|---|
| `kraftvakt/capabilities` | Gir standardhandlinger per felt, grenser og standardverdier. |
| `kraftvakt/config/get` | Gir konfigurasjonen, navnene på entitetene og hva som mangler. |
| `kraftvakt/config/save` | Lagrer hele konfigurasjonen. Avvises mens reguleringen kjører. Ugyldig konfigurasjon lagres ikke, og svaret gir feilene per felt. |
| `kraftvakt/regulation/set_running` | Starter eller stopper reguleringen, som bryteren **Regulering**. |
| `kraftvakt/status/subscribe` | Sender status straks og deretter for hvert reguleringsvindu, hver avgjørelse og ved start og stopp. |

Formatene står i kapittel 3.8 i `IMPLEMENTATION.md`. En lagret konfigurasjon
tas i bruk neste gang reguleringen startes, uten at integrasjonen lastes på
nytt.

### Logo og ikon

Kildene ligger i `assets/brand/`. PNG-filene i
`custom_components/kraftvakt/brand/` (lastes direkte av Home Assistant
fra 2026.3) bygges med:

```bash
uv run --with cairosvg --with pillow scripts/build_brand.py
```

## Lisens

[MIT](LICENSE)
