# Kraftvakt – Implementasjonsplan for første versjon

Planen beskriver *hvordan* kravene i [REQUIREMENTS.md](REQUIREMENTS.md) skal
implementeres. Den brukes som arbeidsgrunnlag i senere sesjoner: hver sesjon
tar neste fase i kapittel 7, følger reglene i `CLAUDE.md` og krysser av
oppgavene i planen når de er ferdige.

GUI-skissene ligger i [skisser/](skisser/index.html).

Innhold:

1. Beslutninger
2. Avklarte tolkninger
3. Arkitektur
4. Reguleringen steg for steg
5. Frontend
6. Teststrategi
7. Faser
8. Sporbarhet
9. Risikoer og tekniske avklaringer
10. Forslag til endringer i REQUIREMENTS.md og annen dokumentasjon

---

## 1. Beslutninger

Beslutninger som er tatt, med begrunnelse. Endres en beslutning, oppdateres
planen først.

| # | Beslutning | Begrunnelse |
|---|---|---|
| B1 | Panelet skrives i **Lit + TypeScript** med byggesteg (Rollup). Kilden ligger i `frontend/` i rot, og ferdig bundle sjekkes inn som `custom_components/kraftvakt/frontend/kraftvakt-panel.js`. | Avklart med eier. Vanlig for HA-paneler. HACS installerer rett fra repoet, så bundlen må ligge der. |
| B2 | Panelet bruker Home Assistants egne komponenter (`ha-form`, `ha-selector`, `ha-entity-picker`, `ha-sortable`, `ha-dialog`, `ha-switch` m.fl.) i stedet for egne. | Ser ut og oppfører seg som resten av HA, og gir gratis velgere for entitet, mal og handling. |
| B3 | Konfigurasjonen lagres i en egen `homeassistant.helpers.storage.Store` (`.storage/kraftvakt.config`), ikke i `config_entry.options`. Config entry-en forblir tom. | Konfigurasjonen er en nøstet struktur som endres fra panelet. Bryterne for elbilladerne (ENT-003, ENT-004) skrives ofte, og en endring av `options` utløser update listener og reload. Store skrives atomisk, så GEN-011 oppfylles. |
| B4 | Reguleringslogikken er en ren Python-pakke (`regulation/`) uten avhengighet til Home Assistant. Den tar inn et øyeblikksbilde av målinger og innstillinger og returnerer en liste med kommandoer. | Gjør den komplekse logikken testbar med enhetstester (CLAUDE.md), og skiller *hva* som skal skje fra *hvordan* det utføres. |
| B5 | Tid injiseres (klokke-funksjon) i måling og regulering. | Deterministiske tester, også med `freezer`/`async_fire_time_changed` i HA-testene. |
| B6 | Panelet snakker med backend over egne WebSocket-kommandoer (`kraftvakt/...`), alle med `require_admin`. | GUI-001 krever at panelet bare er for administratorer. WebSocket er standard for HA-paneler. |
| B7 | Konfigurasjonssidene redigerer et lokalt utkast og lagrer hele konfigurasjonen samlet med en «Lagre»-knapp. Dialogene for apparat og elbillader oppdaterer utkastet. | Én atomisk lagring med validering i backend. Ingen halvferdige tilstander i lagret konfigurasjon. |
| B8 | Panelets tekster ligger i egne oversettelsesfiler i frontend (`frontend/src/translations/en.json` og `nb.json`) og velges ut fra `hass.language`. Entitetsnavn oversettes på vanlig måte i `strings.json`/`translations/`. | HA har ingen oversettelseskategori for egne paneler. SPR-001/002. |
| B9 | Elbilladerens entiteter (ENT-003, ENT-004) legges til og fjernes dynamisk når konfigurasjonen lagres, uten reload av config entry. | En reload ville startet reguleringen av seg selv (REG-016), selv om brukeren nettopp stoppet den for å endre konfigurasjonen. |
| B10 | Alle maler og handlinger kjøres med `homeassistant.helpers.script.Script` og `Template`, med variablene i 3.6. | Standard HA-mekanisme, samme syntaks som i automasjoner. |

---

## 2. Avklarte tolkninger

Kravene er tolket slik nedenfor der de ikke var entydige. Tolkningene er
avklart med eier 2026-11-07. Der tolkningen bør inn i kravene, står det et
forslag i kapittel 10.

