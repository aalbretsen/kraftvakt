# Kraftvakt – Kravspesifikasjon

Prioritert effektstyring for Home Assistant.

Dokumentstatus: Utkast til første versjon. Kravene kan endres, flyttes og omnummereres fritt til første versjon er godkjent.

## 1. Innledning

### 1.1 Formål med dokumentet

Dokumentet beskriver kravene til Kraftvakt. Det skal gi utvikleren nok forståelse av helheten til å utvikle løsningen ut fra kravene alene. Dokumentet beskriver *hva* løsningen skal gjøre, ikke *hvordan*.

### 1.2 Konvensjoner

- Kravene følger prinsippene i ISO/IEC/IEEE 29148: hvert krav er entydig, verifiserbart og uttrykker behov, ikke løsning.
- **skal** = obligatorisk krav. **bør** = ønsket krav.
- Krav-ID har formen `KATEGORI-NNN`. ID-ene låses når første versjon er godkjent.
- Kravene er ordnet i kravgrupper. Hver gruppe starter med en kort beskrivelse av sammenhengen.
- **Begrunnelse** forklarer hvorfor kravet finnes, der det er kjent.
- **Relatert** lister krav som påvirker eller påvirkes av kravet.
- `[AVKLARES: ÅS-nn]` betyr at kravet avhenger av et åpent spørsmål i kapittel 5.
- Navn på entiteter og parametere er arbeidsnavn.
- Begrepene i kapittel 3 beskriver konseptene generelt og skal kunne stå for seg selv.

### 1.3 Kategorier

| Kode | Kategori |
|---|---|
| GEN | Generelt og rammebetingelser |
| SPR | Språk |
| MAL | Måling og snittberegning |
| REG | Regulering |
| STR | Straffeperiode |
| APP | Apparater og prioritetsliste |
| LAD | Elbillading |
| ENT | Eksponerte entiteter |
| GUI | Konfigurasjonsgrensesnitt |

## 2. Helhetsbeskrivelse

### 2.1 Bakgrunn

Norske nettselskaper beregner kapasitetsleddet i nettleien ut fra timene i måneden med høyest forbruk. Å holde gjennomsnittseffekten i hver time under en valgt grense hindrer at husstanden havner på et dyrere trinn.

### 2.2 Virkemåte sett utenfra

- Brukeren setter en effektgrense, for eksempel 10 kW, som tilsvarer høyst 10 kWh forbruk i løpet av en time. Reguleringen prøver hele tiden å holde forbruket rett under effektgrensen.
- Kraftvakt styrer bare apparater som kan vike for annet forbruk, typisk oppvarming og billading. Apparater som ikke kan vente, som stekeovn, styres ikke. Forbruket deres inngår likevel i totalen. Når for eksempel middagen lages, viker de styrte apparatene. Resten av døgnet kan de bruke strøm som vanlig.
- Brukeren ordner de styrte apparatene i en prioritert liste. Eksempler er varmtvannsbereder og varmekabler.
- Et apparat får være på så lenge det er nok ledig effekt til det under effektgrensen. Apparater slås på ett og ett, i fast prioritert rekkefølge.
- Når forbruket går over effektgrensen, slås det lavest prioriterte apparatet av med en gang.
- Kraftvakt bruker to glidende gjennomsnitt:
  - *Reguleringssnittet* er et kort gjennomsnitt over reguleringsvinduet, som standard ett minutt. Det jevner ut målingene, slik at apparater ikke slås av og på unødig ofte. Det brukes til å finne ledig effekt og til å avgjøre om et apparat kan slås på eller må slås av.
  - *Snittforbruket* er gjennomsnittet over kapasitetsvinduet, som tilsvarer tidsrommet nettselskapet måler forbruket over for å fastsette kapasitetsleddet. I dag er det gjennomsnittet for siste time. Å holde snittforbruket under effektgrensen er det endelige målet. Reguleringen styrer ikke etter dette snittet, slik at den kan være i forkant. Snittforbruket overvåkes likevel, slik at straff kan iverksettes hvis reguleringen har feilet.
