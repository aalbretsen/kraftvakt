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
11. Åpne spørsmål til eier

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
| T13 | LAD-027 | Hvilket tidspunkt regnes «neste ladetidsrom» fra? | Fra tidspunktet bryteren for overstyring (ENT-004) ble slått på, også når reguleringen har vært stoppet eller i sikker tilstand imens. Bryteren registrerer tidspunktet, bare i minnet. Overstyringen opphører ved første avgjørelse der et ladetidsrom har startet etter dette tidspunktet. Selve vurderingen skjer fortsatt ved avgjørelsene (REG-005). Etter omstart av HA eller integrasjonen er tidspunktet ukjent, og første start av reguleringen etter omstarten brukes (LAD-027). Endret 2026-11-08 (Å7): før regnet en senere start av reguleringen som nytt tidspunkt. |
| T14 | GEN-013 | Hvilke variabler er tilgjengelige i maler og handlinger? | `entity_id` og `entity` (entitetens tilstandsobjekt, med f.eks. `entity.state` og `entity.attributes`) i alle maler og handlinger. I tillegg `current`, `min_current` og `max_current` i handlingen for ladestrøm (LAD-006). |
| T15 | GEN-013, T9 | Hvilke felt gjelder kravet om unike entiteter? | Bare entiteten som identifiserer et apparat eller en elbillader (`entity_id`). Effektsensor, sensorer for ladeeffekt, betingelser og handlinger kan bruke samme entitet flere steder. Avklart 2026-11-07. |
| T16 | LAD-007 | Nedre grense og standardverdier for ladestrøm? | Hele ampere, minste ≥ 1 A og minste ≤ største. Standard er 6 A og 16 A, så feltene kan ikke mangle. Avklart 2026-11-07. |
| T17 | APP-001, APP-005, APP-008 | Hva skjer med overflødige oppføringer i prioritetslisten? | Manglende oppføringer legges nederst. Duplikater, oppføringer for apparater eller varianter som ikke finnes, og `ev_charging` mens billadestyring er deaktivert, avvises som ugyldig konfigurasjon. Panelet fjerner dem selv. Avklart 2026-11-07. |
| T18 | GEN-013 | Hvor grundig valideres handlinger og maler? | Egendefinerte handlinger valideres med HAs skjema for skript, og maler sjekkes for syntaksfeil, i fase 1. Om «Standard» finnes for entitetens domene, valideres i fase 5, der tabellen i `actions.py` ligger. Avklart 2026-11-07. |
| T19 | MAL-007 | Hva gjelder når effektsensoren mangler enhet eller oppgir en annen effektenhet enn W og kW? | W og kW regnes om. En sensor uten enhet leses som watt. Alle andre enheter gir ugyldig måleverdi. Avklart 2026-11-07. |
| T20 | MAL-001, T1 | Hvor er takten til reguleringsvinduene forankret? | Første vindu starter når integrasjonen starter, og hvert vindu slutter ett reguleringsvindu etter forrige, planlagt mot absolutte tidspunkter (R4). Alle vinduer er hele vinduer. Avklart 2026-11-07. |
| T21 | MAL-005, MAL-006, REG-011 | Hva viser snittsensorene mens effektsensoren er borte over lengre tid, også når reguleringen er stoppet og ingen sikker tilstand kan inntre? | Målingen forkaster historikken når effektsensoren var uten gyldig måleverdi da to vinduer på rad ble lukket, uansett om reguleringen kjører. Snittsensorene er da utilgjengelige til en gyldig verdi kommer, og den fylles bakover etter MAL-005. Sikker tilstand (fase 5) bruker samme vilkår. Avklart 2026-11-07. |
| T22 | APP-009 | Flere apparater kan bytte variant ved samme avgjørelse, for eksempel to varianter «Morgen» som begge starter klokken 05. I hvilken rekkefølge håndteres byttene? | Bytte av variant følger APP-009: apparatet er avslått etter byttet og slås på igjen på vanlig måte, etter ventetid. Bytter flere apparater samtidig, håndteres de ett og ett i rekkefølgen til den nye plassen, høyest prioritet først. Et apparat som var på før byttet, slås av hvis det fortsatt er på. Et apparat som var av, slår av det laveste prioriterte apparatet som er på, hvis den nye plassen er over det. Et apparat som uansett må av, kan dermed regnes som det som gir plass. Avklart 2026-11-07. |
| T23 | GUI-006, T11 | Statussiden viser apparatene i gjeldende prioritetsrekkefølge og elbilladerne i gjeldende ladeprioritering. Hvor kommer rekkefølgen fra? | Backend sorterer listene i statusbildet (3.8): apparatene etter oppføringen for gjeldende variant i prioritetslisten (apparatet selv før første avgjørelse), og elbilladerne etter gjeldende ladeprioritering (LAD-016). Avklart 2026-11-07. |
| T24 | GUI-006, T11, ENT-003, LAD-025 | Hvordan vet statussiden hvorfor en elbillader ikke har lov til å lade? | Statusbildet får feltet `excluded` per elbillader: om elbilladeren var tatt ut av reguleringen (ENT-003) ved siste avgjørelse, og `null` før første avgjørelse etter start. Panelet viser «Utenfor regulering» når den er sann, ellers «Utenfor ladetidsrom (start–slutt)» når elbilladeren ikke har lov til å lade og har ladetidsrom. Før første avgjørelse vises ingen grunn. Avklart 2026-11-07. |
| T25 | LAD-002, LAD-010, LAD-017, LAD-029 | Med én elbillader om gangen og uten «bil tilkoblet» kan Kraftvakt bare se at en bil er tilkoblet ved å aktivere elbilladeren, så elbilladere uten bil blir aktivert etter tur. | «Bil tilkoblet» er påkrevd for hver elbillader når bare én kan lade om gangen. Mangler den, er konfigurasjonen ikke fullstendig (`missing_car_connected`), og reguleringen kan ikke startes (REG-016). Avklart 2026-11-08 (Å6). |
| T26 | REG-009 | Når HA starter, kan Kraftvakt lastes før integrasjonene til apparatene, så av-kommandoene ved start kan feile. | Ved oppstart av HA starter reguleringen når HA har startet (`async_at_started`). Ved reload, og når brukeren starter reguleringen, skjer starten straks. Starter brukeren eller stopper reguleringen før HA har startet, gjelder det brukeren gjorde. Avklart 2026-11-08 (Å3). |
| T27 | GEN-011 | Hva skjer når den lagrede konfigurasjonen ikke kan leses? | Oppsettet stopper med `ConfigEntryError` og en oversatt feilmelding (`unreadable_configuration`). Filen endres ikke. Avklart 2026-11-08 (Å4). |
| T28 | REG-009 | Ved reload kan handlinger fra den gamle runtime-en fortsatt kjøre når den nye slår alt av. | Låsen for handlingene ligger i `hass.data` og deles mellom runtime-ene, så den nye venter til de gamle handlingene er ferdige. Avklart 2026-11-08 (Å5). |

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
| `measurement.py` | Tidsvektet integrasjon av effekten (stykkevis konstant: siste verdi gjelder til neste). Lukker vinduer, holder glidende timesvindu, enhetsomregning W/kW (T19), negative verdier til 0, fylling ved oppstart og etter to lukkede vinduer uten gyldig måling (T21), og om sensoren var gyldig da vinduet ble lukket (T3). | MAL-001, MAL-003–007 |
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
men reguleringen kan ikke startes før den er fullstendig. Når bare én
elbillader kan lade om gangen, må hver elbillader ha «bil tilkoblet» for å være
fullstendig (T25).

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
- ventetid: plassen som venter, og når ventetiden startet. Bare plassen som står
  for tur, kan vente (4.2, steg 9),
- telleren for økende ventetid: sist styrte plass og antall ganger den er slått på igjen,
- overforbrukstilstand, overforbruk (kWh), straffeperiode, om innhentingen har startet,
- gjeldende ladeprioritering, forbigått per elbillader, når første fiktive apparat ble slått på,
- gjeldende variant per apparat,
- sikker tilstand,
- teller for reguleringsintervallet (T1).

Snittene ligger i `measurement.py` og er ikke en del av tilstanden (MAL-005).