| # | Krav | Spørsmål | Avklart tolkning |
|---|---|---|---|
| T1 | REG-002, REG-009, MAL-001 | Snittene beregnes fortløpende også mens reguleringen er stoppet, så vinduene har sin egen takt. Hvordan henger «første avgjørelse etter ett helt reguleringsintervall» sammen med vinduene? | Vinduene beholder sin takt. En avgjørelse tas når det N-te reguleringssnittet *hvis vindu startet etter starten av reguleringen* er beregnet (N = 1x–4x). Første avgjørelse kommer dermed etter mellom N og N+1 vinduer. Snitt som delvis ligger før starten, telles ikke. |
| T2 | MAL-005, MAL-006, REG-011 | Hva skjer ved oppstart før effektsensoren har gitt første gyldige verdi (vanlig når HAN-sensoren kommer via MQTT)? | Det finnes ingen «siste gyldige verdi». Vinduer uten noen måling regnes som uten gyldig måleverdi. Sensorene for snitt er utilgjengelige. Etter to slike vinduer går reguleringen i sikker tilstand (ENT-005 blir sann), og når første gyldige verdi kommer, fylles vinduene etter MAL-005 og reguleringen starter etter REG-011. Reguleringen slår ikke på noe før det finnes et reguleringssnitt. |
| T3 | MAL-006 | Er «uten gyldig måleverdi når et nytt reguleringssnitt skal beregnes» tilstanden i det øyeblikket vinduet lukkes, eller hele vinduet? | Tilstanden i det øyeblikket vinduet lukkes. Tidsrom uten gyldig verdi inne i vinduet fylles med siste gyldige verdi uansett. |
| T4 | STR-004, STR-005, STR-009 | Overforbruket telles «fra tilstanden startet». Ved avgjørelsen der tilstanden starter, er overforbruket da 0, og STR-009 hindrer straff. | Overforbrukstilstanden starter med overforbruk 0 ved avgjørelsen D0. Reguleringssnitt beregnet etter D0 telles. Tilstanden kan tidligst avsluttes ved avgjørelsen etter D0. Med straffeterskel 0 starter straff dermed tidligst ved avgjørelsen etter D0. |
| T5 | STR-007 | Når innhentingen har startet under en straffeperiode, og reguleringssnittet igjen går over effektgrensen: stopper innhentingen igjen? | Nei. Innhentingen starter første gang et reguleringssnitt i straffeperioden er under effektgrensen, og fortsetter deretter netto (pluss over, minus under) til straffen er over. |
| T6 | REG-015, LAD-014 | Er ventetiden ved vedvarende pendling fast (5, 7, 9 …) eller lineær etter REG-013? Teller tvungne utkoblinger (straff, LAD-024, APP-009 osv.) som at «et annet apparat er slått av»? | Fast og uavhengig av reguleringssnittet, etter formelen i 4.4 (5, 7, 9 … med standardverdiene). Den lineære ventetiden gjelder første gang apparatet slås på igjen. Alle av/på-kommandoer reguleringen sender for et annet apparat, også tvungne, nullstiller telleren. |
| T7 | LAD-008, LAD-021, LAD-023 | Kan en *deaktivert* elbillader regnes som aktivt ladende fordi ladeeffekten er ugyldig (GEN-010)? | Ja. Ordlyden følges: enhver elbillader med ladeeffekt over 100 W eller ugyldig ladeeffekt regnes som aktivt ladende, også når den er deaktivert. Konsekvensene står i 4.3. |
| T8 | REG-001, REG-014, STR-002, APP-004, LAD-009 | Oppløsning på innstillingene. | Effektgrense, straffeterskel og effektreserver: kW med to desimaler (0,01). Reguleringsvindu: hele sekunder. Ventetid ved effektgrensen: hele minutter. Effektreserve for apparat: ≥ 0, ingen øvre grense. |
| T9 | GEN-013 | Kan samme entitet brukes for både et apparat og en elbillader? | Nei. En entitet kan bare brukes én gang i hele konfigurasjonen. |
| T10 | LAD-001, ENT-003, ENT-004 | Hva skjer med elbilladerne og entitetene deres når billadestyring deaktiveres? | Elbilladerne beholdes i konfigurasjonen, men regnes ikke med i reguleringen eller i kravet til fullstendig konfigurasjon. Entitetene for ENT-003/ENT-004 blir stående, men er utilgjengelige mens billadestyring er deaktivert. Stillingen deres beholdes i lagringen. |
| T11 | GUI-006 | Skal statussiden vise mer enn minimumskravet? | Ja, alt som ble foreslått i skissene: detaljer for elbilladere (ladestrøm, forbigått, ventende, utenfor ladetidsrom), ventetid for apparatet som står for tur, gjenstående overforbruk og om innhentingen har startet under straff, søyle med snittene mot effektgrensen og tid til neste avgjørelse. |
| T12 | GUI-012 | Skal den låste konfigurasjonssiden ha en snarvei for å stoppe reguleringen? | Ja, en knapp «Stopp regulering» i låsebanneret. |
| T13 | LAD-027 | Hvilket tidspunkt regnes «neste ladetidsrom» fra? | Fra tidspunktet bryteren for overstyring (ENT-004) ble slått på, eller fra siste start av reguleringen hvis den er senere. Bryteren registrerer tidspunktet. Overstyringen opphører ved første avgjørelse der et ladetidsrom har startet etter dette tidspunktet. Selve vurderingen skjer fortsatt ved avgjørelsene (REG-005). Etter omstart av HA eller integrasjonen er tidspunktet ukjent, og starten av reguleringen brukes (LAD-027). |
| T14 | GEN-013 | Hvilke variabler er tilgjengelige i maler og handlinger? | `entity_id` og `entity` (entitetens tilstandsobjekt, med f.eks. `entity.state` og `entity.attributes`) i alle maler og handlinger. I tillegg `current`, `min_current` og `max_current` i handlingen for ladestrøm (LAD-006). |
| T15 | GEN-013, T9 | Hvilke felt gjelder kravet om unike entiteter? | Bare entiteten som identifiserer et apparat eller en elbillader (`entity_id`). Effektsensor, sensorer for ladeeffekt, betingelser og handlinger kan bruke samme entitet flere steder. Avklart 2026-11-07. |
| T16 | LAD-007 | Nedre grense og standardverdier for ladestrøm? | Hele ampere, minste ≥ 1 A og minste ≤ største. Standard er 6 A og 16 A, så feltene kan ikke mangle. Avklart 2026-11-07. |
| T17 | APP-001, APP-005, APP-008 | Hva skjer med overflødige oppføringer i prioritetslisten? | Manglende oppføringer legges nederst. Duplikater, oppføringer for apparater eller varianter som ikke finnes, og `ev_charging` mens billadestyring er deaktivert, avvises som ugyldig konfigurasjon. Panelet fjerner dem selv. Avklart 2026-11-07. |
| T18 | GEN-013 | Hvor grundig valideres handlinger og maler? | Egendefinerte handlinger valideres med HAs skjema for skript, og maler sjekkes for syntaksfeil, i fase 1. Om «Standard» finnes for entitetens domene, valideres i fase 5, der tabellen i `actions.py` ligger. Avklart 2026-11-07. |
| T19 | MAL-007 | Hva gjelder når effektsensoren mangler enhet eller oppgir en annen effektenhet enn W og kW? | W og kW regnes om. En sensor uten enhet leses som watt. Alle andre enheter gir ugyldig måleverdi. Avklart 2026-11-07. |
| T20 | MAL-001, T1 | Hvor er takten til reguleringsvinduene forankret? | Første vindu starter når integrasjonen starter, og hvert vindu slutter ett reguleringsvindu etter forrige, planlagt mot absolutte tidspunkter (R4). Alle vinduer er hele vinduer. Avklart 2026-11-07. |
| T21 | MAL-005, MAL-006, REG-011 | Hva viser snittsensorene mens effektsensoren er borte over lengre tid, også når reguleringen er stoppet og ingen sikker tilstand kan inntre? | Målingen forkaster historikken når effektsensoren var uten gyldig måleverdi da to vinduer på rad ble lukket, uansett om reguleringen kjører. Snittsensorene er da utilgjengelige til en gyldig verdi kommer, og den fylles bakover etter MAL-005. Sikker tilstand (fase 5) bruker samme vilkår. Avklart 2026-11-07. |

---

## 3. Arkitektur

### 3.1 Oversikt

```
                 ┌────────────── Home Assistant ───────────────┐
 effektsensor ──▶│ runtime.py (KraftvaktRuntime)               │
 ladeeffekt   ──▶│   ├─ measurement.py   (snitt, MAL)          │
 bil tilkoblet ─▶│   ├─ conditions.py    (GEN-009)             │
                 │   ├─ regulation/      (ren logikk, REG/STR/  │
                 │   │                    APP/LAD)             │
                 │   └─ actions.py       (utfører kommandoer)  │──▶ apparater
                 │                                             │──▶ elbilladere
 panel (Lit) ◀──▶│ websocket_api.py                            │
                 │ storage.py ◀─▶ config_model.py              │
 entiteter   ◀──▶│ sensor.py · binary_sensor.py · switch.py    │
                 └─────────────────────────────────────────────┘
```

Flyt for hvert reguleringsvindu:

1. `measurement.py` lukker vinduet og gir et reguleringssnitt, et
   snittforbruk og om sensoren hadde gyldig verdi.
2. Sensorene ENT-001 og ENT-002 oppdateres.
3. Er det tid for en avgjørelse (T1), lager `runtime.py` et øyeblikksbilde
   (`DecisionInput`) med snittene, ladeeffekt, bil tilkoblet, varianter,
   brytere og klokkeslett, og kaller `RegulationEngine.decide()`.
4. Motoren returnerer en ordnet liste kommandoer. `actions.py` utfører dem i
   rekkefølge. Feil logges, og reguleringen fortsetter (GEN-012).
5. Statusen sendes til panelet og entitetene.