- En ventetid før et apparat slås på igjen hindrer at det samme apparatet slås av og på gang på gang. Målet med ventetiden er at straff aldri skal bli nødvendig.
- Straffen er en sikkerhetsventil. Går snittforbruket klart over effektgrensen, inntrer en straffeperiode. Alle apparater som reguleringen har slått på, holdes da av til overforbruket er hentet inn med et like stort redusert forbruk.
- Elbilladere håndteres spesielt. Ladestrømmen økes etter hvert som det blir ledig effekt og reduseres når det trengs, på samme måte som flere varmekabler slås på etter hvert.
- Hver elbillader kan begrenses til et ladetidsrom, for eksempel om natten når nettleien er lavere. Brukeren kan overstyre tidsrommet og tillate lading midt på dagen, uten at det gjelder neste dag.

### 2.3 Avgrensninger

- Kraftvakt leser ikke strømmåleren selv, men bruker en sensor fra en annen integrasjon, typisk fra HAN-porten.
- Kraftvakt vet ikke hvor mye et apparat faktisk bruker, for eksempel på grunn av en innebygd termostat. Kraftvakt bestemmer bare om det er ledig kapasitet til at apparatet kan være på, og forsøker aldri å anslå et apparats forbruk.
- Kraftvakt kjører helt lokalt, uten skytjenester.

### 2.4 Sammenheng mellom kravgruppene

| Kravgruppe | Bygger på | Brukes av |
|---|---|---|
| MAL – snittberegning | GEN-003 | REG, STR, ENT |
| REG – regulering | MAL, APP | STR, LAD |
| STR – straffeperiode | MAL, REG | APP, LAD |
| APP – prioritetsliste | – | REG, STR, LAD |
| LAD – elbillading | APP, REG | ENT |

## 3. Begreper

| Begrep | Betydning |
|---|---|
| Effektgrense | Høyeste tillatte effekt, og målet reguleringen etterstreber. Tilsvarer ønsket trinn i kapasitetsleddet i nettleietariffen. Reguleringen prøver hele tiden å holde forbruket rett under effektgrensen. |
| Effektsensor | Sensor fra en annen integrasjon som måler husets totale momentane effekt. |
| Reguleringsvindu | Kort glidende vindu som reguleringssnittet beregnes over. |
| Reguleringssnitt | Gjennomsnitt av effektsensoren over reguleringsvinduet. Snittet som styrer reguleringen: grunnlaget for ledig effekt og alle beslutninger om å slå apparater av og på. |
| Ledig effekt | Effektgrensen minus reguleringssnittet. |
| Kapasitetsvindu | Glidende vindu som tilsvarer tidsrommet nettselskapet måler forbruket over for å fastsette kapasitetsleddet. Med dagens tariff er det derfor et glidende vindu som måler gjennomsnittet én time tilbake i tid. |
| Snittforbruk | Gjeldende gjennomsnittlig forbruk over kapasitetsvinduet, i dag gjennomsnittet for siste time. Det endelige målet er at snittforbruket holdes under effektgrensen. Snittforbruket overvåkes for å kunne iverksette straff. |
| Effektreserve | Ledig effekt som må være tilgjengelig før et apparat kan slås på. |
| Apparat | En enhet som Kraftvakt kan slå av og på. |
| Prioritetsliste | Sortert liste over apparater. Øverst står apparatet med høyest prioritet, det vil si det som sist blir tvangsslått av. |
| Ventetid | Tid som må gå før reguleringen kan slå på et apparat. Skal dempe reguleringen, slik at apparater ikke slås av og på unødig ofte. |
| Vedvarende pendling | At reguleringen gang på gang slår det samme apparatet av og på, uten at andre apparater styres i mellomtiden. |
| Straffeterskel | Forbruk over effektgrensen som snittforbruket må overstige før en straffeperiode starter. |
| Overforbruk | Forbruk over effektgrensen som har ført til at snittforbruket har gått over effektgrensen. |
| Innhenting | Reduksjon i forbruk som må oppnås før reguleringen kan starte igjen etter at straff er iverksatt. |
| Straffeperiode | Tidsrom der regulerte apparater holdes av for å hente inn et overforbruk. |
| Aktivt ladende elbillader | Elbillader som faktisk lader bilen og forbruker strøm. |
| Ventende elbillader | I modus for én elbillader om gangen: elbillader med tilkoblet bil som ikke får lade fordi en annen elbillader lader aktivt. |
| Ladetidsrom | Tidsrom i døgnet der en elbillader har lov til å lade. |
| Overstyring av ladetidsrom | Midlertidig tillatelse til å lade utenfor ladetidsrommet, frem til neste ladetidsrom starter. |

