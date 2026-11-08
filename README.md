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

> **Status:** Første versjon under utprøving. Måling, regulering av apparater
> med varianter, elbillading, straff, sikker tilstand og panelet er på plass og
> testet automatisk og manuelt mot Home Assistant 2026.10.4, men Kraftvakt har
> ennå lite erfaring fra virkelig drift.

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
- **Sikker tilstand:** Har effektsensoren vært uten gyldig verdi da to
  reguleringsvinduer på rad ble lukket, slås alle apparater av til den kommer
  tilbake. Én manglende verdi tåles.

Effektsensoren kan oppgi effekt i W eller kW. En sensor uten enhet leses som W.

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
  Bil tilkoblet er påkrevd når bare én elbillader kan lade om gangen.
  Når billadestyring er av, beholdes elbilladerne, men de kan bare vises.

For handlingene kan du velge **Standard** når entitetens domene har en
standardhandling (for eksempel `switch.turn_on` og `switch.turn_off`), ellers
lager du en egendefinert handling med HAs handlingsredigerer, se eksemplene
lenger ned. Mislykkes en handling, skrives feilen til loggen, og reguleringen
fortsetter uten å prøve igjen. Entiteter som allerede brukes av et annet apparat
eller en elbillader, kan ikke velges.

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

- snittforbruket og reguleringssnittet mot effektgrensen, med tiden hvert snitt
  dekker, og forbruket nå, slik effektsensoren måler det,
- en ring som tømmes frem mot neste avgjørelse. Klokkeslettet vises når du
  holder musen over,
- om reguleringen er i sikker tilstand, og om en straffeperiode pågår, med
  gjenstående overforbruk,
- prioritetslisten med apparatene i prioritert rekkefølge, om de er på eller
  av, og gjeldende variant. Der «Elbillading» står i listen, står
  elbilladerne under hverandre i gjeldende ladeprioritering, med om de er
  aktivert, og om de er forbigått, ventende, utenfor regulering eller utenfor
  ladetidsrommet. Ladestrømmen vises som én prikk per ampere fra minste til
  største ladestrøm. Apparatet eller elbilladeren som står for tur, har én
  blokk per reguleringsvindu som er igjen til avgjørelsen der det slås på.

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

Snittsensorene er utilgjengelige til første reguleringsvindu er lukket, og når
effektsensoren har vært uten gyldig verdi da to vinduer på rad ble lukket.
Når effektsensoren gir en gyldig verdi igjen, brukes den verdien bakover i tid
i begge snittene.

Når Kraftvakt starter, hentes timen før fra historikken til effektsensoren i
Home Assistant (opptakeren, `recorder`), slik at snittforbruket stemmer også
rett etter en omstart. Tiden Home Assistant var nede, regnes med den siste
verdien før den stoppet. Uten historikk brukes første måling bakover i tid.

## Start og stopp

Reguleringen starter av seg selv når Home Assistant eller integrasjonen
starter, forutsatt at konfigurasjonen er fullstendig: effektsensor er valgt, og
hvert apparat har entitet og handlinger for å slå på og av. Når billadestyring
er aktivert, må hver elbillader i tillegg ha entitet, handlinger for å aktivere,
deaktivere og sette ladestrøm, og sensor for ladeeffekt. Kan bare én
elbillader lade om gangen, må hver elbillader også ha bil tilkoblet.

Ved hver start slås alle apparatene av og alle elbilladerne deaktiveres med en
gang. Deretter slår reguleringen dem på ett og ett i prioritert rekkefølge.
Første avgjørelse tas når et helt reguleringsintervall har gått etter starten.
Når Home Assistant starter, venter reguleringen til Home Assistant har startet
ferdig, slik at integrasjonene til apparatene er lastet før de slås av. Kan ikke
den lagrede konfigurasjonen (`.storage/kraftvakt.config`) leses, starter ikke
Kraftvakt. Integrasjonen viser da en feilmelding, og filen endres ikke.

Bryteren **Regulering** stopper og starter reguleringen. Når reguleringen
stoppes, slås alle apparatene av, og ingenting slås på før den startes igjen.
Er konfigurasjonen ikke fullstendig, blir bryteren stående av, og forsøket
skrives til loggen. Bryteren har ingen lagret stilling. Etter en omstart kjører
reguleringen igjen.

I sikker tilstand blir sensoren **Sikker tilstand** på. Når effektsensoren gir
en gyldig verdi igjen, starter reguleringen på nytt med alle apparater avslått.
Går snittforbruket over effektgrensen pluss straffeterskelen, holdes alle
apparater av til overforbruket er hentet inn, og så starter reguleringen på
nytt på samme måte.

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
  fortsette til den er ferdig. De andre venter. Da må bil tilkoblet være satt
  for hver elbillader. Uten den kan Kraftvakt bare se at en bil er koblet til
  ved å aktivere elbilladeren, og elbilladere uten bil ville blitt aktivert
  etter tur.