Referansetidspunktet for overstyring av ladetidsrom (T13) er tidspunktet
bryteren ble slått på, eller første start av reguleringen etter en omstart av
HA eller integrasjonen. Det holdes av `ChargerSwitchBoard` og nullstilles ikke
når reguleringen startes på nytt.

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
| `kraftvakt/config/get` | – | `{config, entity_names, missing}` | `entity_names` gir navnet i HA for entiteten til hvert apparat og hver elbillader (GEN-013). |
| `kraftvakt/config/save` | `config`: hele konfigurasjonen | `{saved: true, config, missing}` eller `{saved: false, errors}` | Avvises med feilkoden `regulation_running` mens reguleringen kjører (REG-010). `errors` og `missing` har formen i 3.4. Lagret `config` har prioritetslisten fullført (APP-008). Oppdaterer entitetene for elbilladerne (B9). |
| `kraftvakt/regulation/set_running` | `running: bool` | `{running}` | REG-016, GUI-007. Avvises ved start med feilkoden `config_incomplete` når konfigurasjonen ikke er fullstendig. |
| `kraftvakt/status/subscribe` | – | tomt resultat, deretter hendelser med statusbildet | Første statusbilde sendes straks. Deretter ved hvert nytt snitt, hver avgjørelse, start/stopp og lagring av konfigurasjonen. Abonnementet virker også etter reload av config entry. |
| `kraftvakt/capabilities` | – | `{default_actions, limits, defaults}` | Én kilde for grenser i både backend og panel. |

Kommandoene som trenger runtime, avvises med feilkoden `not_loaded` når
integrasjonen ikke er lastet. Brukere som ikke er administratorer, får HAs
feilkode `unauthorized`.

Svaret fra `kraftvakt/capabilities`, forkortet:

```json
{
  "default_actions": {
    "appliances": { "turn_on": ["switch", "input_boolean", "light", "fan", "climate", "water_heater"], "turn_off": ["…"] },
    "chargers": { "activate": ["…"], "deactivate": ["…"], "set_current": ["number", "input_number"] }
  },
  "limits": {
    "general": { "power_limit_kw": { "min": 1, "max": 50, "step": 0.01 }, "regulation_window_s": { "min": 10, "max": 600, "step": 1 }, "…": {} },
    "appliances": { "power_reserve_kw": { "min": 0, "max": null, "step": 0.01 } },
    "chargers": { "min_current_a": { "min": 1, "max": null, "step": 1 }, "max_current_a": { "…": 0 }, "power_reserve_kw": { "min": 0, "max": 5, "step": 0.01 } }
  },
  "defaults": {
    "general": { "power_sensor": null, "power_limit_kw": 10.0, "regulation_window_s": 60, "regulation_interval": 1, "wait_at_limit_min": 5, "penalty_threshold_kw": 1.0 },
    "appliances": { "power_reserve_kw": null },
    "charging": { "enabled": false, "one_at_a_time": true },
    "chargers": { "min_current_a": 6, "max_current_a": 16, "power_reserve_kw": 4.0 }
  }
}
```