## 4. Krav

### 4.1 GEN – Generelt og rammebetingelser

Grunnrammene for hele løsningen.

**GEN-001 Formål**
Kraftvakt skal være en integrasjon for Home Assistant. Den skal styre hvilke apparater som får være på, i prioritert rekkefølge, slik at snittforbruket holdes under effektgrensen.
Begrunnelse: Unngå et dyrere trinn i kapasitetsleddet i nettleien.
Relatert: REG, STR, APP.

**GEN-002 Lokal drift**
Løsningen skal kjøre helt lokalt i Home Assistant, uten skytjenester eller eksterne datakilder.

**GEN-003 Effektsensor**
Løsningen skal hente husets totale effekt fra en effektsensor levert av en annen integrasjon. Brukeren skal kunne velge sensoren. Løsningen skal ikke lese strømmåleren selv.
Relatert: MAL-001, MAL-003, GUI-002.

**GEN-004 Kun av/på-styring**
Løsningen skal bare avgjøre om et apparat har lov til å være på. Den skal ikke forutsette at apparatets faktiske forbruk er kjent eller styrbart. For elbilladere styres ladestrømmen gjennom fiktive apparater for elbillader (LAD-011).
Relatert: GEN-005, APP-004, LAD-011.

**GEN-005 Ingen anslag av apparatforbruk**
Løsningen skal aldri beregne eller anslå hva et apparat bruker ut fra endringer i totalforbruket etter at apparatet er slått på.
Begrunnelse: Et apparat bruker ikke nødvendigvis strøm selv om det får lov, og andre forbrukere kan starte samtidig.
Relatert: GEN-004, REG-003.

### 4.2 SPR – Språk

**SPR-001 Standardspråk**
Engelsk skal være standardspråk.

**SPR-002 Flerspråklig støtte**
Løsningen skal støtte flere språk.
Relatert: SPR-001, SPR-003.

**SPR-003 Norsk**
Norsk skal leveres som første oversettelse i tillegg til engelsk.

### 4.3 MAL – Måling og snittberegning

Løsningen bruker to glidende gjennomsnitt av effektsensoren. Reguleringssnittet er kort og styrer den løpende reguleringen. Snittforbruket viser forbruket over kapasitetsvinduet, i dag siste time. Det brukes til å avgjøre om reguleringen holder seg innenfor effektgrensen, og til å styre straffen.

**MAL-001 Reguleringssnitt**
Løsningen skal beregne reguleringssnittet som et glidende gjennomsnitt av effektsensoren over reguleringsvinduet.
Begrunnelse: Jevne ut målingene, slik at kortvarige topper ikke fører til at apparater slås av og på hele tiden.
Relatert: MAL-002, REG-002, ENT-001.

**MAL-002 Reguleringsvindu**
Reguleringsvinduet skal kunne konfigureres i sekunder. Standard er 60 sekunder, og gyldig område er 10–600 sekunder.
Relatert: MAL-001, LAD-018, GUI-002.

**MAL-003 Snittforbruk**
Løsningen skal beregne snittforbruket som et glidende gjennomsnitt av effektsensoren over kapasitetsvinduet, én time tilbake i tid.
Begrunnelse: Et glidende vindu gjør det mulig å oppdage med en gang når snittforbruket går over effektgrensen, og å rette opp et overforbruk fortløpende. Med faste klokketimer kan et overforbruk midt i timen bare rettes opp ved å kutte strømmen resten av timen.
Relatert: MAL-004, REG-006, STR-001, STR-004, ENT-002.

**MAL-004 Fast kapasitetsvindu**
Kapasitetsvinduet skal være fast én time og skal ikke kunne konfigureres av brukeren.
Begrunnelse: Vinduet skal samsvare med nettleietariffen, som i dag måles per time. Et fast vindu gjør også oppsettet enklere.
Relatert: MAL-003.