- Utenfor ladetidsrommet lader ikke elbilladeren. Ladetidsrommet kan gå over
  midnatt og gjelder i Home Assistants tidssone.
- Overstyringen av ladetidsrommet gjelder til neste ladetidsrom har startet
  etter at bryteren ble slått på, også om reguleringen har vært stoppet eller i
  sikker tilstand imens. Etter en omstart av Home Assistant regnes det fra
  første start av reguleringen.

Bryterne **‹lader› utenfor regulering** og **‹lader› overstyr ladetidsrom**
kan brukes mens reguleringen kjører, og endringen gjelder fra neste
avgjørelse. Stillingen lagres med en gang og beholdes over omstart. Mens
billadestyring er deaktivert, er bryterne utilgjengelige, men stillingen
beholdes.

## Eksempler på maler og handlinger

Maler skrives med Home Assistants malspråk (Jinja2), og handlinger er de samme
som i automasjoner og skript. I handlingsredigereren kan du bytte til YAML via
menyen ⋮ og lime inn eksemplene. Alle maler og handlinger får variablene
`entity_id` (apparatets eller elbilladerens entitet) og `entity` (tilstanden
til entiteten, for eksempel `entity.state` og `entity.attributes`). Byttes
entiteten ut, virker malene fortsatt. Handlingen for ladestrøm får i tillegg
variablene `current`, `min_current` og `max_current`. `current` ligger alltid
mellom minste og største ladestrøm.

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