### 3.2 Mappestruktur

```
custom_components/kraftvakt/
  __init__.py            oppsett, panelregistrering, plattformer
  const.py
  config_flow.py         tom flyt (GUI-004)
  config_model.py        dataklasser, (de)serialisering, validering, fullstendighet
  storage.py             Store med versjon og migrering
  measurement.py         PowerAverager: reguleringssnitt og snittforbruk
  conditions.py          sann/usann fra entitet eller mal (GEN-009/010)
  actions.py             standardhandlinger og egendefinerte handlinger
  runtime.py             KraftvaktRuntime: timere, start/stopp, status
  websocket_api.py
  sensor.py              ENT-001, ENT-002
  binary_sensor.py       ENT-005
  switch.py              ENT-003, ENT-004, ENT-006
  regulation/
    __init__.py
    model.py             DecisionInput, Command, Slot og tilstand
    priority.py          bygger rekkefølgen av plasser (apparater + fiktive)
    waiting.py           lineær ventetid og økende ventetid
    penalty.py           overforbrukstilstand og straff
    charging.py          elbilladerregler
    engine.py            RegulationEngine: setter sammen en avgjørelse
  frontend/
    kraftvakt-panel.js   bygget bundle (sjekkes inn)
  strings.json, translations/en.json, translations/nb.json
frontend/                kilde for panelet (B1)
  package.json, tsconfig.json, rollup.config.mjs
  src/...
tests/
  unit/                  enhetstester av regulation/, measurement, config_model
  ...                    black box-tester med HA test harness
skisser/                 GUI-skisser
```

### 3.3 Moduler og ansvar

| Modul | Ansvar | Krav |
|---|---|---|
| `config_model.py` | Dataklasser for konfigurasjonen, standardverdier, gyldige områder, validering, unike entiteter og merkelapper, og `missing_items()` som sier hva som mangler for at konfigurasjonen er fullstendig. | GEN-011, GEN-013, REG-001, REG-002, REG-014, REG-016, MAL-002, STR-002, APP-001–008, LAD-001–010, LAD-025 |
| `storage.py` | Laster og lagrer konfigurasjonen og bryterstillingene. Versjonert for senere migrering. | GEN-011, ENT-003, ENT-004 |
| `measurement.py` | Tidsvektet integrasjon av effekten (stykkevis konstant: siste verdi gjelder til neste). Lukker vinduer, holder glidende timesvindu, enhetsomregning W/kW, negative verdier til 0, fylling ved oppstart og etter sikker tilstand. | MAL-001, MAL-003–007 |
| `conditions.py` | Evaluerer en betingelse `{type: entity|template, value}` til sann/usann etter GEN-009, med `entity_id` og `entity` som variabler (T14). | GEN-009, GEN-010, APP-006, LAD-010 |
| `actions.py` | Utfører kommandoer fra motoren. Tabell over standardhandlinger per domene. Kjører egendefinerte handlinger med variabler. Logger feil uten å gjenta. | GEN-012, GEN-013, APP-002, APP-003, LAD-004–006 |
| `regulation/` | All logikk for avgjørelsene. Ingen HA-import. | REG, STR, APP-007, APP-009, LAD-011–030 |
| `runtime.py` | Lytter på effektsensoren, styrer vindustimeren, teller avgjørelser (T1), leser ladeeffekt og betingelser ved avgjørelsen, kaller motoren, utfører kommandoer, start/stopp, sikker tilstand og status til panel og entiteter. | GEN-007, REG-005, REG-009, REG-011, REG-016 |
| `websocket_api.py` | Kommandoene i 3.8. | REG-010, GUI-* |
| plattformene | Entitetene i 3.7. | ENT-001–006 |

### 3.4 Datamodell for konfigurasjonen

Lagret som JSON i Store. ID-er er korte UUID-er som genereres i panelet eller
backend, slik at apparater og varianter kan gis nytt navn eller ny entitet uten
å miste plassen i listen.

```json
{
  "general": {
    "power_sensor": "sensor.han_power",
    "power_limit_kw": 10.0,
    "regulation_window_s": 60,
    "regulation_interval": 1,
    "wait_at_limit_min": 5,
    "penalty_threshold_kw": 1.0
  },
  "appliances": [
    {
      "id": "a1",
      "entity_id": "switch.varmtvannsbereder",
      "turn_on": { "mode": "default" },
      "turn_off": { "mode": "custom", "action": [ { "action": "switch.turn_off", "target": { "entity_id": "{{ entity_id }}" } } ] },
      "power_reserve_kw": null,
      "variants": [
        { "id": "v1", "label": "Morgen", "condition": { "type": "template", "value": "{{ 5 <= now().hour < 8 }}" } }
      ]
    }
  ],
  "priority": [
    { "type": "appliance", "appliance_id": "a1", "variant_id": "v1" },
    { "type": "ev_charging" },
    { "type": "appliance", "appliance_id": "a1", "variant_id": null }
  ],
  "charging": {
    "enabled": false,
    "one_at_a_time": true,
    "chargers": [
      {
        "id": "c1",
        "entity_id": "switch.lader_garasje",
        "activate": { "mode": "default" },
        "deactivate": { "mode": "default" },
        "set_current": { "mode": "custom", "action": [ { "action": "number.set_value", "target": { "entity_id": "number.lader_garasje_strom" }, "data": { "value": "{{ current }}" } } ] },
        "min_current_a": 6,
        "max_current_a": 16,
        "charge_power_sensor": "sensor.lader_garasje_effekt",
        "power_reserve_kw": 4.0,
        "car_connected": { "type": "entity", "value": "binary_sensor.lader_garasje_bil" },
        "charging_window": { "start": "22:00", "end": "06:00" }
      }
    ]
  },
  "charger_switches": {
    "c1": { "excluded": false, "window_override": false }
  }
}
```

Regler som valideres i `config_model.py`:

- Prioritetslisten har nøyaktig én oppføring for hvert apparat og hver variant,
  og `ev_charging` nøyaktig én gang når billadestyring er aktivert (APP-001,
  APP-005, APP-008). Mangler oppføringer, legges de nederst (APP-008).
  Overflødige oppføringer avvises (T17).
- Merkelapper er ikke tomme og er unike per apparat (APP-006).
- Entiteter for apparater og elbilladere er unike i hele konfigurasjonen (GEN-013, T9, T15).
- `1 ≤ min_current_a ≤ max_current_a`, hele ampere, standard 6 og 16 (LAD-007, T16).
- Ladetidsrom: start ≠ slutt, hele minutter (LAD-025).
- Områder og standardverdier: REG-001, MAL-002, REG-002, REG-014, STR-002, LAD-009, med oppløsning etter T8.
- Egendefinerte handlinger og maler har gyldig syntaks etter HAs egne skjemaer (T18).
  HA validerer maler bare i event-loopen, så denne sjekken er en egen funksjon
  (`action_and_template_issues`), og `parse_config` må kalles fra event-loopen.

Ugyldig konfigurasjon kan ikke lagres. Ufullstendig konfigurasjon kan lagres,
men reguleringen kan ikke startes før den er fullstendig.