`default_actions` gir domenene som har standardhandling, per seksjon og felt.
Panelet tilbyr «Standard» bare når domenet til entiteten står i listen (3.6).

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
  "chargers": [ { "id": "c1", "name": "Lader garasje", "activated": true, "current_a": 9, "bypassed": false, "waiting": false, "allowed": true, "excluded": false, "waiting_until": null } ]
}
```

Tidspunkter er ISO 8601 i HAs tidssone. Snittene er `null` til første vindu er
lukket. `next_decision_at` er `null` mens reguleringen er stoppet.
`waiting_until` er satt for apparatet eller elbilladeren som står for tur og
venter (REG-012), og regnes ut på nytt ved hver avgjørelse (REG-013). For en
elbillader gjelder den neste fiktive apparat. `variant` er merkelappen til
gjeldende variant, eller `null` når apparatet selv gjelder. Detaljene for
elbilladerne gjelder etter siste avgjørelse, og `allowed` er usann før første
avgjørelse etter start. `excluded` er `null` før første avgjørelse etter start
(T24). Apparatene står i rekkefølgen til gjeldende variant i prioritetslisten,
og elbilladerne i gjeldende ladeprioritering (T23).

Feltene `waiting_until`, `current_a`, `bypassed`, `waiting`, `allowed`,
`excluded`, `overconsumption_kwh`, `recovery_started` og `next_decision_at` går
ut over GUI-006 og er godkjent av eier (T11, T24).

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
   - Gjeldende variant vurderes likevel ved hver avgjørelse under straff
     (APP-007). Alt er av, så byttet gir ingen kommandoer.
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
                           ?config_entry= sendes videre til /kraftvakt/appliances (GUI-003),
                           utkastet, lagringslinjen og låsen for konfigurasjonssidene (B7, GUI-012)
  api.ts                   typer og WebSocket-kall
  localize.ts              oppslag i translations/{en,nb}.json (B8)
  navigation.ts            sidene og navigering mellom dem
  issues.ts                tekst og side for mangler og valideringsfeil (3.4)
  draft.ts                 hjelpere for utkastet: ID-er, flytting, fullført prioritetsliste (T17)
  validation.ts            sjekk av utkastet mot grensene fra capabilities, og mangler (3.4)
  entities.ts              navn på entiteter, og Kraftvakts egne entiteter
  types.ts, format.ts, clock.ts  HA-typer, tallformat og nedtelling
  pages/
    status-page.ts         GUI-005, GUI-006, GUI-007
    config-page.ts         felles egenskaper for konfigurasjonssidene
    general-page.ts        GUI-008
    appliances-page.ts     GUI-009, GUI-011
    charging-page.ts       GUI-010, GUI-011, infotekst om bryterne ENT-003/ENT-004
  components/
    locked-banner.ts       GUI-012, med «Stopp regulering» (T12)
    manual-control-warning.ts  GUI-011
    sortable-list.ts       sorterbar liste (ha-sortable) for prioritetslisten og elbilladerne
    item-dialog.ts         felles for dialogene: entitet, handlinger, felt med grenser, knapper
    appliance-dialog.ts    APP-002–004, APP-006, GEN-013
    charger-dialog.ts      LAD-004–010, LAD-025
    action-field.ts        «Standard» eller egendefinert handling
    condition-field.ts     entitet eller mal, med forhåndsvisning av verdien (GEN-009)
    save-bar.ts            «Lagre» og «Forkast» når utkastet er endret (B7)
    confirm-dialog.ts      spør før ulagrede endringer forkastes
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
- Handlingsredigereren og dialogen for å legge til en handling henter tekstene
  sine fra HAs oversettelsesfragment `config`, som bare HAs egen
  konfigurasjonsside laster. Panelet laster det med
  `hass.loadFragmentTranslation("config")`. Uten det er etikettene og menyene
  i handlingsredigereren tomme (funnet i fase 9).
- `ha-dialog` er i 2026.10 bygd på `wa-dialog`: `open`, `header-title`, sporet
  `footer` for knappene og hendelsen `closed`. Lukkes dialogen fra innsiden,
  blir `open` stående, så panelet setter den selv ved `closed`.
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

- [x] `measurement.py` (ren logikk) med enhetstester.
- [x] Lytting på effektsensoren og vindustimer i `runtime.py` (bare måling).
- [x] `sensor.py` med ENT-001 og ENT-002.
- [x] Black box-test av sensorene.
- Krav: GEN-003, MAL-001, MAL-003–007, ENT-001, ENT-002.

### Fase 3 – Reguleringsmotor for vanlige apparater

- [x] `regulation/model.py`, `priority.py`, `waiting.py`, `engine.py` uten straff og elbilladere.
- [x] Varianter og bytte av variant (T22).
- [x] Scenariotester.
- Krav: REG-003–008, REG-012–015, APP-007, APP-009.

### Fase 4 – Straff

- [x] `regulation/penalty.py` og kobling i `engine.py`.
- [x] Scenariotester, også innhenting og STR-009.
- Krav: STR-001–009.

### Fase 5 – Runtime, handlinger, start/stopp og sikker tilstand

- [x] `conditions.py`, `actions.py`. Valideringen av standardhandlinger (T18) er `default_action_issues()` i `actions.py`. Den kan ikke kalles fra `parse_config()` uten sirkulær import, så `kraftvakt/config/save` i fase 7 må kalle begge.
- [x] `runtime.py`: avgjørelsestakt (T1), start ved oppstart, start/stopp, sikker tilstand, statuslyttere.
- [x] `binary_sensor.py` (ENT-005) og reguleringsbryter i `switch.py` (ENT-006).
- [x] Black box-tester ende til ende.
- Krav: GEN-004–010, GEN-012, REG-009–011, REG-016, ENT-005, ENT-006.

### Fase 6 – Elbillading

- [x] `regulation/charging.py` og fiktive apparater i `priority.py`.
- [x] Brytere for elbilladere (ENT-003, ENT-004) med lagring og dynamisk oppretting (B9). Stillingene og tidspunktet overstyringen ble slått på, holdes av `ChargerSwitchBoard` i `charger_switches.py`, som også lagrer konfigurasjonen sammen med bryterne. `kraftvakt/config/save` i fase 7 skal lagre en ny konfigurasjon med `ChargerSwitchBoard.async_update_config()`. Da legges bryterne for nye elbilladere til, og bryterne for elbilladere som er tatt ut, fjernes fra entitetsregisteret (R5). Bryterne får navnet til elbilladerens entitet når de opprettes.
- [x] Scenariotester og black box-tester.
- Krav: LAD-011–030, ENT-003, ENT-004.

### Fase 7 – WebSocket-API

- [x] Kommandoene i 3.8 med tester, i `websocket_api.py`. Kommandoene registreres i `async_setup`. `kraftvakt/config/save` validerer med `parse_config()` og `default_action_issues()` og lagrer med `KraftvaktRuntime.async_save_config()`. Den lager ny motor og ny `ActionRunner` (med felles lås, så kommandoer fra forrige konfigurasjon blir ferdige først), følger ny effektsensor fra nå og nytt reguleringsvindu fra neste vindu, og lagrer gjennom `ChargerSwitchBoard.async_update_config()`. Snittene går videre (GEN-007). Grensene ligger i `SETTING_RANGES` i `config_model.py` og brukes både til validering og i `kraftvakt/capabilities`.
- Krav: REG-010, REG-016, GUI-001.

### Fase 8 – Panel: grunnmur og statusside

- [x] Forutsetning: Node.js via nvm og `.nvmrc` (9.1). Gjort 2026-11-07.
- [x] Oppsett av `frontend/` (Lit, TypeScript, Rollup) og CI-jobb. Lit 3.3.3 og TypeScript 6.0.3 som HA-frontenden for 2026.10 bruker, `@mdi/js` 7.4.47 for ikoner, og ellers siste stabile versjoner, låst i `package.json`. Bundlen er minifisert og merket som generert i `.gitattributes`. CI-jobben «Panel» kjører `npm ci`, typesjekk og bygg, og feiler hvis bundlen avviker fra den innsjekkede.
- [x] Panelskall med toppmeny og ruter, oversettelser, venting på HA-komponenter (5.4). Fanene er `ha-tab-group` med `ha-tab-group-tab` og hendelsen `wa-tab-show`. Navigering skjer med `navigateToPage()` i `navigation.ts`. Oversettelsesnøklene typesjekkes, også at `nb.json` har alle nøklene i `en.json`. Panelet abonnerer på status og henter konfigurasjonen når reguleringen startes eller stoppes, eller når mangellisten endres. Status og konfigurasjon sendes ned til sidene, slik at fase 9 kan bruke `status.running` til låsen (GUI-012).
- [x] Videresending fra `?config_entry=` til apparatsiden (GUI-003, 5.2).
- [x] Statusside. Mangler beskrives i `issues.ts`, som fase 9 kan bruke for valideringsfeil. Backend sorterer listene i statusbildet (T23) og gir `excluded` per elbillader (T24). Konfigurasjonssidene er plassholdere til fase 9. Testet i nettleser mot lokal HA 2026.10.4, på engelsk og norsk og i smal visning.
- Krav: GUI-001, GUI-002, GUI-003, GUI-005–007, SPR-001, SPR-002.

### Fase 9 – Panel: konfigurasjonssider

- [x] Generelle parametere. Grensene og standardverdiene i hjelpetekstene kommer fra `kraftvakt/capabilities`. Kraftvakts egne sensorer er tatt ut av velgeren for effektsensor og sensor for ladeeffekt.
- [x] Apparater og prioritetsliste med dialog og varianter. Prioritetslisten og elbilladerlisten bruker `sortable-list.ts`. Dialogene for apparat og elbillader bygger på `item-dialog.ts`. «Standard» tilbys bare for domenene i `default_actions`, og velges når det velges en entitet som har standardhandling. En egendefinert handling starter som standardhandlingen. Maler forhåndsvises med `render_template`, der `entity` er tilstandsobjektet slik frontenden har det.
- [x] Billading med dialog.
- [x] Låst konfigurasjon, advarsel om manuell styring, lagringslinje. Konfigurasjonssidene deler ett utkast i `kraftvakt-panel.ts`. Panelet sjekker utkastet mot grensene og regner ut mangler selv (`validation.ts`), slik at feil vises før lagring. «Lagre» er deaktivert så lenge utkastet har slike feil. Feilene fra `kraftvakt/config/save` vises ved feltene til neste lagring. Panelet spør før ulagrede endringer forkastes når brukeren går til statussiden, og nettleseren spør når siden lukkes eller lastes på nytt. Navigering i HAs sidemeny kan ikke stoppes. Utkastet forkastes når reguleringen startes, siden det ikke kan lagres da.
- Testet i nettleser mot lokal HA 2026.10.4: konfigurasjon fra bunnen til reguleringen kunne startes, endring mens den er stoppet, låsen og «Stopp regulering» mens den kjører, engelsk og norsk og smal visning.
- Krav: GUI-008–012, GEN-013.

### Fase 10 – Ferdigstilling

- [x] Gjennomgang av sporbarheten i kapittel 8 mot testene. Kapittel 8 har nå én rad per krav. Krav uten egen test fikk test: GEN-002 (manifestet), GEN-005 og GEN-006 (tilstanden til apparatene leses ikke), SPR-001 (engelske navn som standard) og GUI-004 (ingen felt i config flow). GUI-002 og GUI-011 ligger bare i panelet og er testet manuelt.
- [x] README: oppsett, slik virker det, konfigurasjon, statussiden, entiteter, eksempler på maler og handlinger, simulert effektsensor for utvikling og ny statuslinje.
- [x] Oppdater tekstene i `strings.json`/oversettelsene og README til «effektgrense». Panelets tekster brukte allerede kravenes begreper.
- [x] Manuell test mot lokal HA 2026.10.4 med simulert effektsensor (`input_number` og mal-sensor), `input_boolean` som apparater og elbillader, reguleringsvindu 10 s og ventetid 1 min. Testet 2026-11-08: integrasjonen legges til uten felt, effektsensor og vindu settes i panelet, start slår av alt (også apparater som var slått på for hånd) og setter ladestrømmen til minste før deaktivering, apparatene slås på ett og ett med ventetid, elbilladeren uten ladeeffekt blir forbigått på 6 A og får mer strøm når bilen trekker strøm, bytte til varianten «Morgen» slår apparatet av og på igjen, 12 kW slår av det lavest prioriterte først (bassengvarmeren, så ett ampere), sensoren utilgjengelig gir sikker tilstand etter to vinduer, gyldig verdi fyller snittene og starter på nytt, reload med 20 kW gir straff med overforbruk på statussiden, og straffen slutter når overforbruket er hentet inn. Bryteren stopper reguleringen. «Rediger i YAML» i handlingsredigereren er bekreftet. Funn: nedtellingen til neste avgjørelse kunne vise ett sekund for mye (0:11 med vindu 10 s) rett etter en avgjørelse, fordi panelet regnet med klokka fra forrige sekund. Rettet etter avklaring med eier. Nettleseren brukte en gammel bundle fra en tidligere test på samme port, fordi URL-en bare har versjonen (står i README).
- [ ] Versjon 1.0.0 i `manifest.json` og `pyproject.toml`. Eier har bestemt å vente med 1.0.0 (2026-11-08). Versjonen er fortsatt 0.1.0.
- [x] Åpne spørsmål til eier (kapittel 11) avklart 2026-11-08, og endringene gjort: start når HA har startet (T26), tydelig feil ved uleselig konfigurasjon (T27), handlinger etter reload venter på de gamle (T28), «bil tilkoblet» påkrevd med én elbillader om gangen (T25), overstyring regnet fra bryteren (T13) og nedtellingen på statussiden.

---

## 8. Sporbarhet

Én rad per krav, med testene som verifiserer kravet. Stiene er relative til
`tests/`, og `unit/` er enhetstester. Gjennomgått mot testene i fase 10.

«manuell» betyr at kravet, eller delen av det som ligger i panelet, er testet
manuelt i nettleser mot lokal Home Assistant 2026.10.4 i fase 8, 9 og 10.
Panelet har ingen automatiske tester i første versjon (kapittel 6). Black
box-testene av WebSocket-API-et dekker det panelet får fra backend.

| Krav | Modul | Testtype | Tester |
|---|---|---|---|
| GEN-001 | hele løsningen | black box | `test_regulation.py`: `test_appliances_are_turned_on_one_per_decision`, `test_lowest_priority_is_turned_off_above_the_limit`, `test_penalty_turns_everything_off_until_paid_back` |
| GEN-002 | `manifest.json` | black box | `test_init.py`: `test_integration_runs_locally` |
| GEN-003 | `runtime.py`, `config_model.py` | enhet + black box | `test_runtime.py`: `test_power_sensor_state_feeds_the_averages`; `test_websocket_api.py`: `test_saved_power_sensor_and_window_are_measured`; `unit/test_config_completeness.py`: `test_default_config_misses_power_sensor` |
| GEN-004 | `regulation/` | enhet | `unit/regulation/test_engine_switching.py`: `test_appliances_are_turned_on_one_per_decision_in_priority_order`; `unit/regulation/test_engine_charging.py`: `test_current_increases_one_ampere_per_fictive_appliance` |
| GEN-005 | `regulation/` | enhet + black box | `test_regulation.py`: `test_appliance_states_are_not_taken_into_account`; `unit/regulation/test_engine_switching.py`: `test_appliances_are_turned_on_one_per_decision_in_priority_order` |
| GEN-006 | `regulation/`, `runtime.py` | enhet + black box | `test_regulation.py`: `test_appliance_states_are_not_taken_into_account`; `test_charging.py`: `test_charger_without_car_is_not_activated`; `unit/regulation/test_charging.py`: `test_actively_charging_above_100_watt_or_without_a_valid_value` |
| GEN-007 | `regulation/engine.py`, `runtime.py` | enhet + black box | `test_regulation.py`: `test_reload_starts_the_regulation_again`; `unit/regulation/test_engine_switching.py`: `test_start_begins_with_a_new_state`; `unit/regulation/test_engine_cycling.py`: `test_restart_resets_the_increase`; `unit/regulation/test_engine_penalty.py`: `test_stop_and_start_end_the_penalty`; `unit/regulation/test_engine_safe_state.py`: `test_safe_state_ends_a_penalty`; `unit/regulation/test_engine_charging.py`: `test_current_priority_starts_as_configured_at_each_start` |
| GEN-008 | `runtime.py`, `websocket_api.py` | enhet + black box | `test_websocket_api.py`: `test_new_configuration_is_used_from_the_next_start`; `test_charging.py`: `test_charger_switches_are_unavailable_while_charging_is_disabled`; `unit/regulation/test_engine_charging.py`: `test_chargers_are_left_alone_while_charging_is_disabled` |
| GEN-009 | `conditions.py` | enhet + black box | `unit/test_conditions.py`: `test_entity_is_true_only_when_on`, `test_missing_entity_is_false`, `test_template_is_true_only_for_the_boolean_true`, `test_failing_template_is_false`; `test_regulation.py`: `test_variant_condition_moves_the_appliance`; `test_charging.py`: `test_charger_without_car_is_not_activated` |
| GEN-010 | `conditions.py`, `regulation/charging.py` | enhet + black box | `unit/regulation/test_charging.py`: `test_actively_charging_above_100_watt_or_without_a_valid_value`, `test_charger_without_valid_charging_power_is_bypassed_only_without_car`; `test_charging.py`: `test_charger_without_car_is_not_activated` |
| GEN-011 | `storage.py`, `charger_switches.py` | enhet + black box | `test_storage.py`: `test_saved_data_survives_restart`, `test_load_without_stored_data_gives_defaults`; `test_init.py`: `test_unreadable_configuration_gives_a_clear_error`; `unit/test_config_model.py`: `test_defaults_follow_requirements`; `test_charging.py`: `test_excluded_switch_stops_charging_and_is_saved`, `test_charger_switches_are_kept_over_a_reload` |
| GEN-012 | `actions.py` | enhet + black box | `unit/test_actions.py`: `test_failed_action_is_logged_and_not_retried`, `test_action_that_cannot_run_is_logged`; `test_regulation.py`: `test_failed_action_does_not_stop_the_regulation` |
| GEN-013 | `config_model.py`, `actions.py`, `conditions.py`, panel | enhet + black box + manuell | `unit/test_config_validation.py`: `test_entity_is_unique_across_appliances_and_chargers`, `test_entity_uniqueness_ignores_sensors_and_conditions`; `unit/test_config_completeness.py`: `test_appliance_needs_entity_and_both_actions`; `unit/test_actions.py`: `test_default_actions_must_exist_for_the_domain`, `test_custom_actions_get_the_entity_variables`; `unit/test_conditions.py`: `test_template_gets_the_entity_of_the_appliance`; `test_regulation.py`: `test_template_condition_gets_the_appliance_entity`, `test_custom_action_gets_the_entity_variables`; `test_websocket_api.py`: `test_config_get_gives_configuration_names_and_missing` |
| SPR-001 | `strings.json`, panelets oversettelser | black box + manuell | `test_regulation.py`: `test_entity_names_are_translated` |
| SPR-002 | `translations/nb.json`, panelets oversettelser | black box + manuell | `test_regulation.py`: `test_entity_names_are_translated`; `test_sensor.py`: `test_sensor_names_are_translated` |
| MAL-001 | `measurement.py`, `runtime.py` | enhet + black box | `unit/test_measurement.py`: `test_window_end_follows_the_window_length`, `test_regulation_windows_do_not_overlap`; `test_runtime.py`: `test_windows_close_at_absolute_times_from_start`; `test_sensor.py`: `test_sensors_are_updated_once_per_window` |
| MAL-002 | `config_model.py` | enhet + black box | `unit/test_config_model.py`: `test_defaults_follow_requirements`; `unit/test_config_validation.py`: `test_general_ranges`; `test_sensor.py`: `test_window_length_comes_from_the_configuration` |
| MAL-003 | `measurement.py` | enhet + black box | `unit/test_measurement.py`: `test_capacity_average_slides_over_the_last_hour`, `test_capacity_window_does_not_depend_on_the_window_length`; `test_sensor.py`: `test_capacity_average_over_a_whole_hour_of_updates` |
| MAL-004 | `measurement.py` | enhet + black box | `unit/test_measurement.py`: `test_regulation_average_is_weighted_by_time`, `test_averages_are_correct_for_any_update_rate`, `test_update_rate_does_not_change_the_result`; `test_sensor.py`: `test_capacity_average_over_a_whole_hour_of_updates` |
| MAL-005 | `measurement.py` | enhet + black box | `unit/test_measurement.py`: `test_first_measurement_fills_both_windows_backwards`, `test_two_invalid_closes_in_a_row_discard_the_history`; `test_sensor.py`: `test_sensors_follow_an_outage_of_the_power_sensor`; `test_regulation.py`: `test_regulation_starts_again_when_the_power_sensor_is_back` |
| MAL-006 | `measurement.py`, `runtime.py` | enhet + black box | `unit/test_measurement.py`: `test_one_invalid_close_uses_the_last_valid_measurement`; `unit/regulation/test_engine_safe_state.py`: `test_one_invalid_close_is_tolerated`; `test_runtime.py`: `test_unavailable_power_sensor_makes_the_window_invalid`; `test_regulation.py`: `test_safe_state_when_the_power_sensor_is_lost` |
| MAL-007 | `measurement.py` | enhet + black box | `unit/test_measurement.py`: `test_power_kw_converts_valid_measurements`; `test_runtime.py`: `test_power_sensor_state_feeds_the_averages`; `test_sensor.py`: `test_power_sensor_without_unit_is_read_as_watt` |
| REG-001 | `config_model.py` | enhet | `unit/test_config_model.py`: `test_defaults_follow_requirements`; `unit/test_config_validation.py`: `test_general_ranges` |
| REG-002 | `config_model.py`, `runtime.py` | enhet + black box | `unit/test_config_model.py`: `test_defaults_follow_requirements`; `unit/test_config_validation.py`: `test_general_ranges`; `test_regulation.py`: `test_decisions_follow_the_regulation_interval` |
| REG-003 | `regulation/engine.py`, `runtime.py` | enhet + black box | `unit/regulation/test_engine_switching.py`: `test_no_decision_before_there_is_an_average`; `test_regulation.py`: `test_appliances_are_turned_on_one_per_decision` |
| REG-004 | `regulation/engine.py` | enhet + black box | `unit/regulation/test_engine_switching.py`: `test_appliances_are_turned_on_one_per_decision_in_priority_order`, `test_lowest_priority_is_switched_off_above_the_limit`; `unit/regulation/test_engine_variants.py`: `test_switch_happens_at_the_same_decision_as_switching_off`; `unit/regulation/test_engine_penalty.py`: `test_penalty_turns_everything_off_at_once`; `test_regulation.py`: `test_appliances_are_turned_on_one_per_decision` |
| REG-005 | `runtime.py`, `regulation/engine.py` | enhet + black box | `unit/regulation/test_engine_charging.py`: `test_override_ends_also_during_a_penalty`; `test_regulation.py`: `test_appliances_are_turned_on_one_per_decision`, `test_safe_state_when_the_power_sensor_is_lost`; `test_charging.py`: `test_excluded_switch_stops_charging_and_is_saved` |
| REG-006 | `regulation/engine.py` | enhet | `unit/regulation/test_engine_switching.py`: `test_nothing_is_turned_on_at_or_above_the_limit`, `test_power_reserve_must_fit_under_the_limit`, `test_nothing_changes_at_the_limit`; `unit/regulation/test_engine_cycling.py`: `test_persistent_cycling_still_needs_room_under_the_limit` |
| REG-007 | `regulation/engine.py`, `regulation/priority.py` | enhet + black box | `unit/regulation/test_engine_switching.py`: `test_appliances_are_turned_on_one_per_decision_in_priority_order`, `test_lower_priority_waits_for_higher_priority`; `unit/regulation/test_priority.py`: `test_fictive_appliances_of_chargers_that_may_not_charge_or_are_bypassed`; `test_regulation.py`: `test_appliances_are_turned_on_one_per_decision` |
| REG-008 | `regulation/engine.py` | enhet + black box | `unit/regulation/test_engine_switching.py`: `test_lowest_priority_is_switched_off_above_the_limit`; `unit/regulation/test_engine_waiting.py`: `test_switching_off_cancels_the_waiting_time`; `unit/regulation/test_engine_charging.py`: `test_bypassed_charger_is_not_switched_off_above_the_limit`; `test_regulation.py`: `test_lowest_priority_is_turned_off_above_the_limit` |
| REG-009 | `regulation/engine.py`, `runtime.py` | enhet + black box | `unit/regulation/test_engine_switching.py`: `test_start_turns_off_every_appliance_once`; `unit/regulation/test_engine_variants.py`: `test_current_variant_is_found_at_each_decision`; `unit/regulation/test_engine_penalty.py`: `test_penalty_ends_with_a_restart_when_paid_back`; `unit/regulation/test_engine_safe_state.py`: `test_regulation_starts_again_when_the_sensor_is_back`; `unit/regulation/test_engine_charging.py`: `test_start_and_stop_deactivate_the_chargers`; `test_regulation.py`: `test_everything_is_turned_off_at_startup`, `test_regulation_starts_when_home_assistant_has_started`, `test_start_waits_for_a_whole_window_after_the_start`, `test_reload_starts_the_regulation_again`, `test_reload_waits_for_the_actions_of_the_old_regulation` |
| REG-010 | `runtime.py`, `websocket_api.py`, panel | black box + manuell | `test_websocket_api.py`: `test_save_is_refused_while_the_regulation_runs`, `test_runtime_refuses_a_new_configuration_while_running`; `test_charging.py`: `test_excluded_switch_stops_charging_and_is_saved` |
| REG-011 | `regulation/engine.py`, `runtime.py` | enhet + black box | `unit/regulation/test_engine_safe_state.py`: `test_lost_power_sensor_turns_everything_off_at_once`, `test_nothing_is_turned_on_in_the_safe_state`, `test_regulation_starts_again_when_the_sensor_is_back`; `test_regulation.py`: `test_safe_state_when_the_power_sensor_is_lost`, `test_regulation_starts_again_when_the_power_sensor_is_back`, `test_safe_state_before_the_first_measurement` |
| REG-012 | `regulation/engine.py`, `regulation/waiting.py` | enhet + black box | `unit/regulation/test_engine_waiting.py`: `test_appliance_is_turned_on_after_the_waiting_time`, `test_no_waiting_time_turns_on_at_the_same_decision`, `test_waiting_time_is_cancelled_when_conditions_fail`; `test_websocket_api.py`: `test_status_shows_the_variant_and_the_waiting_time` |
| REG-013 | `regulation/waiting.py` | enhet | `unit/regulation/test_waiting.py`: `test_linear_waiting_time`; `unit/regulation/test_engine_waiting.py`: `test_zero_average_gives_no_waiting_time`, `test_waiting_time_is_calculated_again_at_each_decision`, `test_waiting_time_close_to_the_limit`, `test_end_of_the_waiting_time_follows_the_average` |
| REG-014 | `config_model.py` | enhet | `unit/test_config_model.py`: `test_defaults_follow_requirements`; `unit/test_config_validation.py`: `test_general_ranges`; `unit/regulation/test_engine_waiting.py`: `test_appliance_is_turned_on_after_the_waiting_time` |
| REG-015 | `regulation/waiting.py` | enhet | `unit/regulation/test_waiting.py`: `test_waiting_time_is_linear_until_persistent_cycling`, `test_waiting_time_on_persistent_cycling_for_appliances`, `test_command_for_another_slot_ends_the_count`; `unit/regulation/test_engine_cycling.py`: `test_waiting_time_grows_on_persistent_cycling`, `test_switching_another_appliance_resets_the_increase` |
| REG-016 | `runtime.py`, `config_model.py`, `switch.py`, `websocket_api.py` | enhet + black box | `unit/regulation/test_engine_switching.py`: `test_stop_turns_off_everything_and_makes_no_decisions`; `unit/test_config_completeness.py`: `test_full_config_is_complete`, `test_appliance_needs_entity_and_both_actions`, `test_charger_needs_entity_actions_and_charge_power_sensor`, `test_car_connected_is_required_with_one_charger_at_a_time`; `test_regulation.py`: `test_everything_is_turned_off_at_startup`, `test_user_start_before_home_assistant_has_started`, `test_stop_turns_everything_off_and_stops_the_decisions`, `test_incomplete_configuration_does_not_start`; `test_websocket_api.py`: `test_set_running_stops_and_starts_like_the_switch`, `test_start_is_refused_while_the_configuration_is_incomplete` |
| STR-001 | `regulation/penalty.py` | enhet + black box | `unit/regulation/test_penalty.py`: `test_penalty_starts_above_limit_plus_threshold`; `unit/regulation/test_engine_penalty.py`: `test_penalty_turns_everything_off_at_once`, `test_no_penalty_at_or_under_limit_plus_threshold`; `test_regulation.py`: `test_penalty_turns_everything_off_until_paid_back` |
| STR-002 | `config_model.py`, `regulation/penalty.py` | enhet | `unit/test_config_model.py`: `test_defaults_follow_requirements`; `unit/test_config_validation.py`: `test_general_ranges`; `unit/regulation/test_penalty.py`: `test_zero_threshold_starts_the_penalty_at_the_next_decision`; `unit/regulation/test_engine_penalty.py`: `test_zero_threshold_gives_penalty_one_decision_later` |
| STR-003 | `regulation/engine.py` | enhet + black box | `unit/regulation/test_engine_penalty.py`: `test_penalty_turns_everything_off_at_once`, `test_nothing_is_turned_on_during_the_penalty`; `unit/regulation/test_engine_charging.py`: `test_penalty_and_safe_state_deactivate_the_chargers`; `test_regulation.py`: `test_penalty_turns_everything_off_until_paid_back` |
| STR-004 | `regulation/penalty.py` | enhet | `unit/regulation/test_penalty.py`: `test_no_overconsumption_at_or_under_the_limit`, `test_overconsumption_starts_at_zero`, `test_overconsumption_state_ends_when_paid_back`, `test_overconsumption_state_starts_again_at_once` |
| STR-005 | `regulation/penalty.py` | enhet | `unit/regulation/test_penalty.py`: `test_overconsumption_is_net_energy_over_the_limit`, `test_every_average_since_the_previous_decision_counts`, `test_energy_follows_the_regulation_window`, `test_penalty_lasts_until_the_overconsumption_is_paid_back` |
| STR-006 | `regulation/penalty.py`, `regulation/engine.py` | enhet + black box | `unit/regulation/test_penalty.py`: `test_penalty_lasts_until_the_overconsumption_is_paid_back`, `test_penalty_does_not_end_when_the_capacity_average_falls`; `unit/regulation/test_engine_penalty.py`: `test_stop_and_start_end_the_penalty`; `unit/regulation/test_engine_safe_state.py`: `test_safe_state_ends_a_penalty`; `test_regulation.py`: `test_penalty_turns_everything_off_until_paid_back` |
| STR-007 | `regulation/penalty.py` | enhet | `unit/regulation/test_penalty.py`: `test_recovery_starts_at_the_first_average_under_the_limit`, `test_recovery_is_not_tracked_outside_a_penalty`; `unit/regulation/test_engine_penalty.py`: `test_status_shows_the_recovery` |
| STR-008 | `regulation/engine.py` | enhet + black box | `unit/regulation/test_engine_penalty.py`: `test_penalty_ends_with_a_restart_when_paid_back`, `test_appliances_come_back_one_by_one_after_the_penalty`, `test_restart_after_the_penalty_waits_again`; `test_regulation.py`: `test_penalty_turns_everything_off_until_paid_back` |
| STR-009 | `regulation/penalty.py` | enhet | `unit/regulation/test_penalty.py`: `test_no_penalty_when_overconsumption_is_paid_back`; `unit/regulation/test_engine_penalty.py`: `test_no_penalty_when_overconsumption_is_paid_back`, `test_appliances_come_back_one_by_one_after_the_penalty` |
| APP-001 | `config_model.py`, `regulation/priority.py`, panel | enhet + black box + manuell | `unit/test_config_validation.py`: `test_missing_priority_entries_are_reported`, `test_duplicate_priority_entry_is_rejected`; `unit/regulation/test_priority.py`: `test_slots_follow_the_priority_list`; `unit/regulation/test_engine_switching.py`: `test_appliances_are_turned_on_one_per_decision_in_priority_order`; `test_websocket_api.py`: `test_config_get_gives_configuration_names_and_missing` |
| APP-002 | `config_model.py`, `actions.py` | enhet + black box | `unit/test_config_completeness.py`: `test_appliance_needs_entity_and_both_actions`; `unit/test_actions.py`: `test_default_actions_call_the_domain_service`; `test_regulation.py`: `test_appliances_are_turned_on_one_per_decision`, `test_custom_action_gets_the_entity_variables` |
| APP-003 | `config_model.py`, `actions.py` | enhet + black box | `unit/test_config_completeness.py`: `test_appliance_needs_entity_and_both_actions`; `unit/test_actions.py`: `test_default_actions_call_the_domain_service`; `test_regulation.py`: `test_everything_is_turned_off_at_startup`, `test_lowest_priority_is_turned_off_above_the_limit` |
| APP-004 | `config_model.py`, `regulation/engine.py` | enhet | `unit/test_config_validation.py`: `test_appliance_power_reserve`; `unit/test_config_completeness.py`: `test_optional_settings_are_not_required`; `unit/regulation/test_engine_switching.py`: `test_power_reserve_must_fit_under_the_limit` |
| APP-005 | `config_model.py`, `regulation/priority.py`, panel | enhet + manuell | `unit/test_config_validation.py`: `test_ev_charging_entry_only_when_charging_is_enabled`, `test_parse_config_adds_ev_charging_when_enabled`; `unit/regulation/test_priority.py`: `test_ev_charging_entry_is_replaced_by_charger_slots` |
| APP-006 | `config_model.py`, `conditions.py`, panel | enhet + black box + manuell | `unit/test_config_validation.py`: `test_variant_condition_must_have_value`, `test_variant_label_must_not_be_empty`, `test_variant_labels_must_be_unique_per_appliance`; `unit/test_config_serialization.py`: `test_full_config_round_trips`; `test_regulation.py`: `test_variant_condition_moves_the_appliance` |
| APP-007 | `regulation/priority.py`, `regulation/engine.py` | enhet + black box | `unit/regulation/test_priority.py`: `test_topmost_true_condition_gives_current_variant`, `test_only_the_current_variant_gets_a_slot`; `unit/regulation/test_engine_variants.py`: `test_current_variant_decides_the_place`, `test_current_variant_is_found_at_each_decision`; `test_regulation.py`: `test_variant_condition_moves_the_appliance`; `test_websocket_api.py`: `test_status_shows_the_variant_and_the_waiting_time` |
| APP-008 | `config_model.py`, panel | enhet + black box + manuell | `unit/test_config_validation.py`: `test_priority_entry_for_unknown_variant_is_rejected`, `test_parse_config_adds_missing_priority_entries_at_bottom`; `test_websocket_api.py`: `test_incomplete_configuration_is_saved` |
| APP-009 | `regulation/engine.py` | enhet | `unit/regulation/test_engine_variants.py`: `test_switch_above_the_lowest_on_makes_room`, `test_appliance_that_was_on_is_switched_off_and_on_again`, `test_switch_restarts_the_waiting_time_of_the_appliance`, `test_switch_resets_the_increasing_waiting_time`, `test_several_switches_are_handled_one_by_one_by_new_place`; `unit/regulation/test_engine_charging.py`: `test_variant_switch_makes_room_by_switching_off_a_fictive_appliance` |
| LAD-001 | `config_model.py`, `regulation/engine.py`, panel | enhet + black box + manuell | `unit/test_config_model.py`: `test_defaults_follow_requirements`; `unit/test_config_completeness.py`: `test_chargers_do_not_count_while_charging_is_disabled`; `unit/regulation/test_engine_charging.py`: `test_chargers_are_left_alone_while_charging_is_disabled`; `test_charging.py`: `test_charger_switches_are_unavailable_while_charging_is_disabled` |
| LAD-002 | `config_model.py`, `regulation/charging.py` | enhet | `unit/test_config_model.py`: `test_defaults_follow_requirements`; `unit/test_config_completeness.py`: `test_car_connected_is_required_with_one_charger_at_a_time`; `unit/regulation/test_charging.py`: `test_one_at_a_time_the_charging_charger_goes_first`, `test_several_at_once_may_all_charge_when_allowed_and_not_bypassed` |
| LAD-003 | `config_model.py`, `regulation/charging.py`, panel | enhet + black box + manuell | `unit/test_config_validation.py`: `test_entity_is_unique_across_appliances_and_chargers`; `unit/regulation/test_charging.py`: `test_priority_starts_as_configured`; `test_charging.py`: `test_charger_switches_are_named_after_the_charger` |
| LAD-004 | `regulation/engine.py`, `actions.py` | enhet + black box | `unit/test_config_completeness.py`: `test_charger_needs_entity_actions_and_charge_power_sensor`; `unit/regulation/test_engine_charging.py`: `test_start_and_stop_deactivate_the_chargers`, `test_current_decreases_one_ampere_per_fictive_appliance`; `unit/test_actions.py`: `test_charger_actions_get_the_current_variables`; `test_charging.py`: `test_charger_current_follows_the_free_power` |
| LAD-005 | `regulation/engine.py`, `actions.py` | enhet + black box | `unit/test_config_completeness.py`: `test_charger_needs_entity_actions_and_charge_power_sensor`; `unit/regulation/test_engine_charging.py`: `test_current_increases_one_ampere_per_fictive_appliance`; `unit/test_actions.py`: `test_charger_actions_get_the_current_variables`; `test_charging.py`: `test_charger_current_follows_the_free_power` |
| LAD-006 | `actions.py` | enhet + black box | `unit/test_actions.py`: `test_current_is_kept_between_min_and_max`, `test_charger_actions_get_the_current_variables`; `test_charging.py`: `test_charger_current_follows_the_free_power` |
| LAD-007 | `config_model.py` | enhet | `unit/test_config_model.py`: `test_charger_defaults`; `unit/test_config_validation.py`: `test_charger_settings`, `test_min_current_may_equal_max`, `test_max_current_must_be_at_least_one`, `test_min_current_above_max_is_rejected` |
| LAD-008 | `regulation/charging.py`, `runtime.py` | enhet | `unit/test_config_completeness.py`: `test_charger_needs_entity_actions_and_charge_power_sensor`; `unit/regulation/test_charging.py`: `test_actively_charging_above_100_watt_or_without_a_valid_value`; `unit/regulation/test_engine_charging.py`: `test_charger_that_does_not_draw_power_is_bypassed` |
| LAD-009 | `config_model.py`, `regulation/priority.py` | enhet | `unit/test_config_model.py`: `test_charger_defaults`; `unit/test_config_validation.py`: `test_charger_settings`; `unit/regulation/test_engine_charging.py`: `test_only_the_first_fictive_appliance_needs_the_power_reserve` |
| LAD-010 | `config_model.py`, `conditions.py` | enhet + black box | `unit/test_config_validation.py`: `test_car_connected_condition`; `unit/test_config_completeness.py`: `test_car_connected_is_required_with_one_charger_at_a_time`; `unit/regulation/test_charging.py`: `test_charger_without_car_is_bypassed`; `test_charging.py`: `test_charger_without_car_is_not_activated` |
| LAD-011 | `regulation/charging.py`, `regulation/priority.py` | enhet | `unit/regulation/test_charging.py`: `test_one_fictive_appliance_per_ampere`, `test_current_follows_the_fictive_appliances_that_are_on`; `unit/regulation/test_priority.py`: `test_fictive_appliances_are_interleaved_between_chargers`; `unit/regulation/test_engine_charging.py`: `test_current_increases_one_ampere_per_fictive_appliance` |
| LAD-012 | `regulation/engine.py`, `regulation/priority.py` | enhet + black box | `unit/regulation/test_priority.py`: `test_only_the_first_fictive_appliance_has_the_power_reserve`; `unit/regulation/test_engine_charging.py`: `test_current_increases_one_ampere_per_fictive_appliance`, `test_only_the_first_fictive_appliance_needs_the_power_reserve`; `test_charging.py`: `test_charger_current_follows_the_free_power` |
| LAD-013 | `regulation/engine.py` | enhet + black box | `unit/regulation/test_engine_charging.py`: `test_current_decreases_one_ampere_per_fictive_appliance`; `test_charging.py`: `test_charger_current_follows_the_free_power` |
| LAD-014 | `regulation/waiting.py` | enhet | `unit/regulation/test_waiting.py`: `test_cycling_steps_are_parameters`; `unit/regulation/test_priority.py`: `test_only_the_first_fictive_appliance_has_the_power_reserve`; `unit/regulation/test_engine_charging.py`: `test_fictive_appliances_cycle_with_their_own_steps` |
| LAD-015 | `regulation/priority.py`, `regulation/charging.py` | enhet | `unit/regulation/test_priority.py`: `test_fictive_appliances_are_interleaved_between_chargers`; `unit/regulation/test_charging.py`: `test_several_at_once_may_all_charge_when_allowed_and_not_bypassed`; `unit/regulation/test_engine_charging.py`: `test_several_chargers_take_turns` |
| LAD-016 | `regulation/charging.py` | enhet + black box | `unit/regulation/test_charging.py`: `test_priority_starts_as_configured`; `unit/regulation/test_engine_charging.py`: `test_current_priority_starts_as_configured_at_each_start`; `test_websocket_api.py`: `test_status_shows_the_chargers_in_the_current_priority` |
| LAD-017 | `regulation/charging.py` | enhet + black box | `unit/regulation/test_charging.py`: `test_charger_without_car_is_bypassed`, `test_charger_that_does_not_draw_power_is_bypassed_after_two_windows`, `test_bypassed_charger_does_not_stand_in_the_way`; `unit/regulation/test_engine_charging.py`: `test_charger_that_does_not_draw_power_is_bypassed`, `test_bypassed_charger_starts_again_when_the_car_draws_power`, `test_bypassed_charger_is_not_switched_off_above_the_limit`; `test_charging.py`: `test_charger_without_car_is_not_activated` |
| LAD-018 | `regulation/charging.py` | enhet + black box | `unit/regulation/test_charging.py`: `test_bypassed_charger_is_no_longer_bypassed_when_a_car_connects`, `test_chargers_bypassed_at_once_keep_their_order_at_the_back`; `unit/regulation/test_engine_charging.py`: `test_bypassed_charger_does_not_stand_in_the_way_one_at_a_time`; `test_websocket_api.py`: `test_status_shows_the_chargers_in_the_current_priority` |
| LAD-019 | `regulation/engine.py` | enhet | `unit/regulation/test_engine_charging.py`: `test_charger_that_does_not_draw_power_is_bypassed`, `test_bypassed_charger_starts_again_when_the_car_draws_power` |
| LAD-020 | `regulation/charging.py` | enhet | `unit/regulation/test_charging.py`: `test_priority_is_corrected_when_a_charger_has_all_fictive_appliances_on`; `unit/regulation/test_engine_charging.py`: `test_priority_is_corrected_when_a_charger_has_all_fictive_appliances_on` |
| LAD-021 | `regulation/charging.py` | enhet | `unit/regulation/test_charging.py`: `test_one_at_a_time_the_charging_charger_goes_first`, `test_one_at_a_time_the_activated_one_of_several_charging_goes_first`; `unit/regulation/test_engine_charging.py`: `test_charging_charger_goes_first_and_the_other_waits` |
| LAD-022 | `regulation/charging.py` | enhet | `unit/regulation/test_charging.py`: `test_one_at_a_time_without_charging_takes_the_first_allowed`; `unit/regulation/test_engine_charging.py`: `test_first_charger_in_the_current_priority_is_chosen` |
| LAD-023 | `regulation/charging.py` | enhet | `unit/regulation/test_charging.py`: `test_one_at_a_time_the_charging_charger_goes_first`, `test_one_at_a_time_charging_charger_not_allowed_keeps_others_waiting`; `unit/regulation/test_engine_charging.py`: `test_charging_charger_goes_first_and_the_other_waits`, `test_charger_without_charging_power_keeps_the_other_waiting` |
| LAD-024 | `regulation/charging.py`, `regulation/engine.py` | enhet + black box | `unit/regulation/test_charging.py`: `test_allowed_to_charge`; `unit/regulation/test_engine_charging.py`: `test_excluded_charger_stops_at_once_and_never_charges`; `test_charging.py`: `test_excluded_switch_stops_charging_and_is_saved` |
| LAD-025 | `config_model.py`, `regulation/charging.py`, panel | enhet + manuell | `unit/test_config_validation.py`: `test_charging_window_start_must_differ_from_end`, `test_charging_window_in_whole_minutes`, `test_charging_window_across_midnight_is_valid`; `unit/regulation/test_charging.py`: `test_charging_window_can_reach_across_midnight`, `test_charging_window_start_is_found_in_the_time_zone`; `unit/regulation/test_engine_charging.py`: `test_charger_charges_only_inside_its_charging_window` |
| LAD-026 | `regulation/charging.py` | enhet | `unit/regulation/test_charging.py`: `test_allowed_to_charge`, `test_override_without_window_or_switched_off_never_ends`; `unit/regulation/test_engine_charging.py`: `test_override_without_window_has_no_effect` |
| LAD-027 | `regulation/charging.py`, `charger_switches.py` | enhet + black box | `unit/regulation/test_charging.py`: `test_override_ends_when_the_next_window_has_started`, `test_override_counts_from_the_switch_also_over_a_later_start`, `test_override_counts_from_the_start_when_switched_on_is_unknown`; `unit/regulation/test_engine_charging.py`: `test_override_allows_charging_until_the_next_window_starts`, `test_override_ends_also_during_a_penalty`, `test_switching_the_override_off_stops_charging_outside_the_window`; `test_charging.py`: `test_window_override_lets_the_charger_charge_until_the_window`, `test_window_override_counts_from_the_switch_over_a_stop` |
| LAD-028 | `regulation/engine.py` | enhet + black box | `unit/regulation/test_engine_charging.py`: `test_start_and_stop_deactivate_the_chargers`, `test_new_car_waits_for_room_for_the_power_reserve`; `test_charging.py`: `test_charger_without_car_is_not_activated` |
| LAD-029 | `regulation/engine.py` | enhet | `unit/regulation/test_engine_charging.py`: `test_bypassed_charger_does_not_stand_in_the_way_one_at_a_time`, `test_charging_charger_goes_first_and_the_other_waits` |
| LAD-030 | `regulation/engine.py` | enhet | `unit/regulation/test_engine_charging.py`: `test_charger_that_does_not_draw_power_is_bypassed`, `test_car_disconnected_limits_the_charger_at_once` |
| ENT-001 | `sensor.py` | black box | `test_sensor.py`: `test_sensors_show_the_averages_in_kw`, `test_sensors_are_updated_once_per_window`, `test_sensors_are_unavailable_before_the_first_average` |
| ENT-002 | `sensor.py` | black box | `test_sensor.py`: `test_sensors_show_the_averages_in_kw`, `test_sensors_are_updated_once_per_window`, `test_capacity_average_over_a_whole_hour_of_updates` |
| ENT-003 | `switch.py`, `charger_switches.py` | enhet + black box | `unit/test_config_model.py`: `test_charger_switches_default_off`; `test_charging.py`: `test_excluded_switch_stops_charging_and_is_saved`, `test_charger_switches_are_kept_over_a_reload`, `test_charger_switches_follow_the_configuration_without_reload`; `test_websocket_api.py`: `test_saved_chargers_get_their_switches` |
| ENT-004 | `switch.py`, `charger_switches.py` | enhet + black box | `unit/test_config_model.py`: `test_charger_switches_default_off`; `unit/regulation/test_engine_charging.py`: `test_override_allows_charging_until_the_next_window_starts`; `test_charging.py`: `test_window_override_lets_the_charger_charge_until_the_window`, `test_charger_switches_are_kept_over_a_reload` |
| ENT-005 | `binary_sensor.py` | black box | `test_regulation.py`: `test_safe_state_when_the_power_sensor_is_lost`, `test_regulation_starts_again_when_the_power_sensor_is_back`, `test_safe_state_before_the_first_measurement` |
| ENT-006 | `switch.py` | black box | `test_regulation.py`: `test_stop_turns_everything_off_and_stops_the_decisions`, `test_incomplete_configuration_does_not_start`, `test_reload_starts_the_regulation_again`; `test_websocket_api.py`: `test_set_running_stops_and_starts_like_the_switch`, `test_status_follows_start_and_stop_from_the_panel_and_the_switch` |
| GUI-001 | `__init__.py`, `websocket_api.py` | black box + manuell | `test_init.py`: `test_setup_and_unload_registers_panel`, `test_panel_is_config_panel_for_integration`; `test_websocket_api.py`: `test_commands_require_an_administrator` |
| GUI-002 | panel (`kraftvakt-panel.ts`) | manuell | – |
| GUI-003 | `__init__.py`, panel | black box + manuell | `test_init.py`: `test_panel_is_config_panel_for_integration` |
| GUI-004 | `config_flow.py` | black box | `test_config_flow.py`: `test_user_flow_creates_entry` |
| GUI-005 | panel (`status-page.ts`), `websocket_api.py` | black box + manuell | `test_websocket_api.py`: `test_config_get_gives_configuration_names_and_missing`, `test_status_is_sent_at_once_and_at_each_window` |
| GUI-006 | panel (`status-page.ts`), `websocket_api.py` | enhet + black box + manuell | `test_websocket_api.py`: `test_status_is_sent_at_once_and_at_each_window`, `test_status_shows_the_variant_and_the_waiting_time`, `test_status_shows_the_chargers`; `unit/regulation/test_charging.py`: `test_status_of_each_charger`; `unit/regulation/test_engine_penalty.py`: `test_status_shows_the_recovery` |
| GUI-007 | panel (`status-page.ts`), `websocket_api.py` | black box + manuell | `test_websocket_api.py`: `test_set_running_stops_and_starts_like_the_switch`, `test_status_follows_start_and_stop_from_the_panel_and_the_switch` |
| GUI-008 | panel (`general-page.ts`), `websocket_api.py` | black box + manuell | `test_websocket_api.py`: `test_capabilities_give_default_actions_limits_and_defaults` |
| GUI-009 | panel (`appliances-page.ts`), `websocket_api.py` | black box + manuell | `test_websocket_api.py`: `test_config_get_gives_configuration_names_and_missing`, `test_invalid_configuration_is_not_saved`, `test_incomplete_configuration_is_saved` |
| GUI-010 | panel (`charging-page.ts`), `websocket_api.py` | black box + manuell | `test_websocket_api.py`: `test_invalid_configuration_is_not_saved`, `test_saved_chargers_get_their_switches` |
| GUI-011 | panel (`manual-control-warning.ts`) | manuell | – |
| GUI-012 | panel (`locked-banner.ts`), `websocket_api.py` | black box + manuell | `test_websocket_api.py`: `test_save_is_refused_while_the_regulation_runs` |

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
17. **MAL-007:** Presiser at en effektsensor uten enhet leses som watt, og at
    andre enheter enn W og kW gir ugyldig måleverdi (T19).
18. **MAL-001:** Presiser at første reguleringsvindu starter når integrasjonen
    starter (T20).
19. **MAL-005/MAL-006/GEN-007:** Presiser at snittene også begynner på nytt når
    effektsensoren var uten gyldig verdi da to vinduer på rad ble lukket, selv
    om reguleringen er stoppet, og at snittsensorene da er utilgjengelige (T21).
20. **APP-009:** Presiser hvordan flere apparater som bytter variant ved samme
    avgjørelse, håndteres (T22).

---

## 11. Åpne spørsmål til eier

Valg som ble tatt underveis i fasene uten å være avklart med eier. Alle ble
avklart med eier 2026-11-08. Endret oppførsel står i kapittel 2 (T13,
T25–T28). Resten er beholdt slik den var. Nedtellingen på statussiden ble i
tillegg rettet (funn i den manuelle testen i fase 10).

| # | Fase | Krav | Oppførsel før avklaringen | Alternativ | Avgjørelse |
|---|---|---|---|---|---|
| Å1 | 4 | STR-003 | Når straff starter, sendes av-kommando til alle apparater og elbilladere i konfigurasjonen, også de som allerede er av (som ved start, REG-009). | Sende av-kommando bare til apparatene og elbilladerne reguleringen har slått på. | Beholdt. |
| Å2 | 4 | APP-007 | Gjeldende variant vurderes også ved avgjørelsene under straff. Alt er av, så et bytte gir ingen kommandoer, men statussiden viser den nye varianten. | Ikke vurdere varianter under straff, og finne gjeldende variant ved første avgjørelse etter straffen. | Beholdt. |
| Å3 | 5 | REG-009 | Når HA starter, slås alt av straks Kraftvakt er lastet. Integrasjonene til apparatene er kanskje ikke lastet ennå. Da feiler av-kommandoene og gjentas ikke (GEN-012). | Vente med starten til HA har startet (`async_at_started`). | Endret til alternativet (T26). |
| Å4 | 5 | GEN-011 | En lagret konfigurasjon som ikke kan leses, gir et unntak, og oppsettet av integrasjonen feiler uten en egen feilmelding. | Feile med en tydelig feilmelding, eller starte med tom konfigurasjon uten å overskrive lagringen. | Endret: tydelig feilmelding, filen endres ikke (T27). |
| Å5 | 5 | REG-009 | Ved reload av integrasjonen kan handlinger fra den gamle runtime-en fortsatt kjøre mens den nye slår alt av. Rekkefølgen mellom dem er da ikke garantert. Lite sannsynlig, og ikke håndtert. | Vente til handlingene fra den gamle runtime-en er ferdige før den nye slår alt av. | Endret til alternativet (T28). |
| Å6 | 6 | LAD-017, LAD-029 | Med én elbillader om gangen og uten innstillingen «bil tilkoblet» blir elbilladere uten bil aktivert etter tur. Den ene blir forbigått etter to reguleringsvinduer, og den neste aktiveres (LAD-029 deaktiverer den første). Den første er da ikke lenger forbigått og står for tur igjen. | Huske at en elbillader er forbigått også etter at den er deaktivert, til en bil kobles til eller den begynner å trekke strøm. Med «bil tilkoblet» konfigurert skjer ikke dette. | Eier valgte først alternativet. Det ville gjort at en deaktivert elbillader aldri ble aktivert igjen uten «bil tilkoblet». Endret i stedet til at «bil tilkoblet» er påkrevd med én om gangen (T25). |
| Å7 | 6 | LAD-027, T13 | Et ladetidsrom som starter mens reguleringen er i sikker tilstand eller stoppet, telles ikke, fordi starten av reguleringen blir nytt referansetidspunkt. Overstyringen varer da til neste dags ladetidsrom. | Regne fra tidspunktet bryteren ble slått på også over sikker tilstand og stopp, og bare bruke starten av reguleringen etter omstart av HA eller integrasjonen. | Endret til alternativet (T13). |
| Å8 | 6 | LAD-017 | En elbillader som ikke lader, kan få flere fiktive apparater slått på i de to reguleringsvinduene før den blir forbigått. Den begrenses så til minste ladestrøm (LAD-030). Med standard ventetid skjer det sjelden. | Ikke slå på flere fiktive apparater før elbilladeren er aktivt ladende. | Beholdt. |
| Å9 | 7 | MAL-005, GEN-007 | Snittene går videre når konfigurasjonen lagres. En ny effektsensor følges fra lagringen, og historikken fra den gamle sensoren blir med i snittforbruket. Et nytt reguleringsvindu gjelder fra neste vindu. | Starte snittene på nytt etter MAL-005 når effektsensoren eller reguleringsvinduet endres. | Beholdt. |
| Å10 | 7 | REG-010 | Valideringsfeil fra `kraftvakt/config/save` sendes som resultat (`{saved: false, errors}`), ikke som WebSocket-feil, fordi HAs feilmelding ikke kan bære data. | WebSocket-feil med feilene i meldingsteksten. | Beholdt. |
| Å11 | 7 | GEN-013, T18 | Valideringsfeil kommer i to omganger. Feil i type og format må rettes før `default_action_unavailable` vises, fordi den sjekken trenger en lesbar konfigurasjon. | Gi alle feil samtidig, med en enklere sjekk av standardhandlinger som tåler en uferdig konfigurasjon. | Beholdt. |
| Å12 | 7 | REG-010 | `regulation_running` sjekkes før valideringen. Mens reguleringen kjører, får brukeren derfor ikke vite om konfigurasjonen er gyldig. | Validere først og avvise lagringen etterpå. | Beholdt. |
| Å13 | 7 | GUI-006, T11 | `waiting_until` i statusbildet gis også for elbilladere, og gjelder da neste fiktive apparat. | Bare gi ventetid for vanlige apparater. | Beholdt. |
| Å14 | 9 | GUI-008–010, B7 | Panelet sjekker utkastet mot grensene og regner ut mangler selv før lagring, i tillegg til valideringen i backend. «Lagre» er deaktivert så lenge utkastet har slike feil. | Bare vise feilene fra backend etter at brukeren har trykket «Lagre». | Beholdt. |
| Å15 | 9 | B7 | Panelet spør før ulagrede endringer forkastes bare når brukeren går til statussiden, og nettleseren spør når siden lukkes eller lastes på nytt. Navigering i HAs sidemeny kan ikke stoppes, så utkastet går da tapt uten spørsmål. | Lagre utkastet i nettleseren og hente det frem igjen når panelet åpnes. | Beholdt. |
| Å16 | 9 | REG-010, GUI-007 | Et ulagret utkast forkastes når reguleringen startes, siden det ikke kan lagres mens den kjører. | Spørre før reguleringen startes, eller beholde utkastet til reguleringen stoppes igjen. | Beholdt. Panelet har «Start regulering» bare på statussiden, og spør allerede før ulagrede endringer forkastes når brukeren går dit. Bare start med bryteren forkaster utkastet uten spørsmål. |
| Å17 | 9 | GEN-009 | Velgeren for boolsk entitet (varianter og bil tilkoblet) viser bare domenene `binary_sensor`, `input_boolean`, `switch` og `schedule`. | Tillate alle entiteter, siden alle andre tilstander enn `on` uansett regnes som usann. | Beholdt. |
| Å18 | 9 | GEN-013 | Når brukeren velger egendefinert handling, er den fylt ut med standardhandlingen for entitetens domene. | Starte med en tom handling. | Beholdt. |
| Å19 | 9 | GUI-009, GUI-010 | Mangler (påkrevde felt) vises ikke i dialogen før et nytt apparat eller en ny elbillader er lagt til. En ny variant starter som mal. | Vise mangler med en gang, og la en ny variant starte som entitet. | Beholdt. |