Krever Python 3.14.2 eller nyere, som Home Assistant 2026.10.4 krever, og
[uv](https://docs.astral.sh/uv/). Utviklingsavhengighetene står i
`requirements_dev.txt`.

```bash
uv venv --python 3.14
uv pip install -r requirements_dev.txt
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Koden ligger i `custom_components/kraftvakt/`. Reguleringen er ren Python uten
Home Assistant i `regulation/`, og `runtime.py` kobler den til Home Assistant.
Testene ligger i `tests/`, med enhetstester i `tests/unit/`. Simulatoren
ligger i `simulator/`, og testene for den i `tests/simulator/` og
`tests/unit/simulator/`.

Instruksjoner til Claude Code står i `CLAUDE.md` og i skill-filene i
`.claude/skills/`. Der står også hvordan reguleringen skal virke, i detalj.

### Panelet

Panelet er skrevet i Lit og TypeScript og ligger i `frontend/`. Det bygges med
Node.js. Versjonen står i `.nvmrc`, og den samme versjonen brukes av Home
Assistant-frontenden. Installer og aktiver den med
[nvm](https://github.com/nvm-sh/nvm) eller
[nvm.fish](https://github.com/jorgebucaran/nvm.fish):

```bash
nvm install
```

```bash
nvm use
```

Den ferdige bundlen, `custom_components/kraftvakt/frontend/kraftvakt-panel.js`,
sjekkes inn, fordi HACS installerer rett fra repoet. Bygg den på nytt etter
hver endring i `frontend/`, og sjekk inn kilden og bundlen sammen. CI feiler
hvis den innsjekkede bundlen ikke stemmer med kilden.

```bash
cd frontend
npm ci
npm run typecheck
npm run build
```

`npm run watch` bygger på nytt ved hver endring. Bundlen lastes med versjonen
fra `manifest.json` i URL-en, så nettleseren kan bruke en gammel bundle etter
et nytt bygg. Last da siden på nytt uten hurtigbuffer. Tekstene i panelet ligger
i `frontend/src/translations/` (engelsk og norsk) og velges ut fra språket til
brukeren i Home Assistant.

### Lokal Home Assistant

Kjør en lokal Home Assistant mot repoet. `config/custom_components/` er en
vanlig mappe med én lenke til Kraftvakt og én til simulatoren:

```bash
mkdir -p config/custom_components
ln -s ../../custom_components/kraftvakt config/custom_components/kraftvakt
ln -s ../../simulator/custom_components/kraftvakt_simulator config/custom_components/kraftvakt_simulator
uv run hass -c config
```

### Simulator

Simulatoren gjør det mulig å teste Kraftvakt uten HAN-port og ekte apparater.
Den er en egen integrasjon, **Kraftvakt simulator**, i
`simulator/custom_components/kraftvakt_simulator/`. Den ligger utenfor
`custom_components/` og blir derfor ikke installert av HACS, og den brukes bare
med en lokal Home Assistant.

Legg til integrasjonen under **Innstillinger → Enheter og tjenester**, og legg
til én enhet om gangen med **Legg til enhet**:

- **HAN:** husets effekt (`sensor.han_effekt`, eller `sensor.han_power` på
  engelsk, når enheten heter «HAN»). Den er bakgrunnsforbruket pluss effekten
  til alle de simulerte enhetene. Bakgrunnsforbruket er en `number`-entitet som
  kan endres mens Home Assistant kjører. Det kan bare finnes én HAN.
- **Varmeapparat:** varmekabler, varmtvannsbereder eller panelovn, med effekt
  (W), driftsandel (0–100 %) og periode (minutter). Apparatet har en bryter og
  en effektsensor. Mens bryteren er på, varmer det i en fast syklus som starter
  med den avslåtte delen: 750 W, 25 % og 60 minutter gir 45 minutter av og 15
  minutter på, om igjen og om igjen. Syklusen starter på nytt hver gang
  bryteren slås på. Med bryteren av bruker apparatet ingenting. Varmeeffekt,
  driftsandel og periode er `number`-entiteter som kan endres mens Home
  Assistant kjører. Endres de mens bryteren er på, starter syklusen på nytt.
- **Elbillader:** trefaset 400 V med minste og største ladestrøm. Den har
  bryterne **Lading tillatt**, **Bil tilkoblet** og **Bil fulladet**,
  **Ladestrøm** (A) og sensoren **Ladeeffekt**. Laderen trekker
  √3 × 400 V × ladestrømmen (6 A gir 4,16 kW) når lading er tillatt, en bil er
  tilkoblet og bilen ikke er fulladet.

Varmeapparater og elbilladere har også bryteren **Frakoblet**. Mens den er på,
bruker enheten ingenting, uansett hva de andre bryterne står på. Slik styrer du
hvilke enheter som bruker strøm under en simulering. Syklusen til et
varmeapparat går videre mens det er frakoblet.

Det som styrer simuleringen og ikke hører til en ekte enhet, står under
**Konfigurasjon** på enhetssiden: **Bakgrunnsforbruk**, **Varmeeffekt**,
**Driftsandel**, **Periode**, **Bil tilkoblet**, **Bil fulladet** og
**Frakoblet**.

Innstillingene kan endres med **Konfigurer på nytt**. Bryterne og ladestrømmen
beholder stillingen over en omstart.

Sett så opp Kraftvakt mot simulatoren: HAN-ens effektsensor som effektsensor,
bryterne til varmeapparatene som apparater, og for hver elbillader:

| Felt i Kraftvakt | Verdi |
|---|---|
| Entitet | `switch.<lader>_lading_tillatt` |
| Aktiver og deaktiver | Standard |
| Sett ladestrøm | Egendefinert handling med `number.set_value` mot `number.<lader>_ladestrom` og `value: "{{ current }}"` |
| Sensor for ladeeffekt | `sensor.<lader>_ladeeffekt` |
| Bil tilkoblet | `switch.<lader>_bil_tilkoblet` |

Endre bakgrunnsforbruket og bryterne for bilen, og se reguleringen på
statussiden.

### WebSocket-API

Panelet snakker med integrasjonen over egne WebSocket-kommandoer. Alle krever
administrator.

| Kommando | Gjør |
|---|---|
| `kraftvakt/capabilities` | Gir standardhandlinger per felt, grenser og standardverdier. |
| `kraftvakt/config/get` | Gir konfigurasjonen, navnene på entitetene og hva som mangler. |
| `kraftvakt/config/save` | Lagrer hele konfigurasjonen. Avvises mens reguleringen kjører. Ugyldig konfigurasjon lagres ikke, og svaret gir feilene per felt. |
| `kraftvakt/regulation/set_running` | Starter eller stopper reguleringen, som bryteren **Regulering**. |
| `kraftvakt/status/subscribe` | Sender status straks og deretter for hvert reguleringsvindu, hver avgjørelse og ved start, stopp og lagring. |

Formatene for konfigurasjonen, feilene og statusen står i
`.claude/skills/kraftvakt-backend/SKILL.md`. En lagret konfigurasjon tas i bruk
neste gang reguleringen startes, uten at integrasjonen lastes på nytt.

### Logo og ikon

Kildene ligger i `assets/brand/`. PNG-filene i
`custom_components/kraftvakt/brand/` (lastes direkte av Home Assistant
fra 2026.3) bygges med:

```bash
uv run --with cairosvg --with pillow scripts/build_brand.py
```

## Lisens

[MIT](LICENSE)