**MAL-005 Hyppige oppdateringer**
Snittberegningene skal gi korrekt resultat når effektsensoren oppdateres hvert sekund, gjennom hele kapasitetsvinduet.
Relatert: MAL-001, MAL-003.

**MAL-006 Sjeldne oppdateringer**
Snittberegningene skal gi korrekt resultat når effektsensoren oppdateres hvert 10. sekund eller sjeldnere.
Begrunnelse: HAN-porten krever minst én oppdatering hvert 10. sekund, men noen målere oppdaterer sjeldnere.
Relatert: MAL-001, MAL-003.

### 4.4 REG – Regulering

Den løpende reguleringen avgjør når apparater slås på og av. Den bruker reguleringssnittet (MAL-001) og prioritetslisten (APP-001). Apparater slås alltid av så snart forbruket er over effektgrensen. Ventetiden gjelder bare når et apparat skal slås på, og skal hindre at straffen (STR) må inntre.

**REG-001 Effektgrense**
Effektgrensen skal kunne konfigureres. Standard er 10 kW, og gyldig område er 1–50 kW.
Relatert: REG-003, REG-005, STR-001, GUI-002.

**REG-002 Grunnlag for beslutninger**
Alle beslutninger om å slå apparater av og på skal bygge på reguleringssnittet, ikke på momentan effekt.
Relatert: MAL-001.

**REG-003 Vilkår for å slå på et apparat**
Et apparat skal bare slås på når reguleringssnittet er under effektgrensen. Er effektreserve satt for apparatet, skal i tillegg reguleringssnittet pluss effektreserven være mindre enn eller lik effektgrensen.
Relatert: REG-001, APP-004, LAD-012.

**REG-004 Fast rekkefølge når apparater slås på**
Apparater skal slås på ett om gangen, i fast prioritert rekkefølge med høyest prioritet først. Et apparat skal ikke slås på før alle apparater med høyere prioritet er på, selv om det ville hatt nok ledig effekt. Apparater som ikke er en del av reguleringen, eller som ikke har lov til å være på, hoppes over.
Relatert: REG-003, REG-006, APP-001, LAD-021, LAD-022.

**REG-005 Utkobling ved overskridelse**
Når reguleringssnittet er over effektgrensen, skal det lavest prioriterte apparatet som er på, slås av med en gang, uten ventetid.
Relatert: REG-001, APP-001, LAD-013.

**REG-006 Lineær ventetid**
Ventetiden før et apparat kan slås på, skal beregnes lineært ut fra forholdet mellom reguleringssnittet og effektgrensen. Et reguleringssnitt på 0 gir ingen ventetid. Et reguleringssnitt lik eller over effektgrensen gir en ventetid lik ventetid ved effektgrensen (REG-007). Ventetiden blir aldri lengre enn dette. Eksempel med standardverdiene: med reguleringssnitt 5 kW, effektgrense 10 kW og ventetid ved effektgrensen 5 minutter blir ventetiden 2,5 minutter.
Begrunnelse: Hindre at det lavest prioriterte apparatet slås av og på gjentatte ganger med korte mellomrom, og dermed hindre at straffen må inntre.
Relatert: REG-004, REG-007, REG-008, MAL-001.

**REG-007 Ventetid ved effektgrensen**
Ventetid ved effektgrensen skal kunne konfigureres i minutter. Standard er 5 minutter, og gyldig område er 0–10 minutter.
Begrunnelse: Øvre grense på 10 minutter gir rom for økende ventetid ved vedvarende pendling (REG-008).
Relatert: REG-006, REG-008, GUI-002.