Fullstendig konfigurasjon (REG-016) gir en liste over mangler med kode og mål,
for eksempel `{"code": "missing_power_sensor", "section": "general", "field": "power_sensor"}`
eller `{"code": "missing_action", "section": "appliances", "target": "a1", "field": "turn_on"}`.
Valideringsfeil har samme form. `section` sier om `target` er et apparat
(`appliances`) eller en elbillader (`chargers`), og felt for en variant har
formen `variants.<id>.label`. Statussiden og konfigurasjonssidene oversetter
kodene (GUI-005).

### 3.5 Reguleringens tilstand

Holdes i `RegulationEngine` og nullstilles ved hver start (GEN-007, REG-009):

- hvilke apparater som er på, og antall fiktive apparater som er på per elbillader,
- ventetid per plass: starttidspunkt for ventetiden,
- telleren for økende ventetid: sist styrte plass og antall ganger den er slått på igjen,
- overforbrukstilstand, overforbruk (kWh), straffeperiode, om innhentingen har startet,
- gjeldende ladeprioritering, forbigått per elbillader, når første fiktive apparat ble slått på,
- gjeldende variant per apparat,
- referansetidspunkt for overstyring av ladetidsrom per elbillader (T13): tidspunktet
  bryteren ble slått på, men aldri tidligere enn siste start av reguleringen,
- sikker tilstand,
- teller for reguleringsintervallet (T1).

Snittene ligger i `measurement.py` og er ikke en del av tilstanden (MAL-005).

### 3.6 Handlinger og maler

Standardhandlinger (GEN-013), der entitetens domene har en entydig handling:

| Domene | Slå på / aktiver | Slå av / deaktiver | Sett ladestrøm |
|---|---|---|---|
| `switch`, `input_boolean`, `light`, `fan` | `<domene>.turn_on` | `<domene>.turn_off` | – |
| `climate`, `water_heater` | `<domene>.turn_on` | `<domene>.turn_off` | – |
| `number`, `input_number` | – | – | `<domene>.set_value` med `value: {{ current }}` |

Tabellen ligger ett sted i `actions.py` og sendes til panelet
(`kraftvakt/capabilities`), slik at panelet bare tilbyr «Standard» der det
finnes. Standard for ladestrøm krever en egen entitet, så for ladestrøm tilbys
standardhandling bare hvis den konfigurerte entiteten er av typen `number`.
Ellers er handlingen egendefinert.

Variabler (T14): `entity_id` og `entity` overalt, og `current`,
`min_current` og `max_current` i handlingen for ladestrøm. `entity` er
entitetens tilstandsobjekt slik det er når malen eller handlingen kjøres (for
eksempel `entity.state` og `entity.attributes.current_temperature`). Er
entiteten ikke tilgjengelig i tilstandsmaskinen, er `entity` `none`. Ladestrømmen klemmes alltid mellom
minste og største før handlingen kjøres (LAD-006).

Rekkefølge for elbillader, som motoren uttrykker som to kommandoer etter
hverandre:

- aktivering: sett ladestrøm til minste, deretter aktiver (LAD-012),
- deaktivering: sett ladestrøm til minste, deretter deaktiver (LAD-004).

### 3.7 Entiteter

Alle entitetene hører til én tjenesteenhet «Kraftvakt» og bruker
`has_entity_name` og `translation_key`.

| Entitet | Plattform | Unik ID | Merknad |
|---|---|---|---|
| Reguleringssnitt | `sensor` (power, kW, measurement) | `regulation_average` | ENT-001. Oppdateres per vindu. Utilgjengelig før første snitt. |
| Snittforbruk | `sensor` (power, kW, measurement) | `capacity_average` | ENT-002. |
| Sikker tilstand | `binary_sensor` (problem) | `safe_state` | ENT-005. |
| Regulering | `switch` | `regulation` | ENT-006. Ingen lagret stilling. Samme funksjon som start/stopp i panelet. Kan ikke slås på når konfigurasjonen er ufullstendig. Forsøket logges, og bryteren blir stående av. |
| «‹lader› utenfor regulering» | `switch` | `charger_<id>_excluded` | ENT-003. Stillingen lagres i Store. Utilgjengelig mens billadestyring er deaktivert (T10). |
| «‹lader› overstyr ladetidsrom» | `switch` | `charger_<id>_window_override` | ENT-004. Settes av når overstyringen opphører. Registrerer tidspunktet den ble slått på (T13), bare i minnet. Utilgjengelig mens billadestyring er deaktivert (T10). |

Bryterne for elbilladerne skriver stillingen til Store straks og påvirker
reguleringen først ved neste avgjørelse (REG-005).

### 3.8 WebSocket-API

Alle kommandoer krever administrator.

| Kommando | Inn | Ut | Merknad |
|---|---|---|---|
| `kraftvakt/config/get` | – | konfigurasjon, navn på entiteter, mangler | |
| `kraftvakt/config/save` | hele konfigurasjonen | ok eller valideringsfeil per felt | Avvises med `regulation_running` mens reguleringen kjører (REG-010). Oppdaterer entitetene for elbilladerne (B9). |
| `kraftvakt/regulation/set_running` | `running: bool` | ok | REG-016, GUI-007. Avvises ved start når konfigurasjonen ikke er fullstendig. |
| `kraftvakt/status/subscribe` | – | strøm av statusbilder | Sendes ved hvert nytt snitt, hver avgjørelse og ved start/stopp. |
| `kraftvakt/capabilities` | – | standardhandlinger per domene, grenser og standardverdier | Én kilde for grenser i både backend og panel. |

Forhåndsvisning av maler i panelet («Nå: sann») bruker HAs egen
`render_template`-abonnement og oppdateres mens brukeren skriver. Godkjent av
eier utover kravene.

Statusbildet:

```json
{
  "running": true,
  "missing": [],
  "safe_state": false,
  "penalty": { "active": false, "overconsumption_kwh": 0.0, "recovery_started": false },
  "regulation_average_kw": 7.42,
  "capacity_average_kw": 8.10,
  "power_limit_kw": 10.0,
  "next_decision_at": "2026-11-07T12:01:00+01:00",
  "appliances": [ { "id": "a1", "name": "Varmtvannsbereder", "on": true, "variant": "Morgen", "waiting_until": null } ],
  "chargers": [ { "id": "c1", "name": "Lader garasje", "activated": true, "current_a": 9, "bypassed": false, "waiting": false, "allowed": true } ]
}
```

Feltene `waiting_until`, `current_a`, `bypassed`, `waiting`, `allowed`,
`overconsumption_kwh`, `recovery_started` og `next_decision_at` går ut over
GUI-006 og er godkjent av eier (T11).

---

## 4. Reguleringen steg for steg

Dette er kjernen. Motoren er en tilstandsmaskin med tre inngangspunkter:

- `start(now) -> list[Command]`: nullstiller tilstanden og slår av alt (REG-009).
- `stop() -> list[Command]`: slår av alt (REG-016).
- `decide(input) -> list[Command]`: én avgjørelse (REG-003).

`runtime.py` kaller `start()` straks ved oppstart av HA/integrasjonen og når
brukeren starter, og `stop()` straks når brukeren stopper. Motoren kan selv
starte på nytt inne i `decide()` (straff slutt, sikker tilstand slutt). Etter
hver start nullstilles telleren for reguleringsintervallet (T1).