**REG-008 Økende ventetid ved vedvarende pendling**
Ved vedvarende pendling for samme apparat skal ventetiden før apparatet slås på igjen starte på ventetid ved effektgrensen (REG-007) og øke med 2 minutter hver gang apparatet slås på igjen, opp til høyst 15 minutter. Vedvarende pendling regnes fra og med andre gang det samme apparatet slås på igjen uten at noe annet apparat er slått av eller på i mellomtiden. Økningen skal nullstilles så snart et annet apparat slås av eller på. Økningen og taket skal ikke kunne konfigureres. For elbilladere gjelder egne verdier (LAD-014). Apparatet skal fortsatt slås av med en gang etter REG-005.
Eksempel med standardverdien for ventetid ved effektgrensen: ventetiden blir 5, 7, 9, 11, 13 og deretter 15 minutter.
Begrunnelse: Vedvarende pendling viser at apparatet bruker mer enn den ledige effekten gir rom for.
Relatert: REG-005, REG-006, REG-007, LAD-014.

### 4.5 STR – Straffeperiode

Straffeperioden er en sikkerhetsventil for tilfeller der den løpende reguleringen ikke har klart å holde snittforbruket under effektgrensen. Overforbruket måles som netto forbruk over effektgrensen, regnet fra tidspunktet snittforbruket gikk over effektgrensen. Har reguleringen allerede hentet seg inn når straffen skulle ha startet, inntrer ingen straff. Ellers holdes forbruket nede til en like stor reduksjon i forbruk er oppnådd.

**STR-001 Utløsning av straff**
En straffeperiode skal starte når snittforbruket er høyere enn effektgrensen pluss straffeterskelen, med unntaket i STR-008.
Relatert: MAL-003, REG-001, STR-002, STR-008.

**STR-002 Straffeterskel**
Straffeterskelen skal kunne konfigureres som forbruk over effektgrensen. Standard er 1 kW, og gyldig område er 0–10 kW. Verdien 0 betyr at straffen starter straks snittforbruket overstiger effektgrensen.
Relatert: STR-001, GUI-002.

**STR-003 Apparater under straff**
Under straffeperioden skal alle apparater som reguleringen har slått på, være avslått. Dette gjelder også elbilladere.
Relatert: APP-002, LAD-013.

**STR-004 Måling av overforbruk**
Løsningen skal måle overforbruket som netto forbruk over effektgrensen, regnet fra tidspunktet snittforbruket gikk over effektgrensen. Forbruk under effektgrensen i samme tidsrom skal trekkes fra.
Begrunnelse: Straffen skal ha riktig størrelse, uavhengig av hvor raskt forbruket faller etter overskridelsen.
Relatert: MAL-003, STR-005, STR-008.

**STR-005 Varighet av straff**
Løsningen skal selv beregne hvor lenge straffeperioden varer. Straffen skal vare til innhentingen er like stor som overforbruket.
Begrunnelse: Straffen skal hente inn overforbruket, slik at snittforbruket ikke overstiger effektgrensen.
Relatert: STR-004, STR-006.

**STR-006 Start av innhenting**
Innhentingen skal ikke starte før reguleringssnittet igjen er under effektgrensen.
Relatert: STR-005, MAL-001.

**STR-007 Oppstart etter straff**
Etter straffeperioden skal reguleringen starte med alle regulerte apparater avslått, og slå dem på ett og ett etter REG-003 og REG-004.
Relatert: REG-003, REG-004.

**STR-008 Ingen straff når overforbruket er hentet inn**
En straffeperiode skal ikke starte hvis overforbruket allerede er null eller mindre når vilkåret i STR-001 er oppfylt.
Begrunnelse: Reguleringen kan ha hentet seg inn selv. Da er straffen unødvendig.
Relatert: STR-001, STR-004.

### 4.6 APP – Apparater og prioritetsliste

Prioritetslisten bestemmer i hvilken rekkefølge apparater slås på og av. Den inneholder vanlige apparater og, når billading er aktivert, elementet «Elbillading».

**APP-001 Prioritetsliste**
Apparatene skal konfigureres i en sorterbar prioritetsliste. Øverste apparat har høyest prioritet.
Relatert: REG-004, REG-005, APP-005, GUI-003.

**APP-002 Handling for å slå på**
Hvert apparat skal ha en konfigurerbar handling som slår det på.

**APP-003 Handling for å slå av**
Hvert apparat skal ha en konfigurerbar handling som slår det av.