### 4.1 Plasser og rekkefølge

Prioritetslisten gjøres om til en ordnet liste av **plasser**. En plass er
enten et apparat (gjeldende variant) eller et fiktivt apparat for en
elbillader.

1. For hver oppføring i prioritetslisten: ta med oppføringen bare hvis den er
   gjeldende variant av apparatet (APP-007).
2. Oppføringen `ev_charging` erstattes av de fiktive apparatene for
   elbilladerne som får lade (4.3), flettet etter LAD-015: første fiktive for
   hver elbillader i gjeldende ladeprioritering, så andre, osv.
3. Hvert fiktivt apparat `(lader, k)` er på når `k < antall_på[lader]`.
   Det første fiktive apparatet har elbilladerens effektreserve, de andre
   ingen (LAD-012).

### 4.2 Én avgjørelse

Rekkefølgen under er viktig. Hvert steg kan avslutte avgjørelsen.

1. **Sikker tilstand (REG-011).**
   - Hadde de to siste vinduene ingen gyldig måling og reguleringen ikke er i
     sikker tilstand: slå av alt, gå i sikker tilstand. Ferdig.
   - Er reguleringen i sikker tilstand og siste vindu hadde gyldig måling:
     start på nytt (REG-009). Ferdig.
   - Er reguleringen fortsatt i sikker tilstand: ferdig.
   - Finnes det ikke noe reguleringssnitt ennå (T2): ferdig.
2. **Overstyring av ladetidsrom (LAD-027).** Overstyringer som har utløpt
   (T13), slås av, og kommandoen for å sette ENT-004 tilbake legges i lista.
3. **Overforbruk (STR-004, STR-005, STR-007).**
   - I overforbrukstilstand: legg til netto energi `(snitt − grense) × vindu`
     for hvert reguleringssnitt beregnet siden forrige avgjørelse. Under straff
     før innhenting har startet, legges bare positive bidrag til. Innhentingen
     starter ved første snitt under grensen (T5).
   - Er overforbruket ≤ 0 (og tilstanden startet før denne avgjørelsen):
     avslutt tilstanden.
   - Er ikke tilstanden aktiv og snittforbruket > grensen: start den med
     overforbruk 0 (T4).
4. **Straff (STR-001, STR-003, STR-006, STR-008, STR-009).**
   - Pågår straff og overforbrukstilstanden er avsluttet: start på nytt
     (REG-009). Ferdig.
   - Pågår straff: ferdig. Ingenting slås på.
   - Er snittforbruket > grense + straffeterskel og overforbruket > 0: start
     straff, slå av alt samtidig. Ferdig.
5. **Elbilladere (4.3):** hvem har lov til å lade, hvem er forbigått, gjeldende
   ladeprioritering, hvem er ventende.
6. **Tvungne utkoblinger** (unntak fra REG-004), i denne rekkefølgen:
   - elbilladere som ikke har lov til å lade: alle fiktive av, deaktiver
     (LAD-024, LAD-025, LAD-027),
   - elbilladere som nettopp er blitt forbigått med flere enn ett fiktivt
     apparat på: ned til ett (LAD-030),
   - apparater som bytter gjeldende variant (APP-009): apparatet av hvis det var
     på. Var det av og får en plass over den laveste påslåtte plassen, slås den
     laveste påslåtte av. Ventetid og teller for apparatet nullstilles.
7. **Bygg plasser** etter 4.1.
8. **Over effektgrensen (REG-008).** Er reguleringssnittet > grensen: slå av
   den lavest prioriterte plassen som er på, og som ikke tilhører en forbigått
   elbillader. Avbryt løpende ventetid. Ferdig.
9. **Slå på (REG-006, REG-007, REG-012, REG-013, REG-015).**
   - Kandidat = første plass som er av og ikke hoppes over (forbigått,
     ventende, ikke lov, ikke gjeldende variant). Bare denne kan slås på
     (REG-007). Løpende ventetid for en annen plass avbrytes.
   - Er vilkårene i REG-006 ikke oppfylt: avbryt ventetiden. Ferdig.
   - Beregn ventetid (4.4). Startet ikke ventetiden ennå: start den nå.
   - Er tiden siden ventetiden startet ≥ ventetiden: slå på (med LAD-029 og
     LAD-012 for fiktive apparater), oppdater telleren for økende ventetid,
     nullstill ventetiden.

### 4.3 Elbilladere

Vurderes i steg 5, bare når billadestyring er aktivert.

1. **Lov til å lade:** ikke utenfor regulering (ENT-003), og enten uten
   ladetidsrom, inne i ladetidsrommet eller med aktiv overstyring (LAD-024 til
   LAD-027). Ladetidsrom over midnatt håndteres. Tidssonen er HAs.
2. **Aktivt ladende:** ladeeffekt > 100 W eller ugyldig ladeeffekt, uansett om
   elbilladeren er aktivert eller ikke (LAD-008, GEN-010, T7). Konsekvenser:
   - En elbillader med ugyldig ladeeffekt kan ikke bli forbigått på grunn av
     manglende lading, bare fordi bil tilkoblet er usann (LAD-017).
   - I modus for én om gangen holder en elbillader med ugyldig ladeeffekt de
     andre elbilladerne ventende (LAD-023), også når den er deaktivert eller
     ikke har lov til å lade. Reguleringen oppfører seg som om den lader, og
     starter ikke en annen elbillader.
3. **Forbigått (LAD-017):** bil tilkoblet er angitt og usann, eller den er ikke
   aktivt ladende og første fiktive apparat har vært på i ≥ 2 × reguleringsvinduet.
4. **Gjeldende ladeprioritering (LAD-016, LAD-018, LAD-020):**
   - Nylig forbigåtte flyttes bakerst og beholder innbyrdes rekkefølge.
   - Har en elbillader alle fiktive apparater på: sett rekkefølgen lik den
     konfigurerte for dem som ikke er forbigått. Forbigåtte står fortsatt bakerst.
5. **Én om gangen (LAD-021 til LAD-023, LAD-029):**
   - Er en elbillader aktivt ladende, er det bare den som får fiktive apparater,
     og bare hvis den har lov til å lade. Andre som vil lade, er ventende.
   - Er flere aktivt ladende (for eksempel én som lader og én med ugyldig
     ladeeffekt), velges den aktiverte, og ellers den første i gjeldende
     ladeprioritering.
   - Ellers får den første i gjeldende ladeprioritering som har lov og ikke er
     forbigått, fiktive apparater.
   - Før den valgte aktiveres, deaktiveres enhver annen aktivert elbillader i
     samme avgjørelse (LAD-029).
6. **Flere samtidig (LAD-015):** alle som har lov og ikke er forbigått, flettes.
   Forbigåtte beholder første fiktive apparat (LAD-019, LAD-030), men får ikke
   flere.

### 4.4 Ventetid

- Lineær (REG-013): `ventetid = ventetid_ved_grensen × min(1, snitt / grense)`,
  regnet ut på nytt ved hver avgjørelse mens den går.
- Økende (REG-015, LAD-014, T6): telleren øker når samme plass slås på igjen uten
  at andre plasser er styrt imellom. Fra og med andre gang:
  `ventetid = min(tak, ventetid_ved_grensen + steg × (n − 2))`, der `n` er
  antall ganger plassen er slått på igjen. Steg/tak er 2/15 minutter for
  apparater og 5/30 minutter for fiktive apparater.
- Ventetid 0 gir påslag ved samme avgjørelse (REG-012).

---

## 5. Frontend

### 5.1 Struktur

```
frontend/src/
  kraftvakt-panel.ts       routing på hass.route, toppmeny (GUI-002),
                           ?config_entry= sendes videre til /kraftvakt/appliances (GUI-003)
  api.ts                   typer og WebSocket-kall
  localize.ts              oppslag i translations/{en,nb}.json (B8)
  pages/
    status-page.ts         GUI-005, GUI-006, GUI-007
    general-page.ts        GUI-008
    appliances-page.ts     GUI-009, GUI-011
    charging-page.ts       GUI-010, GUI-011, infotekst om bryterne ENT-003/ENT-004
  components/
    locked-banner.ts       GUI-012
    manual-control-warning.ts  GUI-011
    priority-list.ts       sorterbar liste (ha-sortable)
    appliance-dialog.ts    APP-002–004, APP-006, GEN-013
    charger-dialog.ts      LAD-004–010, LAD-025
    action-field.ts        «Standard» eller egendefinert handling
    condition-field.ts     entitet eller mal, med forhåndsvisning av verdien (GEN-009)
    save-bar.ts            «Lagre» og «Forkast» når utkastet er endret (B7)
```

### 5.2 Ruter

| Rute | Side |
|---|---|
| `/kraftvakt` og `/kraftvakt/status` | Statusside |
| `/kraftvakt/general` | Generelle parametere |
| `/kraftvakt/appliances` | Apparater og prioritetsliste (mål for GUI-003) |
| `/kraftvakt?config_entry=<id>` | Konfigureringsknappen i HA (R1). Panelet erstatter adressen med `/kraftvakt/appliances`. |
| `/kraftvakt/charging` | Billading |

### 5.3 Bygg

- `npm run build` bygger `custom_components/kraftvakt/frontend/kraftvakt-panel.js`.
- CI får en jobb som bygger panelet og feiler hvis den innsjekkede bundlen er
  utdatert.
- Bundlen lastes med versjon i URL-en, slik boilerplate gjør i dag.
- Node-versjonen står i `.nvmrc` og hentes med nvm (`nvm install` / `nvm use`).
  CI bruker `actions/setup-node` med `node-version-file: .nvmrc`.

### 5.4 HA-komponenter i panelet

Resultat fra R2 (9.1), bekreftet mot HA 2026.10.4. Komponentene under er
definert når panelet tegnes og kan brukes direkte. Ingen hack for lasting
trengs.

| Bruk | Komponent |
|---|---|
| Alle felt: tekst, tall, valg, entitet, mal, handling, klokkeslett, av/på | `ha-form` med selektorer: `text`, `number`, `select`, `entity`, `template`, `action`, `time`, `boolean` |
| Enkeltfelt utenfor skjema | `ha-selector` |
| Sorterbare lister | `ha-sortable` med `handle-selector`. Lytt på `item-moved` og tegn listen på nytt. Komponenten flytter ikke elementene selv. |
| Dialoger | `ha-dialog` |
| Kort, varsler, knapper | `ha-card`, `ha-alert`, `ha-button`, `ha-icon-button`, `ha-svg-icon` |
| Brytere og rader | `ha-switch`, `ha-formfield`, `ha-settings-row`, `ha-expansion-panel` |
| Listerader | `ha-md-list-item` i egen beholder |
| Kode | `ha-code-editor`, `ha-yaml-editor` |
| Toppmeny | `ha-menu-button`, `ha-top-app-bar-fixed` eller egen verktøylinje, og `ha-tab-group` for fanene |

Ikke tilgjengelig når panelet tegnes, og skal ikke brukes direkte:
`ha-textfield`, `ha-radio`, `ha-md-list`, `ha-list-item`, `ha-wa-dialog`,
`ha-md-dialog`, `ha-segmented-button` og `window.loadCardHelpers`. Tekstfelt,
radioknapper og valget «Standard / Egendefinert» i skissene lages derfor med
selektorer i `ha-form` (`text`, og `select` med `mode: list` eller
`mode: dropdown`).

Hvilke komponenter HA har lastet, endret seg mellom 2026.3 og 2026.10
(`ha-textfield`, `ha-radio` og `ha-md-list` forsvant). Derfor:

- Panelet venter på `customElements.whenDefined("ha-form")` før første tegning.
- Alle felt lages med `ha-form` eller `ha-selector`. Selektorene laster sine
  egne underkomponenter (`ha-selector-action`, `ha-selector-template` osv.).
- Ved oppgradering av HA-versjonen i `requirements_dev.txt` testes panelet
  manuelt mot listen over, og `.nvmrc` oppdateres til Node-versjonen
  HA-frontenden bruker.

---

## 6. Teststrategi

Følger CLAUDE.md: black box-tester med HA test harness som hovedgrep, og
enhetstester for kompleks logikk og feilhåndtering.

**Enhetstester (`tests/unit/`)**

- `measurement`: tidsvekting med oppdatering hvert 1. og hvert 10. sekund og
  sjeldnere gjennom hele timen (MAL-004), W/kW, negative verdier, fylling ved
  oppstart (MAL-005), tap av én måling (MAL-006), vindu som ikke går opp i 3600 s.
- `regulation`: scenariotester med en liten DSL, for eksempel
  `given(snitt=5.0).decide().expect(on="a1")`. Ett sett per kravgruppe:
  rekkefølge og ett-per-avgjørelse, ventetid og pendling, straff og innhenting,
  varianter og bytte, elbilladere (forbigått, ladeprioritering, én om gangen,
  ladetidsrom, overstyring).
- `config_model`: validering, standardverdier, fullstendighet.
- `actions`: feil logges og gjentas ikke (GEN-012).

**Black box-tester (`tests/`)**

- Oppsett, panel, ingen innstillinger i config flow (GUI-004), panelet er konfigurasjonspanel for integrasjonen (GUI-003).
- Ende-til-ende-regulering: sett tilstand på effektsensoren, frem tiden med
  `async_fire_time_changed`, og sjekk tjenestekall med `async_mock_service`.
- Entiteter: verdier, oppdatering, brytere, lagring over reload (GEN-011).
- WebSocket-kommandoer: lagring avvist mens reguleringen kjører, start avvist
  med ufullstendig konfigurasjon, statusstrøm.
- Oppstart: alt slås av straks, start først etter fullstendig konfigurasjon.

**Frontend:** ingen automatiske tester i første versjon, utover at bygget og
typesjekken (`tsc --noEmit`) går i CI. Testes manuelt mot lokal HA.

Mål for dekning: > 90 % linjedekning for `regulation/` og `measurement.py`,
> 80 % totalt.

---

## 7. Faser

Hver fase er stor nok til én sesjon og avsluttes med at testene og
`ruff` går grønt, README oppdateres ved behov, og arbeidet committes på egen
branch (CLAUDE.md).