**APP-004 Effektreserve**
Hvert apparat skal kunne ha en valgfri effektreserve, uten grenseverdier. Er den ikke angitt, gjelder bare det første vilkåret i REG-003.
Begrunnelse: Et apparat som trekker mye straks det slås på, for eksempel en bassengvarmer på 4 kW, kan ellers bli slått på når det er for lite ledig effekt. Da slås det av og på gjentatte ganger og kan over tid utløse straff. For mange apparater er forbruket ukjent, så verdien kan ikke kreves.
Relatert: REG-003.

**APP-005 Elbillading i prioritetslisten**
Når billadestyring er aktivert, skal prioritetslisten inneholde elementet «Elbillading». Det skal kunne sorteres som et vanlig apparat, men ikke konfigureres fra listen. Plasseringen bestemmer hvor i prioritetsrekkefølgen alle de fiktive apparatene for elbilladerne ligger.
Relatert: APP-001, LAD-001, LAD-011.

### 4.7 LAD – Elbillading

En elbillader håndteres spesielt. Brukeren forholder seg til én elbillader, men for reguleringen deles den internt opp i fiktive apparater for elbillader, ett for hvert ampere i ladestrømmen. De generelle reglene for apparater (REG) gjelder for hvert fiktivt apparat. Løsningen kan styre én elbillader om gangen eller flere samtidig. Hver elbillader kan begrenses til et ladetidsrom, som brukeren kan overstyre.

#### 4.7.1 Felles innstillinger

**LAD-001 Aktivering av billadestyring**
Billadestyring skal kunne aktiveres og deaktiveres.
Relatert: APP-005, GUI-004.

**LAD-002 Én elbillader om gangen**
Det skal kunne velges om bare én elbillader kan lade om gangen. Standard er ja.
Relatert: LAD-015, LAD-016, LAD-017, LAD-018, LAD-019.

**LAD-003 Elbilladerliste**
Elbilladerne skal konfigureres i en sorterbar liste der rekkefølgen er prioriteten, med høyest prioritet øverst.
Relatert: LAD-015, LAD-016, LAD-017, GUI-004.

#### 4.7.2 Innstillinger per elbillader

**LAD-004 Deaktivering av elbillader**
Hver elbillader skal ha en konfigurerbar handling som deaktiverer den, slik at den ikke starter lading selv om en bil er tilkoblet.
Relatert: LAD-013, LAD-019.

**LAD-005 Aktivering av elbillader**
Hver elbillader skal ha en konfigurerbar handling som aktiverer den.

**LAD-006 Innstilling av ladestrøm**
Hver elbillader skal ha en konfigurerbar handling som setter ladestrømmen i ampere. Løsningen skal oppgi ampereverdien som en parameter som handlingen kan bruke i en mal.
Relatert: LAD-011, LAD-012, LAD-013.

**LAD-007 Grenser for ladestrøm**
Hver elbillader skal ha en konfigurerbar minste og største tillatte ladestrøm i ampere.
Relatert: LAD-011.

**LAD-008 Ladeeffekt**
Hver elbillader skal ha en konfigurerbar sensor for målt ladeeffekt. En elbillader regnes som aktivt ladende når ladeeffekten er over 100 W.
Relatert: LAD-016, LAD-017, LAD-018.

**LAD-009 Effektreserve for elbillader**
Hver elbillader skal ha en konfigurerbar effektreserve: effekten elbilladeren trekker når lading starter på minste ladestrøm. Standard er 4 kW, og gyldig område er 0–5 kW. Verdien 0 betyr at elbilladeren kan starte så snart det er ledig effekt.
Begrunnelse: Verdien kan ikke beregnes, fordi ladestandarden bare angir grenser i ampere og effekten avhenger av antall faser og spenning. 4 kW tilsvarer omtrent 6 A på tre faser, 400 V.
Relatert: LAD-012, LAD-015, GUI-004.

**LAD-010 Bil tilkoblet**
Hver elbillader skal kunne ha en valgfri verdi for om en bil er tilkoblet. Verdien skal kunne angis som en entitet eller en mal som gir sann/usann. Er verdien ikke angitt, skal den ikke påvirke reguleringen.
Relatert: LAD-018, LAD-019.

#### 4.7.3 Fiktive apparater for elbillader