### Fase 0 – Tekniske avklaringer

- [x] R1: Finn ut hvordan konfigureringsknappen kan åpne panelet (GUI-003). Løst med `config_panel_domain`, se 9.1. Lagt inn i `__init__.py` med test.
- [x] R2: Bekreft hvordan `ha-form`, `ha-selector` (entitet, mal, handling) og `ha-sortable` lastes i et eget panel. Bekreftet i HA 2026.3.4 og 2026.10.4, se 9.1 og 5.4.
- [x] Eier bekrefter tolkningene T1–T14 (2026-11-07).
- [x] Oppdater planen med resultatet.

### Fase 1 – Konfigurasjonsmodell og lagring

- [x] Forutsetning: oppgrader utviklingsmiljøet og CI til Python 3.14 (9.1), og lås utviklingsavhengighetene til versjonene HA foretrekker. Gjort 2026-11-07.
- [x] `config_model.py` med dataklasser, standardverdier, grenser, validering og `missing_items()`.
- [x] `storage.py` med Store og versjon.
- [x] Enhetstester.
- Krav: GEN-011, GEN-013, REG-001, REG-002, REG-014, REG-016 (fullstendighet), MAL-002, STR-002, APP-001, APP-004–006, APP-008, LAD-001–010, LAD-025.

### Fase 2 – Måling og snittsensorer

- [ ] `measurement.py` (ren logikk) med enhetstester.
- [ ] Lytting på effektsensoren og vindustimer i `runtime.py` (bare måling).
- [ ] `sensor.py` med ENT-001 og ENT-002.
- [ ] Black box-test av sensorene.
- Krav: GEN-003, MAL-001, MAL-003–007, ENT-001, ENT-002.

### Fase 3 – Reguleringsmotor for vanlige apparater

- [ ] `regulation/model.py`, `priority.py`, `waiting.py`, `engine.py` uten straff og elbilladere.
- [ ] Varianter og bytte av variant.
- [ ] Scenariotester.
- Krav: REG-003–008, REG-012–015, APP-007, APP-009.

### Fase 4 – Straff

- [ ] `regulation/penalty.py` og kobling i `engine.py`.
- [ ] Scenariotester, også innhenting og STR-009.
- Krav: STR-001–009.

### Fase 5 – Runtime, handlinger, start/stopp og sikker tilstand

- [ ] `conditions.py`, `actions.py`.
- [ ] `runtime.py`: avgjørelsestakt (T1), start ved oppstart, start/stopp, sikker tilstand, statuslyttere.
- [ ] `binary_sensor.py` (ENT-005) og reguleringsbryter i `switch.py` (ENT-006).
- [ ] Black box-tester ende til ende.
- Krav: GEN-004–010, GEN-012, REG-009–011, REG-016, ENT-005, ENT-006.

### Fase 6 – Elbillading

- [ ] `regulation/charging.py` og fiktive apparater i `priority.py`.
- [ ] Brytere for elbilladere (ENT-003, ENT-004) med lagring og dynamisk oppretting (B9).
- [ ] Scenariotester og black box-tester.
- Krav: LAD-011–030, ENT-003, ENT-004.

### Fase 7 – WebSocket-API

- [ ] Kommandoene i 3.8 med tester.
- Krav: REG-010, REG-016, GUI-001.

### Fase 8 – Panel: grunnmur og statusside

- [x] Forutsetning: Node.js via nvm og `.nvmrc` (9.1). Gjort 2026-11-07.
- [ ] Oppsett av `frontend/` (Lit, TypeScript, Rollup) og CI-jobb.
- [ ] Panelskall med toppmeny og ruter, oversettelser, venting på HA-komponenter (5.4).
- [ ] Videresending fra `?config_entry=` til apparatsiden (GUI-003, 5.2).
- [ ] Statusside.
- Krav: GUI-001, GUI-002, GUI-003, GUI-005–007, SPR-001, SPR-002.

### Fase 9 – Panel: konfigurasjonssider

- [ ] Generelle parametere.
- [ ] Apparater og prioritetsliste med dialog og varianter.
- [ ] Billading med dialog.
- [ ] Låst konfigurasjon, advarsel om manuell styring, lagringslinje.
- Krav: GUI-008–012, GEN-013.

### Fase 10 – Ferdigstilling

- [ ] Gjennomgang av sporbarheten i kapittel 8 mot testene.
- [ ] README: oppsett, konfigurasjon, entiteter, eksempler på maler og handlinger.
- [ ] Oppdater tekstene i `strings.json`/oversettelsene (i dag står det «kWh-mål», kravene bruker «effektgrense»).
- [ ] Manuell test mot lokal HA med simulert effektsensor.
- [ ] Versjon 1.0.0 i `manifest.json` og `pyproject.toml`.

---

## 8. Sporbarhet

| Kravgruppe | Modul | Fase | Testtype |
|---|---|---|---|
| GEN-001–002 | hele løsningen | alle | – |
| GEN-003 | `measurement.py`, `config_model.py` | 1, 2 | black box |
| GEN-004–006 | `regulation/`, `actions.py` | 3, 5 | enhet |
| GEN-007 | `regulation/engine.py`, `runtime.py` | 3, 5 | enhet + black box |
| GEN-008 | `runtime.py`, `websocket_api.py` | 5, 7 | black box |
| GEN-009–010 | `conditions.py` | 5 | enhet + black box |
| GEN-011 | `storage.py` | 1, 6 | black box |
| GEN-012 | `actions.py` | 5 | enhet |
| GEN-013 | `config_model.py`, `actions.py`, panel | 1, 5, 9 | enhet + black box |
| SPR-001–002 | oversettelser | 8, 10 | manuell |
| MAL-001–007 | `measurement.py` | 2 | enhet + black box |
| REG-001–008, REG-012–015 | `regulation/` | 3 | enhet |
| REG-009–011, REG-016 | `runtime.py`, `regulation/engine.py` | 5 | black box |
| STR-001–009 | `regulation/penalty.py` | 4 | enhet |
| APP-001–006, APP-008 | `config_model.py`, panel | 1, 9 | enhet |
| APP-007, APP-009 | `regulation/` | 3 | enhet |
| LAD-001–010, LAD-025 | `config_model.py`, panel | 1, 9 | enhet |
| LAD-011–030 | `regulation/charging.py`, `priority.py` | 6 | enhet + black box |
| ENT-001–006 | plattformene | 2, 5, 6 | black box |
| GUI-001–012 | panel, `websocket_api.py`, `config_flow.py` | 5, 7, 8, 9 | black box (API) + manuell |

I fase 10 utvides tabellen til én rad per krav med navn på testen som
verifiserer kravet.

---

## 9. Risikoer og tekniske avklaringer