**LAD-011 Fiktive apparater for elbillader**
Løsningen skal internt dele hver elbillader opp i fiktive apparater for elbillader, ett for hvert heltall i ampere fra minste til største ladestrøm. Reguleringen skal behandle hvert fiktivt apparat som et apparat. De fiktive apparatene er gitt av elbilladerens egenskaper og skal ikke kunne prioriteres eller konfigureres av brukeren.
Relatert: APP-005, LAD-007, LAD-012, LAD-013, LAD-015.

**LAD-012 Økning av ladestrøm**
Ladestrømmen skal økes med ett ampere for hvert fiktivt apparat som slås på. Når det første fiktive apparatet slås på, skal elbilladeren aktiveres med minste ladestrøm. Effektreserven for det første fiktive apparatet er elbilladerens effektreserve (LAD-009). Øvrige fiktive apparater skal ikke ha effektreserve.
Relatert: REG-003, LAD-005, LAD-006, LAD-009, LAD-014.

**LAD-013 Reduksjon av ladestrøm**
Ladestrømmen skal reduseres med ett ampere for hvert fiktivt apparat som slås av. Når det siste fiktive apparatet slås av, skal elbilladeren deaktiveres.
Relatert: REG-005, STR-003, LAD-004, LAD-006.

**LAD-014 Ventetid for fiktive apparater**
Kravene til ventetid (REG-006, REG-007) og økende ventetid ved vedvarende pendling (REG-008) skal gjelde for hvert fiktivt apparat i en elbillader, på samme måte som for andre apparater, med disse unntakene ved vedvarende pendling:
- ventetiden skal øke med 5 minutter for hver gang, ikke 2 minutter, og
- ventetiden skal være høyst 30 minutter, ikke 15 minutter.

Eksempel med standardverdien for ventetid ved effektgrensen: ventetiden blir 5, 10, 15, 20, 25 og deretter 30 minutter.

Begrunnelse: Elbilen skal få så stabil strømtilførsel som mulig, ikke en ladestrøm som stadig endres.
Relatert: LAD-011, LAD-012, LAD-013, REG-006, REG-007, REG-008.

**LAD-015 Flere elbilladere samtidig**
Når flere elbilladere kan lade samtidig, skal de fiktive apparatene fordeles i tur mellom elbilladerne. Først får hver elbillader sitt første fiktive apparat slått på i elbilladerlistens rekkefølge, deretter sitt andre, og så videre. Eksempel med tre elbilladere: elbillader 1 apparat 1, elbillader 2 apparat 1, elbillader 3 apparat 1, elbillader 1 apparat 2, og så videre. Effektreserven skal gjelde for hver elbilladers første fiktive apparat.
Relatert: LAD-002, LAD-003, LAD-009, LAD-011.

#### 4.7.4 Én elbillader om gangen

**LAD-016 Aktivt ladende elbillader går foran**
Når bare én elbillader kan lade om gangen, skal en aktivt ladende elbillader få fortsette å lade så lenge den lader, uansett prioritet.
Relatert: LAD-002, LAD-008, LAD-017, LAD-019.

**LAD-017 Valg av elbillader**
Når bare én elbillader kan lade om gangen og ingen elbillader lader aktivt, skal prioriteten i elbilladerlisten avgjøre hvilken elbillader som først får slått på sine fiktive apparater.
Relatert: LAD-003, LAD-016, LAD-018.

**LAD-018 Elbillader som ikke lader, blokkerer ikke**
Når bare én elbillader kan lade om gangen, skal en elbillader som ikke lader, ikke hindre at en elbillader med lavere prioritet får lade. Elbilladeren skal forbigås når ett av disse vilkårene er oppfylt:
- verdien for bil tilkoblet (LAD-010) er usann, eller
- elbilladeren ikke har vært aktivt ladende i en periode på to ganger reguleringsvinduet etter at dens første fiktive apparat ble slått på.

Er verdien for bil tilkoblet ikke angitt, gjelder bare det siste vilkåret.
Begrunnelse: Ellers stopper all lading opp når den høyest prioriterte elbilladeren står uten bil. En bil kan også være tilkoblet uten å trekke strøm, for eksempel med fullt batteri eller når den står ubrukt i garasjen i flere dager.
Relatert: LAD-002, LAD-008, LAD-010, LAD-017, LAD-020, MAL-002.