| # | Risiko | Tiltak |
|---|---|---|
| R1 | GUI-003: Hvordan kan konfigureringsknappen åpne panelet? | **Løst** (9.1). |
| R2 | HA laster komponenter dovent. Er `ha-form`, `ha-selector` og handlingsredigereren tilgjengelige i et eget panel? | **Løst** (9.1, 5.4). Gjenværende risiko: HA kan endre hvilke komponenter som er lastet. Panelet venter på `ha-form` og bruker bare komponentene i 5.4. |
| R3 | Handlingsredigereren (`ha-selector` med `action`) er stor og kan endre seg mellom HA-versjoner. | Kapsles inn i `action-field.ts`, så en endring bare treffer ett sted. Reserve: YAML-redigering med `ha-yaml-editor`. |
| R4 | Tidtakere kan drive over tid. | Vinduene planlegges mot absolutte tidspunkter med `async_track_point_in_utc_time`, ikke med fast intervall. |
| R5 | Dynamiske entiteter for elbilladere (B9) kan gi foreldreløse entiteter i entitetsregisteret. | Fjern registeroppføringer for elbilladere som er tatt ut av konfigurasjonen ved lagring. |

### 9.1 Resultater fra fase 0

Testet 2026-11-07 med en prototype av et eget panel mot lokale Home
Assistant-instanser i egne venv-er: først 2026.3.4 (frontend 20260312.1), og
etter at minimumsversjonen ble løftet, på nytt mot 2026.10.4 (frontend
20260930.5). Prototypen og test-HA lå i en midlertidig mappe og er ikke sjekket
inn. Resultatene under gjelder 2026.10.4 der ikke annet står.

**R1 – Konfigureringsknappen (GUI-003).** `panel_custom.async_register_panel`
tar parameteren `config_panel_domain`. Er den satt til integrasjonens domene,
viser integrasjonssiden et tannhjul som lenker til
`/<panel>?config_entry=<entry_id>`, i samme fane og uten options flow.
Parameteren er lagt inn i `__init__.py`, med testen
`test_panel_is_config_panel_for_integration`, og bekreftet i nettleseren i
begge versjonene. Tannhjulet åpner panelets rot, så panelet må selv sende
`?config_entry=` videre til `/kraftvakt/appliances` (fase 8). Tannhjulet vises
ikke når config entry-en har en feiltilstand. Da må panelet åpnes fra
sidemenyen.

**R2 – HA-komponenter i panelet.** Ved direkte innlasting av panelet var
komponentene i tabellen i 5.4 allerede definert. Et `ha-form` med selektorene
`entity`, `number` (to desimaler), `template`, `action` og `time` ble tegnet
riktig og lastet sine egne underkomponenter, og `value-changed` ga riktige
verdier. `ha-sortable` sendte `item-moved` med gammel og ny plass ved
dra-og-slipp. Handlingsredigereren la til `data: {}` i handlingen, så lagret
konfigurasjon må tåle normalisering. I 2026.3.4 var også `ha-textfield`,
`ha-radio` og `ha-md-list` definert, men ikke i 2026.10.4.
`window.loadCardHelpers` finnes ikke i et eget panel. Det kjente hacket med
`partial-panel-resolver` virket, men trengs ikke, og skal ikke brukes fordi det
bygger på private API-er.

**Utviklingsmiljø.**

- Home Assistant 2026.3 krever Python 3.14. Prosjektets venv og CI bruker
  Python 3.13 og har HA 2026.2.3, som er eldre enn minimumsversjonen 2026.3 i
  `hacs.json`. **Løst 2026-11-07:** venv, `pyproject.toml`, CI og README bruker
  nå Python 3.14.
- Utviklingsavhengighetene er låst i `requirements_dev.txt` og `pyproject.toml`
  til versjonene HA foretrekker: `homeassistant` og pytest-pakkene slik
  `pytest-homeassistant-custom-component` krever (HA 2026.10.4),
  `home-assistant-frontend` slik HAs frontend-manifest krever, og `ruff` og
  `mypy` slik HA core sine testkrav angir. CI bruker samme ruff-versjon
  (`uvx -c requirements_dev.txt`). GitHub Actions er løftet til
  `actions/checkout@v7` og `astral-sh/setup-uv@v10.3.3`. `hassfest@master` og
  `hacs/action@main` følger anbefalingen fra HA og HACS. Dependabot foreslår
  nye versjoner hver uke.
- Minimumsversjonen er løftet fra 2026.3 til 2026.10 i `hacs.json` og README,
  slik at den er lik versjonen testene kjører mot (2026.10.4).
- Node.js styres med nvm. `.nvmrc` angir 24.21.0, samme versjon som
  HA-frontenden for HA 2026.10 (20260930.5) bruker. Løftes HA-versjonen, følger
  `.nvmrc` frontendens `.nvmrc` for samme versjon. Lokalt er nvm.fish installert,
  og Node 24.21.0 er installert med den. `/opt/homebrew/bin/npm` er en rest etter en
  gammel Homebrew-installasjon av Node, og den virker ikke uten `node`.

---

## 10. Forslag til endringer i REQUIREMENTS.md og annen dokumentasjon

Planen endrer ikke REQUIREMENTS.md. Disse endringene foreslås, og eier avgjør:

1. **REG-002/REG-009:** Presiser hvordan avgjørelsene henger sammen med vinduene
   etter en start (T1).
2. **MAL-006/REG-011:** Presiser hva som gjelder før første gyldige måling etter
   oppstart (T2), og at gyldighet vurderes når vinduet lukkes (T3).
3. **STR-004/STR-009:** Presiser at overforbruket er 0 ved avgjørelsen der
   tilstanden starter, og at straff tidligst kan starte ved neste avgjørelse (T4).
4. **STR-007:** Presiser at innhentingen ikke stopper igjen når den først har
   startet (T5).
5. **REG-015:** Presiser at ventetiden ved vedvarende pendling er fast, og at
   tvungne utkoblinger av andre apparater nullstiller telleren (T6).
6. **LAD-008/LAD-023:** Presiser at også en deaktivert elbillader med ugyldig
   ladeeffekt regnes som aktivt ladende og holder andre elbilladere ventende (T7).
7. **REG-001, REG-014, STR-002, APP-004, LAD-009:** Angi oppløsning: kW med to
   desimaler, hele sekunder og hele minutter (T8).
8. **GEN-013:** Presiser at en entitet bare kan brukes én gang i hele
   konfigurasjonen (T9).
9. **LAD-001:** Presiser at elbilladerne beholdes når billadestyring
   deaktiveres, og at entitetene deres da er utilgjengelige (T10).
10. **LAD-027:** Presiser at «neste ladetidsrom» regnes fra tidspunktet
    overstyringen ble slått på (T13).
11. **GEN-013:** Angi hvilke variabler maler og handlinger får: `entity_id` og
    `entity`, og for ladestrøm `current`, `min_current` og `max_current` (T14).
12. **GUI-006:** Ta inn opplysningene som er godkjent utover minimumskravet (T11).
13. **GUI-012:** Ta inn knappen «Stopp regulering» i låsebanneret (T12).
14. **README.md og oversettelsene:** Bruker «kWh-mål» og «effektmål». Bør bruke
    «effektgrense» som i kravene (fase 10).
15. **GEN-013:** Presiser at kravet om unike entiteter gjelder entiteten som
    identifiserer et apparat eller en elbillader, ikke sensorer og betingelser (T15).
16. **LAD-007:** Angi minste ladestrøm ≥ 1 A og standardverdiene 6 A og 16 A (T16).