**LAD-019 Ventende elbillader**
Når bare én elbillader kan lade om gangen og en elbillader lader aktivt, skal en bil som kobles til en annen elbillader, ikke få lade. Den ventende elbilladeren skal ikke få lade før den aktivt ladende elbilladeren slutter å lade, fordi bilen er koblet fra eller ferdig ladet. Dette gjelder uansett elbilladerlistens rekkefølge.
Relatert: LAD-002, LAD-004, LAD-010, LAD-016.

**LAD-020 Nytt forsøk for forbigått elbillader**
En elbillader som er forbigått etter LAD-018, skal forsøkes igjen når elbilladeren som gikk foran, ikke lenger lader aktivt eller ikke lenger har tilkoblet bil.
Relatert: LAD-017, LAD-018.

#### 4.7.5 Del av reguleringen og ladetidsrom

**LAD-021 Elbillader utenfor reguleringen**
Når en elbillader ikke er en del av reguleringen (ENT-003), skal ingen av dens fiktive apparater slås på, og bilen skal aldri lades.
Relatert: ENT-003, REG-004.

**LAD-022 Ladetidsrom**
Hver elbillader skal kunne ha ett valgfritt ladetidsrom i døgnet. Ladetidsrommet skal kunne strekke seg over midnatt. Utenfor ladetidsrommet skal elbilladeren ikke lade, og pågående lading skal stoppes når ladetidsrommet slutter.
Begrunnelse: Gjøre det mulig å lade bare om natten, når nettleien er lavere.
Relatert: LAD-023, LAD-024, REG-004, GUI-004.

**LAD-023 Uten ladetidsrom**
En elbillader uten angitt ladetidsrom skal alltid ha lov til å lade, med mindre den ikke er en del av reguleringen (ENT-003).
Relatert: LAD-021, LAD-022, ENT-003.

**LAD-024 Overstyring av ladetidsrom**
Når overstyring er slått på for en elbillader (ENT-004), skal den ha lov til å lade også utenfor ladetidsrommet. Overstyringen skal opphøre automatisk når neste ladetidsrom starter, slik at den ikke gjelder neste dag.
Begrunnelse: Gjøre det mulig å tillate lading midt på dagen ved behov.
Relatert: LAD-022, ENT-004.

### 4.8 ENT – Eksponerte entiteter

**ENT-001 Sensor for reguleringssnitt**
Reguleringssnittet skal eksponeres som en sensor som andre integrasjoner og dashbord kan bruke.
Relatert: MAL-001.

**ENT-002 Sensor for snittforbruk**
Snittforbruket skal eksponeres som en sensor som andre integrasjoner og dashbord kan bruke.
Relatert: MAL-003.

**ENT-003 Elbillader i reguleringen**
For hver elbillader skal løsningen lage en entitet som brukeren kan slå av og på, og som bestemmer om elbilladeren er en del av reguleringen. Er den slått av, skal bilen aldri lades.
Relatert: LAD-021, LAD-023.

**ENT-004 Overstyring av ladetidsrom**
For hver elbillader skal løsningen lage en entitet som brukeren kan slå av og på, og som overstyrer ladetidsrommet.
Relatert: LAD-024.

### 4.9 GUI – Konfigurasjonsgrensesnitt

**GUI-001 Eget panel**
Løsningen skal konfigureres fra et eget panel i sidemenyen i Home Assistant.

**GUI-002 Generelle parametere**
Disse parameterne skal være samlet i en egen seksjon: effektsensor (GEN-003), effektgrense (REG-001), reguleringsvindu (MAL-002), ventetid ved effektgrensen (REG-007) og straffeterskel (STR-002).

**GUI-003 Prioritetsliste**
Prioritetslisten (APP-001) skal ha en egen seksjon der rekkefølgen kan endres ved sortering.

**GUI-004 Billading**
All konfigurasjon av billading skal være samlet i en egen seksjon. Det gjelder de felles innstillingene (LAD-001 til LAD-003) og innstillingene per elbillader (LAD-004 til LAD-010 og LAD-022).

## 5. Åpne spørsmål

Ingen åpne spørsmål.
