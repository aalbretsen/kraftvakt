# Kraftvakt – Kravspesifikasjon

Prioritert effektstyring for Home Assistant.

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
| GUI | Brukergrensesnitt |

## 2. Helhetsbeskrivelse

### 2.1 Bakgrunn

Norske nettselskaper beregner kapasitetsleddet i nettleien ut fra timene i måneden med høyest forbruk. Å holde gjennomsnittseffekten i hver time under en valgt grense hindrer at husstanden havner på et dyrere trinn.

### 2.2 Virkemåte sett utenfra

- Brukeren setter en effektgrense, for eksempel 10 kW, som tilsvarer høyst 10 kWh forbruk i løpet av en time. Kraftvakt prøver hele tiden å holde forbruket rett under effektgrensen.
- Kraftvakt styrer bare apparater som kan vike for annet forbruk, typisk oppvarming og billading. Brukeren ordner dem i en prioritert liste. Apparater som ikke kan vente, som stekeovn, styres ikke, men forbruket deres inngår i totalen. Et apparat kan ha varianter med alternativ prioritet under bestemte forhold, for eksempel høyere prioritet om morgenen.
- Reguleringen fatter jevnlig avgjørelser om hvilke apparater som skal være på. Et apparat slås på når det er ledig effekt under effektgrensen, ett og ett i prioritert rekkefølge og etter en ventetid som hindrer at det slås av og på gjentatte ganger. Går forbruket over effektgrensen, slås det lavest prioriterte apparatet av.
- Reguleringen styres av et kort gjennomsnitt av forbruket som jevner ut målingene. I tillegg overvåkes gjennomsnittet over tidsrommet nettselskapet måler forbruket over, i dag siste time. Det er dette snittet som skal holdes under effektgrensen.
- Straff er en sikkerhetsventil hvis reguleringen likevel feiler. Går snittforbruket klart over effektgrensen, slås alle regulerte apparater av til overforbruket er hentet inn.
- Reguleringen starter alltid med at alle apparater er slått av, og slår dem deretter på igjen ett og ett. Mangler målinger fra effektsensoren, går reguleringen i sikker tilstand, der alle apparater holdes av.
- Brukeren kan stoppe og starte reguleringen. Det meste av konfigurasjonen kan bare endres mens den er stoppet.
- Elbilladere håndteres spesielt. Ladestrømmen økes og reduseres trinnvis etter hvor mye effekt som er ledig. En elbillader lader bare når reguleringen har gitt den lov, slik at en ny bil ikke begynner å lade av seg selv og får forbruket til å øke brått. Hver elbillader kan begrenses til et ladetidsrom, som brukeren kan overstyre.
- Kraftvakt har et eget panel i sidemenyen i Home Assistant, med en statusside og konfigurasjonssider. All konfigurasjon gjøres der.

### 2.3 Avgrensninger

- Kraftvakt leser ikke strømmåleren selv, men bruker en sensor fra en annen integrasjon, typisk fra HAN-porten.
- Kraftvakt vet ikke hvor mye et apparat faktisk bruker, for eksempel på grunn av en innebygd termostat. Kraftvakt bestemmer bare om det er ledig kapasitet til at apparatet kan være på, og forsøker aldri å anslå et apparats forbruk.
- Kraftvakt tar ikke hensyn til om apparater slås av eller på utenom Kraftvakt. Kraftvakt regner med at apparatene står slik Kraftvakt selv sist har bestemt, og slik styring kan derfor forstyrre reguleringen. Unntaket er elbilladere, der Kraftvakt leser ladeeffekt og om en bil er tilkoblet.
- Kraftvakt husker ikke reguleringens tilstand over en omstart av Home Assistant eller integrasjonen. All konfigurasjon, også stillingen til bryterne for elbilladerne, bevares.
- Kraftvakt regulerer bare forbruk ut fra gjeldende konfigurasjon. Apparater som tas ut av konfigurasjonen, får ingen flere kommandoer.
- Kraftvakt kjører helt lokalt, uten skytjenester.

### 2.4 Sammenheng i løsningen

1. **Måling (MAL):** Effektsensoren gir husets totale effekt. Ut fra den beregnes reguleringssnittet og snittforbruket.
2. **Prioritetsliste (APP):** Brukeren ordner apparatene i prioritert rekkefølge. Når billadestyring er aktivert, står elementet «Elbillading» i listen. På den plassen ligger de fiktive apparatene for elbilladerne (LAD). Et apparat kan ha varianter med alternativ plass i listen, og bare den gjeldende varianten er med i reguleringen.
3. **Regulering (REG):** For hvert reguleringsintervall fatter reguleringen en avgjørelse ut fra reguleringssnittet. Alt skjer ved avgjørelsene. Reguleringen slår apparater av og på i prioritert rekkefølge, med ventetid før et apparat slås på. Reguleringen starter alltid med at alle apparater slås av, kan stoppes og startes av brukeren, og går i sikker tilstand hvis effektsensoren faller bort. Det meste av konfigurasjonen kan bare endres mens reguleringen er stoppet.
4. **Straff (STR):** Når snittforbruket går over effektgrensen, begynner overforbruket å telle. Går snittforbruket over effektgrensen pluss straffeterskelen, overstyrer straffen reguleringen og holder alle regulerte apparater av til forbruket er redusert like mye som overforbruket.
5. **Elbillading (LAD):** Egne regler avgjør hvilke elbilladere som har lov til å lade, og i hvilken rekkefølge de får ladestrøm. Reguleringen styrer ladestrømmen gjennom de fiktive apparatene. En elbillader lader bare når reguleringen har aktivert den, slik at en ny bil aldri starter lading på egen hånd.
6. **Entiteter og brukergrensesnitt (ENT, GUI):** Snittene, varselet om sikker tilstand og brukerens brytere for elbilladerne eksponeres som entiteter. Brukergrensesnittet er et eget panel i sidemenyen, med en meny øverst for å velge mellom statusside og konfigurasjonssider. All konfigurasjon gjøres i panelet.

## 3. Begreper

| Begrep | Betydning |
|---|---|
| Effektgrense | Høyeste tillatte effekt, og målet reguleringen etterstreber. Tilsvarer ønsket trinn i kapasitetsleddet i nettleietariffen. Reguleringen prøver hele tiden å holde forbruket rett under effektgrensen. |
| Effektsensor | Sensor fra en annen integrasjon som måler husets totale momentane effekt. |
| Reguleringsvindu | Kort tidsrom som reguleringssnittet beregnes over. |
| Reguleringssnitt | Gjennomsnitt av effektsensoren over reguleringsvinduet. Snittet som styrer reguleringen: grunnlaget for ledig effekt og for reguleringens beslutninger om å slå apparater av og på. |
| Reguleringsintervall | Hvor ofte reguleringen fatter en ny avgjørelse, målt som et helt antall ganger reguleringsvinduet. |
| Avgjørelse | Reguleringens beslutning om å slå apparater av eller på, eller la dem stå som de er. Fattes ved hvert reguleringsintervall. Alle vurderinger og endringer i reguleringen skjer ved avgjørelsene. |
| Ledig effekt | Effektgrensen minus reguleringssnittet. |
| Kapasitetsvindu | Glidende vindu som tilsvarer tidsrommet nettselskapet måler forbruket over for å fastsette kapasitetsleddet. Med dagens tariff er det derfor et glidende vindu som måler gjennomsnittet én time tilbake i tid. |
| Snittforbruk | Gjeldende gjennomsnittlig forbruk over kapasitetsvinduet, i dag gjennomsnittet for siste time. Det endelige målet er at snittforbruket holdes under effektgrensen. Snittforbruket overvåkes for å kunne iverksette straff. |
| Effektreserve | Ledig effekt som må være tilgjengelig før et apparat kan slås på. |
| Apparat | En enhet som Kraftvakt kan slå av og på. |
| Prioritetsliste | Sortert liste over apparater og deres varianter. Øverst står det med høyest prioritet, det vil si det som sist blir tvangsslått av. |
| Variant | Ekstra oppføring av et apparat i prioritetslisten, med en merkelapp og et uttrykk som er sant eller usant. Gir apparatet en alternativ prioritet under bestemte forhold. |
| Gjeldende variant | Den varianten, eller apparatet uten variant, som akkurat nå gjelder for et apparat. Bare denne er med i prioriteringen og reguleringen. |
| Ventetid | Tid som må gå før reguleringen kan slå på et apparat. Skal dempe reguleringen, slik at apparater ikke slås av og på unødig ofte. |
| Vedvarende pendling | At reguleringen gang på gang slår det samme apparatet av og på, uten at andre apparater styres i mellomtiden. |
| Stoppet regulering | Tilstand der reguleringen ikke tar noen avgjørelser og alle apparater i konfigurasjonen er slått av. Det meste av konfigurasjonen kan bare endres i denne tilstanden. |
| Sikker tilstand | Tilstand der alle regulerte apparater er slått av og reguleringen ikke slår på noe, fordi reguleringen mangler en gyldig effektmåling. |
| Straffeterskel | Forbruk over effektgrensen som snittforbruket må overstige før en straffeperiode starter. |
| Overforbruk | Netto forbruk over effektgrensen, der forbruk under effektgrensen trekkes fra. Brukes til å avgjøre hvor lenge en straffeperiode varer. |
| Overforbrukstilstand | Tilstand som starter når snittforbruket går over effektgrensen og avsluttes når overforbruket er hentet inn igjen. Overforbruket telles bare mens tilstanden varer. |
| Innhenting | Reduksjon i forbruk som må oppnås før reguleringen kan starte igjen etter at straff er iverksatt. |
| Straffeperiode | Sikkerhetsventil som hjelper reguleringen å hente seg inn igjen etter en feil. Tidsrom der regulerte apparater holdes av for å hente inn et overforbruk. |
| Fiktivt apparat for elbillader | Del av en elbillader som tilsvarer ett ampere av ladestrømmen. Reguleringen behandler det som et apparat som kan slås på og av, og styrer slik ladestrømmen. |
| Ladestrøm | Strømstyrken, i ampere, som en elbillader er stilt inn til å lade bilen med. |
| Aktivert elbillader | Elbillader som reguleringen har gitt lov til å lade, ved at minst ett av dens fiktive apparater er på. En deaktivert elbillader starter ikke lading selv om en bil kobles til. |
| Aktivt ladende elbillader | Elbillader som faktisk lader bilen og forbruker strøm. |
| Ventende elbillader | I modus for én elbillader om gangen: elbillader som ikke får lade fordi en annen elbillader lader aktivt. |
| Forbigått elbillader | Elbillader som ikke trekker strøm, for eksempel fordi den står uten bil eller bilen er fulladet, og som derfor ikke skal stå i veien for andre elbilladere. |
| Konfigurert ladeprioritering | Rekkefølgen mellom elbilladerne som brukeren har satt, med høyest prioritet øverst. |
| Gjeldende ladeprioritering | Rekkefølgen mellom elbilladerne som reguleringen faktisk bruker akkurat nå. Kan avvike fra den konfigurerte ladeprioriteringen. Gjelder bare elbilladere, ikke andre apparater eller varianter av apparater. |
| Ladetidsrom | Tidsrom i døgnet der en elbillader har lov til å lade. |
| Overstyring av ladetidsrom | Midlertidig tillatelse til å lade utenfor ladetidsrommet, frem til neste ladetidsrom starter. |
| Panel | Egen side som Kraftvakt legger til i sidemenyen i Home Assistant. Panelet er brukergrensesnittet til løsningen. |
| Statusside | Side i panelet som viser hvordan reguleringen står akkurat nå. |
| Konfigurasjonsside | Side i panelet der brukeren konfigurerer en del av løsningen. |
| Konfigurasjon | Alt brukeren har satt opp for løsningen. Bevares over enhver omstart. |
| Reguleringens tilstand | Det reguleringen holder rede på underveis, for eksempel overforbruk, straff og ventetider. Starter på nytt med standardverdier ved hver oppstart. Målingene og snittene er ikke en del av den. |

## 4. Krav

### 4.1 GEN – Generelt og rammebetingelser

Grunnrammene for hele løsningen. At et apparat er på eller av, betyr i kravene at Kraftvakt har gitt det beskjed om å slå seg på eller av (GEN-006).

**GEN-001 Formål**
Kraftvakt skal være en integrasjon for Home Assistant. Den skal styre hvilke apparater som får være på, i prioritert rekkefølge, slik at snittforbruket holdes under effektgrensen.
Begrunnelse: Unngå et dyrere trinn i kapasitetsleddet i nettleien.
Relatert: REG, STR, APP.

**GEN-002 Lokal drift**
Løsningen skal kjøre helt lokalt i Home Assistant, uten skytjenester eller eksterne datakilder.

**GEN-003 Effektsensor**
Løsningen skal hente husets totale effekt fra en effektsensor levert av en annen integrasjon. Brukeren skal kunne velge sensoren. Løsningen skal ikke lese strømmåleren selv. Bortfall av sensoren håndteres etter MAL-006 og REG-011.
Relatert: MAL-001, MAL-003, MAL-006, MAL-007, REG-011, GUI-008.

**GEN-004 Kun av/på-styring**
Løsningen skal bare avgjøre om et apparat har lov til å være på. Den skal ikke forutsette at apparatets faktiske forbruk er kjent eller styrbart. For elbilladere styres ladestrømmen gjennom fiktive apparater for elbillader (LAD-011).
Relatert: GEN-005, GEN-006, APP-004, LAD-011.

**GEN-005 Ingen anslag av apparatforbruk**
Løsningen skal aldri beregne eller anslå hva et apparat bruker ut fra endringer i totalforbruket etter at apparatet er slått på.
Begrunnelse: Et apparat bruker ikke nødvendigvis strøm selv om det får lov, og andre forbrukere kan starte samtidig.
Relatert: GEN-004, REG-006.

**GEN-006 Ingen hensyn til styring utenom reguleringen**
Reguleringen skal ikke ta hensyn til om apparater slås av eller på utenom Kraftvakt, for eksempel manuelt eller av automasjoner. Den regner alltid med at et apparat står slik Kraftvakt selv sist har bestemt, og holder bare rede på hvilke apparater den selv har gitt beskjed om å slå på. Løsningen trenger derfor ikke lese apparatenes tilstand. Kravet begrenser ikke hva løsningen har lov til å lese, bare hva reguleringen skal ta hensyn til.
Unntak: For elbilladere leser løsningen ladeeffekt (LAD-008) og bil tilkoblet (LAD-010). Det gjør det mulig å styre ladingen effektivt, håndtere forbigåtte elbilladere (LAD-017) og la bare én elbillader lade om gangen (LAD-021 til LAD-023).
Begrunnelse: Løsningen har bare handlinger for å slå apparater av og på (APP-002, APP-003). Å ta hensyn til styring utenom Kraftvakt ville gjort reguleringen mer komplisert. Slik styring kan forstyrre reguleringen, gå ut over apparater med høyere prioritet og utløse straff (GUI-011).
Relatert: GEN-004, GEN-007, GEN-012, REG-009, APP-002, APP-003, LAD-008, LAD-010, LAD-017, LAD-021, LAD-023, GUI-011.

**GEN-007 Reguleringens tilstand starter på nytt ved hver oppstart**
Reguleringens tilstand skal begynne på nytt med standardverdier ved hver oppstart. Det gjelder ved start av Home Assistant eller integrasjonen, når reguleringen startes etter stopp (REG-016), etter sikker tilstand (REG-011) og etter endring av konfigurasjonen (REG-010). Det gjelder overforbruk, pågående straffeperiode, ventetider, tellere for økende ventetid, gjeldende ladeprioritering, om en elbillader er forbigått og hvilke apparater som er på. Å bruke bryterne for elbilladerne (ENT-003 og ENT-004) mens reguleringen kjører starter ikke reguleringen på nytt. Snittene er målinger og ikke en del av reguleringens tilstand. De beregnes fortløpende også mens reguleringen er stoppet, og begynner bare på nytt ved start av Home Assistant eller integrasjonen og etter sikker tilstand (MAL-005). Etter start av Home Assistant eller integrasjonen skal reguleringen starte etter REG-009. Konfigurasjonen er ikke en del av reguleringens tilstand og bevares (GEN-011).
Begrunnelse: En omstart skal behandles på samme måte uansett årsak. Det gir en enklere løsning. Når reguleringen starter med alle apparater avslått, bidrar det vanligvis nok til å hente inn et overforbruk, så det er ikke nødvendig å huske det.
Relatert: GEN-006, GEN-011, MAL-005, REG-009, REG-010, REG-011, REG-016.

**GEN-008 Kun gjeldende konfigurasjon**
Løsningen skal bare regulere forbruk ut fra gjeldende konfigurasjon. Apparater og elbilladere som ikke lenger er en del av konfigurasjonen, skal overlates til seg selv. Løsningen skal ikke sende kommandoer til dem, og skal ikke rydde opp i tilstanden de står i. En elbillader som midlertidig er utenfor reguleringen (ENT-003), er fortsatt en del av konfigurasjonen.
Konfigurasjonen, bortsett fra bryterne for elbilladerne (ENT-003 og ENT-004), kan bare endres mens reguleringen er stoppet (REG-010), og alle apparater i konfigurasjonen er da slått av. Apparater som tas ut av konfigurasjonen, står derfor allerede avslått, og apparater som legges til, styres først når reguleringen startes og alt er slått av.
Begrunnelse: Løsningen skal konsentrere seg om kjernen i det den skal løse og ikke bli mer komplisert enn nødvendig. Det er også forvirrende for brukeren at løsningen sender kommandoer til apparater som er tatt ut av konfigurasjonen.
Relatert: GEN-001, APP-001, LAD-001, REG-010, REG-016, ENT-003.

**GEN-009 Sann/usann-verdi fra entitet eller mal**
Når en innstilling skal gi en sann/usann-verdi fra Home Assistant, skal brukeren kunne angi enten en boolsk entitet eller en mal som tolkes som et boolsk uttrykk. Verdien er sann bare når entiteten eller malen gir den boolske verdien sann. For en entitet regnes verdien som sann når entiteten er på. Alle andre verdier regnes som usann. Det gjelder også når entiteten er utilgjengelig eller deaktivert, og når malen gir en annen verdi enn sann eller feiler.
Kravet gjelder innstillingen bil tilkoblet (LAD-010) og uttrykkene for varianter (APP-006).
Eksempel: En binær sensor som er utilgjengelig, regnes som usann.
Begrunnelse: Ett sted fastlegger hvordan en sann/usann-verdi angis og tolkes, slik at alle slike innstillinger oppfører seg likt.
Relatert: GEN-010, APP-006, APP-007, LAD-010, LAD-017.

**GEN-010 Sann betyr at det som beskrives, er tilfellet**
Hver innstilling der brukeren angir en sann/usann-verdi etter GEN-009, skal defineres slik at sann betyr at det innstillingen beskriver, er tilfellet, og usann betyr at det ikke er tilfellet eller ikke kan fastslås. Sann skal ikke bety at noe er fraværende. Innstillingen skal derfor navngis etter det som er tilfellet når verdien er sann, ikke etter det motsatte.
Hvordan en utilgjengelig eller ugyldig verdi tolkes, skal alltid ses i sammenheng med hva reguleringen bruker verdien som bevis for. Mangler beviset, skal reguleringen oppføre seg som om det den søker bevis for, ikke er tilfellet. Prinsippet gjelder også sann/usann-avgjørelser som reguleringen selv utleder av en måling, som om en elbillader lader (LAD-008).
Eksempel 1: Reguleringen bruker «bil tilkoblet» (LAD-010) som bevis for at en bil er tilkoblet. En utilgjengelig verdi er ikke bevis, så ingen bil regnes som tilkoblet. En innstilling «bil frakoblet» ville ikke fulgt kravet.
Eksempel 2: Reguleringen bruker ladeeffekten (LAD-008) som bevis for at en elbillader ikke lader. En utilgjengelig verdi er ikke bevis, så elbilladeren regnes som aktivt ladende.
Begrunnelse: En verdi som er utilgjengelig eller feiler, regnes som usann (GEN-009). Da skal en manglende verdi aldri kunne bety at noe er tilfellet. Hvilken tolkning som er trygg, avhenger av hva reguleringen bruker verdien til.
Relatert: GEN-009, APP-006, LAD-008, LAD-010.

**GEN-011 Konfigurasjon bevares over omstart**
All konfigurasjon skal lagres varig og bevares uendret over enhver form for omstart, også omstart av Home Assistant og av integrasjonen. Konfigurasjon er:
- alle innstillinger, apparater, varianter, prioriteringer og elbilladere som brukeren setter opp i panelet (GUI-008 til GUI-010), og
- stillingen til verdiene løsningen eksponerer for at brukeren kan sette dem for elbilladerne (ENT-003 og ENT-004).

Standardverdien står i kravet som beskriver hver innstilling, og gjelder til brukeren har satt en annen. Bryterne for elbilladerne regnes som konfigurasjon når det gjelder lagring, men kan endres mens reguleringen kjører (REG-010).
Begrunnelse: Brukerens valg skal ikke forsvinne. Reguleringens tilstand (GEN-007) skal derimot alltid starte på nytt.
Relatert: GEN-007, REG-010, ENT-003, ENT-004, GUI-008, GUI-009, GUI-010.

**GEN-012 Feil ved utføring av handling**
Mislykkes en handling for et apparat eller en elbillader (APP-002, APP-003, LAD-004 til LAD-006), skal feilen skrives til Home Assistants logg. Reguleringen skal fortsette som om handlingen lyktes, og handlingen skal ikke gjentas.
Begrunnelse: Reguleringen tar ikke hensyn til hva som faktisk skjer med apparatet (GEN-006).
Relatert: GEN-006, APP-002, APP-003, LAD-004, LAD-005, LAD-006.

**GEN-013 Entitet for apparat og elbillader**
Hvert apparat og hver elbillader skal knyttes til en entitet i Home Assistant som brukeren velger. Valget er påkrevd, og samme entitet kan ikke brukes for to apparater eller to elbilladere. Navnet i Home Assistant er navnet på apparatet eller elbilladeren, og identifiserer det i listene og på statussiden. For en elbillader er entiteten normalt laderens bryter for tillatt lading.
Entiteten setter konteksten for malene og uttrykkene som er konfigurert for apparatet eller elbilladeren. Den skal være tilgjengelig i dem uten at malen nevner entiteten selv. Byttes entiteten ut med en annen av samme type, skal malene fungere uten å bli oppdatert.
Der det finnes en entydig standardhandling for entitetens type, skal brukeren kunne velge den i stedet for å skrive en mal for handlingene som slår apparatet på og av (APP-002, APP-003) og som aktiverer og deaktiverer elbilladeren (LAD-005, LAD-004).
Begrunnelse: Entiteten blir lett tilgjengelig i malene, og en entitet kan byttes ut uten å endre malene. Brukeren slipper å skrive en mal der en standardhandling er nok.
Relatert: APP-001, APP-002, APP-003, APP-006, LAD-003, LAD-004, LAD-005, LAD-006, LAD-010.

### 4.2 SPR – Språk

**SPR-001 Standardspråk**
Engelsk skal være standardspråk.
Relatert: SPR-002.

**SPR-002 Norsk og flere språk**
Løsningen skal støtte flere språk. Norsk skal leveres som første oversettelse i tillegg til engelsk.
Relatert: SPR-001.

### 4.3 MAL – Måling og snittberegning

Løsningen bruker to gjennomsnitt av effektsensoren. Reguleringssnittet er kort, beregnes én gang for hvert reguleringsvindu og styrer den løpende reguleringen. Snittforbruket er et glidende gjennomsnitt over kapasitetsvinduet, i dag siste time. Det brukes til å avgjøre om reguleringen holder seg innenfor effektgrensen, og til å styre straffen. Snittene beregnes fortløpende. Det er bare reguleringens vurderinger og endringer som skjer ved avgjørelsene (REG-005).

**MAL-001 Reguleringssnitt**
Løsningen skal beregne reguleringssnittet som gjennomsnittet av effektsensoren over reguleringsvinduet. Et nytt reguleringssnitt skal beregnes én gang for hvert reguleringsvindu, slik at hvert snitt dekker et eget tidsrom uten overlapp med forrige snitt. Snittene skal beregnes fortløpende også mens reguleringen er stoppet (REG-016). Etter en omstart av Home Assistant eller integrasjonen erstattes tapte målinger etter MAL-005.
Begrunnelse: Jevne ut målingene, slik at kortvarige topper ikke fører til at apparater slås av og på hele tiden.
Relatert: MAL-002, MAL-004, MAL-006, REG-002, REG-003, REG-016, ENT-001.

**MAL-002 Reguleringsvindu**
Reguleringsvinduet skal kunne konfigureres i sekunder. Standard er 60 sekunder, og gyldig område er 10–600 sekunder.
Relatert: MAL-001, REG-002, LAD-017, GUI-008.

**MAL-003 Snittforbruk og kapasitetsvindu**
Løsningen skal beregne snittforbruket som et glidende gjennomsnitt av effektsensoren over kapasitetsvinduet. Kapasitetsvinduet skal være fast én time tilbake i tid og skal ikke kunne konfigureres av brukeren.
Begrunnelse: Et glidende vindu gjør det mulig å oppdage med en gang når snittforbruket går over effektgrensen, og å rette opp et overforbruk fortløpende. Med faste klokketimer kan et overforbruk midt i timen bare rettes opp ved å kutte strømmen resten av timen. Vinduet skal samsvare med nettleietariffen, som i dag måles per time. Et fast vindu gjør også konfigurasjonen enklere.
Relatert: MAL-004, MAL-005, MAL-006, STR-001, STR-004, STR-005, ENT-002.

**MAL-004 Gjennomsnitt over tid**
Snittberegningene skal gi gjennomsnittlig effekt over vinduet, det vil si energiforbruket i vinduet delt på vinduets lengde. Resultatet skal være korrekt uavhengig av hvor ofte effektsensoren oppdateres. Det skal kunne verifiseres både når sensoren oppdateres hvert sekund og når den oppdateres hvert 10. sekund eller sjeldnere, gjennom hele kapasitetsvinduet.
Begrunnelse: Kapasitetsleddet fastsettes ut fra energiforbruket per time. HAN-porten krever minst én oppdatering hvert 10. sekund, men noen målere oppdaterer sjeldnere.
Relatert: MAL-001, MAL-003.

**MAL-005 Manglende målinger ved oppstart**
Når Home Assistant eller integrasjonen starter, og når effektsensoren gir en gyldig måleverdi igjen etter sikker tilstand (REG-011), skal måleverdier som mangler bakover i tid, i både reguleringsvinduet og kapasitetsvinduet, settes lik den første målte momentane effekten. Reguleringssnittet og snittforbruket skal dermed være lik denne første målingen ved oppstarten.
Begrunnelse: Løsningen bevarer ingen måledata over en omstart (GEN-007). En omstart etter sikker tilstand skal behandles på samme måte som en oppstart.
Relatert: GEN-007, MAL-001, MAL-003, REG-009, REG-011.

**MAL-006 Toleranse for manglende måling**
Er effektsensoren utilgjengelig eller uten gyldig måleverdi (MAL-007) når et nytt reguleringssnitt skal beregnes, skal siste gyldige momentane effekt brukes for tidsrommet uten måling. Det gjelder både reguleringssnittet og snittforbruket. Løsningen skal tåle dette ved én beregning. Er effektsensoren også utilgjengelig eller uten gyldig måleverdi ved den påfølgende beregningen, skal reguleringen gå i sikker tilstand (REG-011).
Begrunnelse: En kortvarig utilgjengelighet skal ikke føre til at hele reguleringen starter på nytt.
Relatert: GEN-003, MAL-001, MAL-003, MAL-004, MAL-007, REG-011.

**MAL-007 Gyldig måleverdi og enhet**
Effektsensoren (GEN-003) og sensorene for ladeeffekt (LAD-008) skal kunne oppgi effekt i watt eller kilowatt, og løsningen skal regne om til en felles enhet. En måleverdi er gyldig når sensoren er tilgjengelig og verdien er et tall. Alle andre verdier, blant annet «ukjent» og «utilgjengelig», er ugyldige. En negativ verdi regnes som 0 W.
Begrunnelse: Ett sted fastlegger hva som regnes som en gyldig måling, slik at vilkårene i MAL-006 og REG-011 er entydige.
Relatert: GEN-003, MAL-006, REG-011, LAD-008.

### 4.4 REG – Regulering

Den løpende reguleringen avgjør når apparater slås på og av. Den kjører i et reguleringsintervall og fatter én avgjørelse for hvert intervall. Alt reguleringen vurderer og endrer, skjer ved avgjørelsene og aldri utløst av hendelser mellom dem (REG-005). Den bruker reguleringssnittet (MAL-001) og prioritetslisten (APP-001). Apparater slås av ved den første avgjørelsen etter at reguleringssnittet er over effektgrensen. Før et apparat slås på, venter reguleringen en ventetid som skal hindre at straffen (STR) må inntre. Reguleringen starter alltid med at alle apparater slås av (REG-009). Brukeren kan stoppe og starte reguleringen (REG-016), og det meste av konfigurasjonen kan bare endres mens den er stoppet (REG-010).

**REG-001 Effektgrense**
Effektgrensen skal kunne konfigureres. Standard er 10 kW, og gyldig område er 1–50 kW.
Relatert: REG-006, REG-008, STR-001, GUI-008.

**REG-002 Reguleringsintervall**
Reguleringen skal kjøre i et reguleringsintervall som brukeren kan konfigurere. Gyldige verdier er 1x, 2x, 3x og 4x reguleringsvinduet. Verdien angir hvor mange nye reguleringssnitt som skal være beregnet mellom hver avgjørelse. Standard er 1x.
Reguleringssnittet skal fortsatt beregnes over reguleringsvinduet, uansett reguleringsintervall. Reguleringen skal bare handle på det siste beregnede reguleringssnittet ved en avgjørelse. Med 2x hoppes ett reguleringssnitt over, og reguleringen handler på det neste. Dette gjelder både når apparater slås på og når de slås av.
Eksempel med reguleringsvindu 60 sekunder: med standardverdien 1x tas en avgjørelse hvert 60. sekund. Med 2x tas den hvert 120. sekund, og med 4x hvert 240. sekund.
Begrunnelse: Reguleringssnittet faller ikke med en gang etter at et apparat er slått av. Et reguleringsintervall gir snittet tid til å reagere før neste avgjørelse.
Relatert: MAL-001, MAL-002, REG-003, REG-004, REG-005, GUI-008.

**REG-003 Avgjørelse per reguleringsintervall**
Reguleringen skal fatte én ny avgjørelse for hvert reguleringsintervall. En avgjørelse går ut på å slå på apparater, slå av apparater eller la alt stå som det er. Avgjørelser om å slå apparater av og på ut fra ledig effekt skal bygge på det siste beregnede reguleringssnittet, ikke på momentan effekt. Straff (STR), sikker tilstand (REG-011), start av regulering (REG-009) og reglene for elbillading (LAD) kan i tillegg holde apparater av eller slå dem av.
Relatert: MAL-001, REG-002, REG-004, REG-005, REG-009, REG-011, STR-003.

**REG-004 Ett apparat per avgjørelse**
En avgjørelse skal slå på høyst ett apparat eller slå av høyst ett apparat, ikke begge deler. For elbilladere er hvert fiktivt apparat et apparat (LAD-011).
Kravet gjelder bare avgjørelser som bygger på ledig effekt fra reguleringssnittet. Det gjelder ikke når flere apparater slås av samtidig fordi forbruket må kuttes straks, eller fordi utkoblingen ikke endrer forbruket: ved start og stopp av regulering (REG-009, REG-016), i sikker tilstand (REG-011), under straff (STR-003), når en elbillader ikke har lov til å lade (LAD-024, LAD-025), når en elbillader som ikke trekker strøm, begrenses eller deaktiveres (LAD-029, LAD-030), og når et apparat bytter gjeldende variant (APP-009).
Begrunnelse: Antallet apparater per avgjørelse er skilt ut som et eget krav, slik at det kan endres senere uten å endre resten av reguleringen.
Relatert: REG-003, REG-007, REG-008, APP-009, LAD-011.

**REG-005 Alt skjer ved avgjørelsene**
Alle vurderinger, beregninger og endringer i reguleringen skal skje ved avgjørelsene og ikke mellom dem. Det gjelder blant annet ventetid, om en elbillader er forbigått, gjeldende ladeprioritering, gjeldende variant for apparater, om en elbillader har lov til å lade, overforbruk, straff og sikker tilstand.
Hendelser skal ikke utløse beregninger eller endringer av seg selv. Eksempler er at brukeren slår om en bryter for en elbillader (ENT-003, ENT-004), at et ladetidsrom starter eller slutter, at en bil kobles til eller fra, og at effektsensoren faller bort. Slike hendelser skal fanges opp ved første avgjørelse etter at de har skjedd. Apparater skal ikke slås av eller på mellom avgjørelsene. Unntakene er at alle apparater slås av når Home Assistant eller integrasjonen starter (REG-009) og når brukeren stopper eller starter reguleringen (REG-016).
Beregningen av reguleringssnittet og snittforbruket (MAL) skjer fortløpende for hvert reguleringsvindu og er ikke en avgjørelse.
Begrunnelse: En regulering som bare endrer noe én gang per intervall er forutsigbar og enkel å forstå, og hendelser midt mellom avgjørelsene kan ikke forstyrre den.
Relatert: MAL-001, REG-002, REG-003, REG-009, REG-011, REG-016, STR-001, LAD-016, LAD-017, LAD-025, LAD-027.

**REG-006 Vilkår for å slå på et apparat**
Et apparat skal bare slås på når reguleringssnittet er under effektgrensen. Er effektreserve satt for apparatet, skal i tillegg reguleringssnittet pluss effektreserven være mindre enn eller lik effektgrensen.
Relatert: REG-001, REG-012, APP-004, LAD-012.

**REG-007 Fast rekkefølge når apparater slås på**
Apparater skal slås på i fast prioritert rekkefølge med høyest prioritet først. Et apparat skal ikke slås på før alle apparater med høyere prioritet er på, selv om det ville hatt nok ledig effekt. Apparater som ikke er en del av reguleringen, som ikke har lov til å være på, eller som er forbigåtte elbilladere (LAD-017), hoppes over. Det samme gjelder oppføringer som ikke er gjeldende variant av apparatet (APP-007). Hvor mange apparater som slås på per avgjørelse, følger av REG-004.
Relatert: REG-004, REG-006, REG-012, APP-001, APP-007, LAD-017, LAD-024, LAD-025.

**REG-008 Utkobling ved overskridelse**
Er reguleringssnittet over effektgrensen ved en avgjørelse, skal det lavest prioriterte apparatet som er på, slås av, uten ventetid. Er reguleringssnittet fortsatt over effektgrensen ved neste avgjørelse, skal neste apparat slås av på samme måte. Fiktive apparater for forbigåtte elbilladere (LAD-017) hoppes over.
Begrunnelse: Reguleringssnittet faller ikke med en gang etter at et apparat er slått av. Ett apparat per avgjørelse (REG-004) hindrer at alle apparater slås av i rask rekkefølge. Å slå av apparater for en elbillader som ikke trekker strøm, reduserer ikke forbruket.
Relatert: REG-001, REG-002, REG-004, APP-001, LAD-013.

**REG-009 Start av regulering**
Reguleringen skal alltid starte med å slå av alle apparater i konfigurasjonen, inkludert fiktive apparater for elbillader, også etter straff og sikker tilstand der alle apparater allerede er slått av. For en elbillader betyr det at den deaktiveres (LAD-004). Et apparat med varianter slås av én gang. Gjeldende variant bestemmes først ved første avgjørelse. Deretter skal apparatene slås på ett og ett etter REG-004, REG-006, REG-007 og REG-012. Tellingen av reguleringsintervallet (REG-002) skal starte på nytt ved hver start, slik at første avgjørelse etter starten tas etter ett helt reguleringsintervall. Reguleringen skal starte på denne måten:
- når Home Assistant eller integrasjonen starter og konfigurasjonen er fullstendig (REG-016), og da slås alle apparater av straks,
- når brukeren starter reguleringen (REG-016), og da slås alle apparater av straks,
- ved avgjørelsen der en straffeperiode avsluttes (STR-008), og
- ved første avgjørelse etter at effektsensoren er tilgjengelig igjen etter bortfall (REG-011).

Omstart er omstart: ved hver start skal ventetider, tellere for økende ventetid, gjeldende ladeprioritering, overforbruk og straffeperiode nullstilles (GEN-007). Snittene beholdes bortsett fra ved oppstart av Home Assistant eller integrasjonen og etter sikker tilstand (MAL-005).
Begrunnelse: Løsningen tar ikke hensyn til apparatenes faktiske tilstand (GEN-006) og husker ikke reguleringens tilstand over en omstart (GEN-007). Å starte med alt avslått gir en kjent tilstand, og det bidrar vanligvis nok til å hente inn et eventuelt overforbruk.
Relatert: GEN-006, GEN-007, MAL-005, REG-004, REG-005, REG-011, REG-016, STR-008.

**REG-010 Konfigurasjon bare mens reguleringen er stoppet**
Konfigurasjonen skal ikke kunne endres mens reguleringen kjører. Brukeren må stoppe reguleringen (REG-016) før innstillinger, apparater, prioriteringer og elbilladere kan legges til, endres eller tas ut. Unntaket er bryterne for elbilladerne (ENT-003 og ENT-004). De kan brukes mens reguleringen kjører, og endringen starter ikke reguleringen på nytt. Stillingen deres er likevel konfigurasjon som bevares (GEN-011).
Begrunnelse: Alle apparater er avslått når reguleringen er stoppet, og alt som er en del av reguleringen, slås av når den startes. Det gir kontroll på utgangspunktet etter enhver endring. Et apparat som tas ut av konfigurasjonen, er allerede avslått, og et apparat som legges til, styres ikke før reguleringen startes.
Relatert: GEN-008, GEN-011, REG-009, REG-016, APP-001, LAD-003, ENT-003, ENT-004, GUI-012.

**REG-011 Sikker tilstand ved bortfall av effektsensor**
Reguleringen skal gå i sikker tilstand når effektsensoren har vært utilgjengelig eller uten gyldig måleverdi ved de to siste beregningene av reguleringssnittet (MAL-006). Dette skal vurderes ved hver avgjørelse, og sikker tilstand inntrer ved den første avgjørelsen der vilkåret er oppfylt.
I sikker tilstand skal alle apparater i konfigurasjonen slås av ved avgjørelsen der sikker tilstand inntrer, og ingen apparater skal slås på. Når effektsensoren gir en gyldig måleverdi igjen, skal reguleringen starte på nytt som ved oppstart: etter REG-009 ved første avgjørelse, med måleverdier etter MAL-005.
Begrunnelse: Uten måling kan reguleringen ikke vite om forbruket er under effektgrensen. En kort utilgjengelighet skal likevel ikke gi sikker tilstand og dermed omstart av hele reguleringen (MAL-006).
Relatert: GEN-003, GEN-007, MAL-005, MAL-006, REG-004, REG-005, REG-009, ENT-005.

**REG-012 Ventetid før et apparat slås på**
Kommer en avgjørelse frem til at neste apparat kan slås på, det vil si at vilkårene i REG-006 og REG-007 er oppfylt, skal apparatet ikke slås på med en gang. I stedet skal ventetiden for apparatet starte. Apparatet skal slås på ved den første avgjørelsen etter at ventetiden er gått, forutsatt at vilkårene da fortsatt er oppfylt. Er ventetiden 0, slås apparatet på ved den samme avgjørelsen. Er vilkårene ikke lenger oppfylt ved en avgjørelse mens ventetiden går, skal ventetiden avbrytes. En ny ventetid starter først når en avgjørelse igjen viser at apparatet kan slås på.
Eksempel med standardverdiene: en avgjørelse viser at et apparat kan slås på, og reguleringssnittet er 5 kW. Ventetiden blir 2,5 minutter (REG-013). Avgjørelsene tas hvert 60. sekund, så apparatet slås på ved avgjørelsen 3 minutter senere, forutsatt at reguleringssnittet er uendret.
Begrunnelse: Ventetiden skal hindre at apparater slås av og på gjentatte ganger med korte mellomrom, og dermed hindre at straffen må inntre.
Relatert: REG-003, REG-006, REG-007, REG-013, REG-014, REG-015.

**REG-013 Lineær ventetid**
Ventetiden før et apparat kan slås på, skal beregnes lineært ut fra forholdet mellom reguleringssnittet og effektgrensen. Et reguleringssnitt på 0 gir ingen ventetid. Et reguleringssnitt lik eller over effektgrensen gir en ventetid lik ventetid ved effektgrensen (REG-014). Ventetiden blir aldri lengre enn dette. Mens ventetiden går, skal den regnes ut på nytt for hvert reguleringsintervall, ut fra reguleringssnittet ved den avgjørelsen.
Eksempel med standardverdiene: med reguleringssnitt 5 kW, effektgrense 10 kW og ventetid ved effektgrensen 5 minutter blir ventetiden 2,5 minutter.
Begrunnelse: Hindre at det lavest prioriterte apparatet slås av og på gjentatte ganger med korte mellomrom, og dermed hindre at straffen må inntre.
Relatert: REG-002, REG-012, REG-014, REG-015, MAL-001.

**REG-014 Ventetid ved effektgrensen**
Ventetid ved effektgrensen skal kunne konfigureres i minutter. Standard er 5 minutter, og gyldig område er 0–10 minutter.
Begrunnelse: Øvre grense på 10 minutter gir rom for økende ventetid ved vedvarende pendling (REG-015).
Relatert: REG-013, REG-015, GUI-008.

**REG-015 Økende ventetid ved vedvarende pendling**
Ved vedvarende pendling for samme apparat skal ventetiden før apparatet slås på igjen øke:
- Vedvarende pendling regnes fra og med andre gang det samme apparatet slås på igjen uten at noe annet apparat er slått av eller på i mellomtiden.
- Ventetiden starter på ventetid ved effektgrensen (REG-014) og øker med 2 minutter hver gang apparatet slås på igjen, opp til høyst 15 minutter.
- Økningen nullstilles så snart et annet apparat slås av eller på.
- Økningen og taket skal ikke kunne konfigureres. For elbilladere gjelder egne verdier (LAD-014).
- Apparatet skal fortsatt slås av uten ventetid etter REG-008.

Eksempel med standardverdien for ventetid ved effektgrensen: ventetiden blir 5, 7, 9, 11, 13 og deretter 15 minutter.

Begrunnelse: Vedvarende pendling viser at apparatet bruker mer enn den ledige effekten gir rom for.
Relatert: REG-008, REG-012, REG-013, REG-014, LAD-014.

**REG-016 Start og stopp av reguleringen**
Brukeren skal kunne stoppe og starte reguleringen, både fra panelet (GUI-007) og med en bryter (ENT-006). De to er samme funksjon og skal alltid vise samme status.
- Når reguleringen stoppes, skal alle apparater i konfigurasjonen slås av, inkludert fiktive apparater for elbillader, slik at elbilladerne deaktiveres. Stoppingen skal virke straks. Så lenge reguleringen er stoppet, skal reguleringen ikke ta avgjørelser og ikke slå på noe.
- Når reguleringen startes, skal alle apparater i konfigurasjonen først slås av. Deretter starter reguleringen etter REG-009, og apparatene slås på ett og ett.
- Reguleringen skal starte av seg selv når Home Assistant eller integrasjonen starter (REG-009), forutsatt at konfigurasjonen er fullstendig.
- Reguleringen skal ikke kunne startes før konfigurasjonen er fullstendig. Konfigurasjonen er fullstendig når effektsensor er valgt, og hvert apparat og, når billadestyring er aktivert, hver elbillader har alle påkrevde innstillinger (GEN-013, APP-002, APP-003, LAD-004 til LAD-008). Statussiden viser hva som mangler (GUI-005).

Begrunnelse: Å stoppe og starte gir en kjent utgangstilstand. Det gjør endringer i konfigurasjonen trygge (REG-010).
Relatert: GEN-007, GEN-008, REG-004, REG-005, REG-009, REG-010, ENT-006, GUI-007.

### 4.5 STR – Straffeperiode

Straffeperioden er en sikkerhetsventil som gjør det mulig å hente seg inn igjen etter en eventuell feil i den løpende reguleringen, og skal aldri være nødvendig. Den skal raskt føre til lavere forbruk, og forbruket skal reduseres like mye som overforbruket, slik at snittforbruket ikke skyter over effektgrensen. Overforbruket telles i en egen overforbrukstilstand som starter når snittforbruket går over effektgrensen og avsluttes når overforbruket er hentet inn igjen. Går snittforbruket over effektgrensen pluss straffeterskelen, inntrer straff. Er overforbruket da allerede hentet inn, inntrer ingen straff. Ellers holdes forbruket nede til overforbruket er hentet inn. Alle vurderinger i straffen skjer ved avgjørelsene (REG-005).

**STR-001 Utløsning av straff**
En straffeperiode skal starte hver gang snittforbruket ved en avgjørelse er høyere enn effektgrensen pluss straffeterskelen, med unntaket i STR-009. Snittforbruket skal bare vurderes ved avgjørelsene.
Relatert: MAL-003, REG-001, REG-005, STR-002, STR-009.

**STR-002 Straffeterskel**
Straffeterskelen skal kunne konfigureres som forbruk over effektgrensen. Standard er 1 kW, og gyldig område er 0–10 kW. Verdien 0 betyr at straffen starter straks snittforbruket overstiger effektgrensen.
Relatert: STR-001, GUI-008.

**STR-003 Apparater under straff**
Under straffeperioden skal alle apparater i konfigurasjonen være avslått. Dette gjelder også elbilladere. Alle apparatene slås av samtidig ved avgjørelsen der straffen starter, slik at forbruket faller så raskt som mulig. Ingen apparater skal slås på så lenge straffeperioden varer.
Begrunnelse: Straffen er en sikkerhetsventil. Den skal kutte forbruket raskt, slik at snittforbruket ikke skyter over effektgrensen.
Relatert: REG-004, APP-002, LAD-013.

**STR-004 Overforbrukstilstand**
Løsningen skal ha en egen overforbrukstilstand. Tilstanden skal starte når snittforbruket ved en avgjørelse er høyere enn effektgrensen, og avsluttes når overforbruket er hentet inn igjen, det vil si at det er null eller mindre. Overforbruket skal bare telles mens tilstanden varer.
Begrunnelse: Overforbruket skal bare måle det som har ført til at snittforbruket gikk over effektgrensen.
Relatert: MAL-003, REG-005, STR-005, STR-006, STR-009.

**STR-005 Måling av overforbruk**
I overforbrukstilstanden skal løsningen regne ut overforbruket som netto energi over effektgrensen, regnet fra tilstanden startet: energi over effektgrensen legges til, og energi under effektgrensen trekkes fra. Overforbruket skal regnes ut ved hver avgjørelse, ut fra alle reguleringssnittene som er beregnet siden forrige avgjørelse. Det skal telles hele tiden så lenge tilstanden varer, også etter at en straffeperiode har startet.
Eksempel med standardverdiene: et reguleringssnitt på 12 kW i ett reguleringsvindu og en effektgrense på 10 kW gir et overforbruk på 2 kW i ett minutt, det vil si omtrent 0,033 kWh. Et påfølgende reguleringssnitt på 8 kW i ett reguleringsvindu trekker like mye fra igjen.
Begrunnelse: Straffen skal ha riktig størrelse, uavhengig av hvor raskt forbruket faller etter overskridelsen.
Relatert: MAL-003, REG-005, STR-004, STR-006, STR-007.

**STR-006 Varighet av straff**
Straffen skal føre til at forbruket reduseres like mye som overforbruket. Løsningen skal selv beregne hvor lenge straffeperioden varer. Straffen skal vare til overforbruket er hentet inn, det vil si til overforbrukstilstanden avsluttes. Straffen avsluttes bare ved at overforbruket er hentet inn, eller ved at reguleringen startes på nytt etter stopp, sikker tilstand eller oppstart av Home Assistant eller integrasjonen. Da huskes ikke overforbruket (GEN-007), og alle apparater er avslått og slås på ett og ett.
Begrunnelse: Straffen skal hente inn overforbruket, slik at snittforbruket ikke overstiger effektgrensen. En start med alle apparater avslått bidrar vanligvis nok til å hente inn et overforbruk.
Relatert: GEN-007, STR-003, STR-004, STR-005, STR-007.

**STR-007 Start av innhenting**
Under en straffeperiode skal forbruk under effektgrensen ikke trekkes fra overforbruket før reguleringssnittet igjen er under effektgrensen. Innhentingen starter dermed først da.
Relatert: STR-005, STR-006, MAL-001.

**STR-008 Oppstart etter straff**
Etter straffeperioden skal reguleringen starte på nytt etter REG-009, ved den avgjørelsen der overforbruket er hentet inn.
Relatert: REG-009.

**STR-009 Ingen straff når overforbruket er hentet inn**
En straffeperiode skal ikke starte hvis overforbruket allerede er null eller mindre når vilkåret i STR-001 er oppfylt.
Begrunnelse: Reguleringen kan ha hentet seg inn selv. Da er straffen unødvendig.
Relatert: STR-001, STR-004, STR-005.

### 4.6 APP – Apparater og prioritetsliste

Prioritetslisten bestemmer i hvilken rekkefølge apparater slås på og av. Den inneholder vanlige apparater og, når billadestyring er aktivert, elementet «Elbillading».

**APP-001 Prioritetsliste**
Apparatene skal konfigureres i en sorterbar prioritetsliste. Øverste oppføring har høyest prioritet. Et apparat står i listen én gang for apparatet selv og én gang for hver variant (APP-006). Hvert apparat skal knyttes til en entitet (GEN-013). Apparatets navn er navnet i Home Assistant, og identifiserer apparatet i listen og på statussiden.
Relatert: GEN-013, REG-007, REG-008, REG-010, APP-005, APP-006, APP-008, GUI-009.

**APP-002 Handling for å slå på**
Hvert apparat skal ha en konfigurerbar handling som slår det på.

**APP-003 Handling for å slå av**
Hvert apparat skal ha en konfigurerbar handling som slår det av.

**APP-004 Effektreserve**
Hvert apparat skal kunne ha en valgfri effektreserve, uten grenseverdier. Er den ikke angitt, gjelder bare det første vilkåret i REG-006.
Begrunnelse: Et apparat som trekker mye straks det slås på, for eksempel en bassengvarmer på 4 kW, kan ellers bli slått på når det er for lite ledig effekt. Da slås det av og på gjentatte ganger og kan over tid utløse straff. For mange apparater er forbruket ukjent, så verdien kan ikke kreves.
Relatert: REG-006.

**APP-005 Elbillading i prioritetslisten**
Når billadestyring er aktivert, skal prioritetslisten inneholde elementet «Elbillading». Det skal kunne sorteres som et vanlig apparat, men ikke konfigureres fra listen. Plasseringen bestemmer hvor i prioritetsrekkefølgen alle de fiktive apparatene for elbilladerne ligger.
Relatert: APP-001, LAD-001, LAD-011.

**APP-006 Varianter av et apparat**
Hvert vanlig apparat skal kunne ha varianter med alternativ prioritet. Varianter gjelder ikke elbilladere og ikke elementet «Elbillading» (APP-005).
- Under konfigureringen av apparatet skal brukeren kunne legge til uttrykk i en sortert rekkefølge, og kunne endre rekkefølgen og fjerne uttrykk.
- Hvert uttrykk skal angis etter GEN-009: som en boolsk entitet eller en mal.
- Hvert uttrykk definerer én variant i tillegg til apparatet selv. Varianten skal ha en merkelapp (tekst) som ikke er tom og som er unik blant apparatets varianter. Merkelappen identifiserer varianten i prioritetslisten.
- En variant har samme handlinger og samme effektreserve som apparatet (APP-002 til APP-004). Bare plassen i prioritetslisten er alternativ.

Eksempel: Varmtvannsberederen har varianten «Morgen» med en mal som er sann mellom klokken 05 og 08.
Begrunnelse: Et apparat kan trenge ulik prioritet under ulike forhold, for eksempel høyere prioritet om morgenen.
Relatert: GEN-009, GEN-010, APP-001, APP-007, APP-008, GUI-009.

**APP-007 Gjeldende variant**
For hvert apparat med varianter skal nøyaktig én variant gjelde til enhver tid: den gjeldende varianten.
- Gjeldende variant er varianten til det øverste uttrykket som er sant.
- Er ingen av uttrykkene sanne, er apparatet uten variant den gjeldende.

Gjeldende variant skal vurderes ved hver avgjørelse (REG-005). Bare oppføringen for den gjeldende varianten skal være med i prioriteringen og reguleringen. De øvrige oppføringene for apparatet skal hoppes over (REG-007, REG-008).
Relatert: GEN-009, REG-005, REG-007, REG-008, APP-006, APP-009.

**APP-008 Varianter i prioritetslisten**
Hver variant skal stå som en egen oppføring i prioritetslisten (APP-001), identifisert ved apparatets navn og variantens merkelapp. Hver oppføring skal kunne sorteres uavhengig av de andre oppføringene for samme apparat. En ny variant skal stå nederst i listen til brukeren sorterer den. En variant som slettes, skal fjernes fra listen.
Relatert: APP-001, APP-006, GUI-009.

**APP-009 Bytte av gjeldende variant**
Bytter et apparat gjeldende variant ved en avgjørelse, skal reguleringen sørge for at byttet ikke gir en større endring i forbruket enn nødvendig, og ikke fører til at flere apparater står på enn reguleringen har gitt rom for.
- Apparatet skal etter byttet være avslått og stå på plassen til den nye gjeldende varianten. Det slås deretter på igjen på vanlig måte (REG-007, REG-012).
- Var apparatet av før byttet, og får det en plass som er høyere enn plassen til det laveste prioriterte apparatet som er på, skal dette laveste prioriterte apparatet slås av for å gi plass.
- Ventetiden og telleren for økende ventetid (REG-015) for apparatet skal nullstilles.
- Utkoblingene skjer ved samme avgjørelse som byttet, som unntak fra REG-004.

Eksempel: A, B og C er på, og D er av. D bytter variant og får en plass over C. C slås av for å gi plass til D, og D settes inn over C. D slås på igjen på vanlig måte.
Begrunnelse: Et apparat som får høyere prioritet enn det laveste prioriterte apparatet som er på, ville ellers slås på i tillegg til de som allerede er på. Det gir ekstra forbruk og for mange påslåtte apparater. Løsningen tar ikke hensyn til apparatets faktiske tilstand (GEN-006), så et avslått apparat gir en kjent tilstand før det får ny plass.
Relatert: GEN-006, REG-004, REG-005, REG-007, REG-012, REG-015, APP-007.

### 4.7 LAD – Elbillading

En elbillader håndteres spesielt. Brukeren forholder seg til én elbillader, men for reguleringen deles den internt opp i fiktive apparater for elbillader, ett for hvert ampere i ladestrømmen. De generelle reglene for apparater (REG) gjelder for hvert fiktivt apparat. Løsningen kan styre én elbillader om gangen eller flere samtidig. Rekkefølgen mellom elbilladerne følger en gjeldende ladeprioritering som oppdateres for hvert reguleringsintervall. En elbillader lader bare når reguleringen har aktivert den, slik at en ny bil aldri starter lading på egen hånd. Hver elbillader kan begrenses til et ladetidsrom, som brukeren kan overstyre. Alle vurderinger og endringer for elbilladerne skjer ved avgjørelsene (REG-005).

#### 4.7.1 Felles innstillinger

**LAD-001 Aktivering av billadestyring**
Billadestyring skal kunne aktiveres og deaktiveres. Standard er deaktivert. Når billadestyring deaktiveres, skal elbilladerne overlates til seg selv (GEN-008).
Relatert: GEN-008, REG-010, APP-005, GUI-010.

**LAD-002 Én elbillader om gangen**
Det skal kunne velges om bare én elbillader kan lade om gangen. Standard er ja.
Relatert: LAD-015, LAD-021, LAD-022, LAD-023, LAD-029.

**LAD-003 Elbilladerliste**
Elbilladerne skal konfigureres i en sorterbar liste der rekkefølgen er den konfigurerte ladeprioriteringen, med høyest prioritet øverst. Hver elbillader skal knyttes til en entitet (GEN-013). Elbilladerens navn er navnet i Home Assistant, og identifiserer elbilladeren i listen, på statussiden og i entitetene (ENT-003 og ENT-004).
Relatert: GEN-013, REG-010, LAD-015, LAD-016, LAD-022, GUI-010.

#### 4.7.2 Innstillinger per elbillader

Hver elbillader styres på to måter, begge med handlinger som brukeren konfigurerer. Den ene avgjør om elbilladeren har lov til å lade (tillatt lading). Normalt gjøres det ved å slå laderen på og av. Den andre avgjør hvor høy ladestrømmen er, i ampere, mellom en minste og en største ladestrøm som brukeren angir.

**LAD-004 Deaktivering av elbillader**
Hver elbillader skal ha en konfigurerbar handling som deaktiverer den, det vil si ikke tillater lading, slik at den ikke starter lading selv om en bil er tilkoblet. Normalt er handlingen å slå laderen av. Hver gang en elbillader deaktiveres, uansett årsak, skal ladestrømmen først settes til minste ladestrøm (LAD-006), og deretter skal handlingen for deaktivering utføres.
Relatert: LAD-005, LAD-006, LAD-011, LAD-013, LAD-019, LAD-023, LAD-028, LAD-029.

**LAD-005 Aktivering av elbillader**
Hver elbillader skal ha en konfigurerbar handling som aktiverer den, det vil si tillater lading. Normalt er handlingen å slå laderen på.
Relatert: LAD-004, LAD-011, LAD-012.

**LAD-006 Innstilling av ladestrøm**
Hver elbillader skal ha en konfigurerbar handling som setter ladestrømmen i ampere. Løsningen skal oppgi tre verdier som parametere som handlingen kan bruke i en mal: ladestrømmen som skal settes, og elbilladerens minste og største ladestrøm (LAD-007). Ladestrømmen som skal settes, skal alltid ligge mellom minste og største.
Relatert: LAD-007, LAD-011, LAD-012, LAD-013.

**LAD-007 Grenser for ladestrøm**
Hver elbillader skal ha en konfigurerbar minste og største tillatte ladestrøm, angitt som hele ampere. Minste ladestrøm skal ikke være større enn største.
Eksempel: Typiske verdier er minste 6 A og største 16 A, eller minste 6 A og største 23 A.
Relatert: LAD-006, LAD-011.

**LAD-008 Ladeeffekt**
Hver elbillader skal ha en konfigurerbar sensor for målt ladeeffekt, og sensoren er påkrevd. En elbillader regnes som aktivt ladende når siste verdi fra sensoren ved avgjørelsen er over 100 W. Terskelen på 100 W skal ikke kunne konfigureres. Reguleringen bruker verdien som bevis for at elbilladeren ikke lader. Er verdien utilgjengelig eller ugyldig (MAL-007), finnes det ikke bevis, og elbilladeren regnes som aktivt ladende (GEN-010).
Relatert: GEN-006, GEN-010, MAL-007, LAD-017, LAD-018, LAD-021, LAD-022.

**LAD-009 Effektreserve for elbillader**
Hver elbillader skal ha en konfigurerbar effektreserve: effekten elbilladeren trekker når lading starter på minste ladestrøm. Standard er 4 kW, og gyldig område er 0–5 kW. Verdien 0 betyr at elbilladeren kan starte så snart det er ledig effekt.
Begrunnelse: Verdien kan ikke beregnes, fordi ladestandarden bare angir grenser i ampere og effekten avhenger av antall faser og spenning. 4 kW tilsvarer omtrent 6 A på tre faser, 400 V.
Relatert: LAD-012, LAD-015, GUI-010.

**LAD-010 Bil tilkoblet**
Hver elbillader skal kunne ha en valgfri innstilling for om en bil er tilkoblet. Innstillingen skal angis etter GEN-009. Er den ikke angitt, skal den ikke påvirke reguleringen. Er den angitt, regnes en bil som tilkoblet bare når verdien er sann.
Relatert: GEN-009, GEN-010, LAD-017, LAD-023.

#### 4.7.3 Fiktive apparater for elbillader

**LAD-011 Fiktive apparater for elbillader**
Løsningen skal internt dele hver elbillader opp i fiktive apparater for elbillader, ett for hvert heltall i ampere fra minste til største ladestrøm. Reguleringen skal behandle hvert fiktivt apparat som et apparat. De fiktive apparatene er gitt av elbilladerens egenskaper og skal ikke kunne prioriteres eller konfigureres av brukeren.
Et fiktivt apparat har ingen egne handlinger. Det slås på og av ved at elbilladeren styres med sine egne handlinger (LAD-004 til LAD-006), som beskrevet i LAD-012 og LAD-013. Ladestrømmen skal til enhver tid være minste ladestrøm pluss antall fiktive apparater som er på, minus ett. Er ingen på, er elbilladeren deaktivert.
Eksempel: Med minste ladestrøm 6 A og største 16 A har elbilladeren 11 fiktive apparater. Er fire av dem på, er ladestrømmen 9 A.
Relatert: REG-004, APP-005, LAD-004, LAD-005, LAD-006, LAD-007, LAD-012, LAD-013, LAD-015.

**LAD-012 Økning av ladestrøm**
Ladestrømmen skal økes med ett ampere for hvert fiktivt apparat som slås på:
- Slås det første fiktive apparatet på, skal ladestrømmen først settes til minste ladestrøm (LAD-006), og deretter skal elbilladeren aktiveres (LAD-005).
- Slås et senere fiktivt apparat på, skal handlingen for ladestrøm (LAD-006) utføres med den nye ladestrømmen (LAD-011).

Effektreserven for det første fiktive apparatet er elbilladerens effektreserve (LAD-009). Øvrige fiktive apparater skal ikke ha effektreserve.
Relatert: REG-006, LAD-005, LAD-006, LAD-009, LAD-011, LAD-014, LAD-028.

**LAD-013 Reduksjon av ladestrøm**
Ladestrømmen skal reduseres med ett ampere for hvert fiktivt apparat som slås av:
- Er det fortsatt fiktive apparater på, skal handlingen for ladestrøm (LAD-006) utføres med den nye ladestrømmen (LAD-011).
- Slås det siste fiktive apparatet som er på, av, skal elbilladeren deaktiveres (LAD-004).

En elbillader som ikke har noen fiktive apparater på, skal være deaktivert og ikke få lade.
Relatert: REG-008, STR-003, LAD-004, LAD-006, LAD-011, LAD-028.

**LAD-014 Ventetid for fiktive apparater**
Kravene til ventetid (REG-012 til REG-014) og økende ventetid ved vedvarende pendling (REG-015) skal gjelde for hvert fiktivt apparat i en elbillader, på samme måte som for andre apparater, med disse unntakene ved vedvarende pendling:
- ventetiden skal øke med 5 minutter for hver gang, ikke 2 minutter, og
- ventetiden skal være høyst 30 minutter, ikke 15 minutter.

Eksempel med standardverdien for ventetid ved effektgrensen: ventetiden blir 5, 10, 15, 20, 25 og deretter 30 minutter.

Siden hvert fiktivt apparat har egen ventetid og høyst ett apparat slås på per avgjørelse (REG-004), tar det minst ett reguleringsintervall per ampere å øke ladestrømmen fra minste til største verdi.
Begrunnelse: Elbilen skal få så stabil strømtilførsel som mulig, ikke en ladestrøm som stadig endres.
Relatert: LAD-011, LAD-012, LAD-013, REG-012, REG-013, REG-014, REG-015.

**LAD-015 Flere elbilladere samtidig**
Når flere elbilladere kan lade samtidig, skal de fiktive apparatene fordeles i tur mellom elbilladerne. Først får hver elbillader sitt første fiktive apparat slått på i rekkefølgen i gjeldende ladeprioritering (LAD-016), deretter sitt andre, og så videre. Eksempel med tre elbilladere: elbillader 1 apparat 1, elbillader 2 apparat 1, elbillader 3 apparat 1, elbillader 1 apparat 2, og så videre. Effektreserven skal gjelde for hver elbilladers første fiktive apparat.
Relatert: LAD-002, LAD-003, LAD-009, LAD-011, LAD-016, LAD-017.

#### 4.7.4 Prioritering mellom elbilladere

Reglene i dette avsnittet gjelder uansett om bare én elbillader kan lade om gangen eller flere kan lade samtidig. Med prioritering menes her gjeldende ladeprioritering, ikke den konfigurerte.

**LAD-016 Gjeldende ladeprioritering**
I tillegg til den konfigurerte ladeprioriteringen (LAD-003) skal løsningen ha en gjeldende ladeprioritering. Gjeldende ladeprioritering skal være lik den konfigurerte ved hver start av regulering (REG-009). Den skal deretter oppdateres ved hver avgjørelse etter LAD-018 og LAD-020, og kan avvike fra den konfigurerte. Reguleringen skal bruke gjeldende ladeprioritering, ikke den konfigurerte, til å avgjøre rekkefølgen mellom elbilladerne, både når fiktive apparater slås på og når de slås av.
Relatert: REG-005, REG-009, LAD-003, LAD-015, LAD-017, LAD-018, LAD-020.

**LAD-017 Forbigått elbillader**
En elbillader som ikke trekker strøm, skal regnes som forbigått. Om en elbillader er forbigått, skal vurderes på nytt ved hver avgjørelse. Elbilladeren er forbigått når ett av disse vilkårene er oppfylt:
- verdien for bil tilkoblet (LAD-010) er usann, eller
- elbilladeren er ikke aktivt ladende (LAD-008), og dens første fiktive apparat har vært på i minst to ganger reguleringsvinduet.

Er verdien for bil tilkoblet ikke angitt, gjelder bare det siste vilkåret. Elbilladeren slutter å være forbigått så snart ingen av vilkårene lenger er oppfylt, for eksempel når en bil kobles til eller når den begynner å trekke strøm. Så lenge en elbillader er forbigått, skal ikke flere av dens fiktive apparater slås på, reguleringen skal ikke slå av dens fiktive apparater ved overskridelse (REG-008), og den skal ikke hindre at andre elbilladere får lade.
Begrunnelse: Ellers blir alle fiktive apparater for en elbillader som ikke trekker strøm, slått på, fordi forbruket aldri øker. Å slå dem av igjen reduserer heller ikke forbruket. En bil kan være tilkoblet uten å trekke strøm, for eksempel med fullt batteri eller når den står ubrukt i garasjen i flere dager.
Relatert: REG-005, REG-007, REG-008, MAL-002, LAD-008, LAD-010, LAD-015, LAD-018, LAD-019, LAD-030.

**LAD-018 Forbigått elbillader har lavere prioritet**
I gjeldende ladeprioritering skal en forbigått elbillader alltid ha lavere prioritet enn en elbillader som ikke er forbigått, herunder en aktivt ladende elbillader. Når en elbillader blir forbigått, skal den flyttes bakerst i gjeldende ladeprioritering, og den skal bli stående der også etter at den ikke lenger er forbigått, helt til gjeldende ladeprioritering rettes etter LAD-020. Blir flere elbilladere forbigått samtidig, beholder de rekkefølgen de hadde i gjeldende ladeprioritering. Det gjelder uansett om bare én elbillader kan lade om gangen eller flere kan lade samtidig, og uansett hva som er konfigurert.
Begrunnelse: Konseptet skal gjelde generelt, slik at alle situasjoner med elbilladere som ikke trekker strøm, håndteres likt. Ellers stopper all lading opp når den høyest prioriterte elbilladeren står uten bil.
Relatert: LAD-008, LAD-016, LAD-017, LAD-020, LAD-021.

**LAD-019 Forbigått elbillader deaktiveres ikke**
En aktivert elbillader skal ikke deaktiveres bare fordi den er forbigått. Den beholder sitt første fiktive apparat på (LAD-030) og kan dermed starte lading når bilen begynner å trekke strøm eller en annen elbillader slutter å lade. Unntaket er når bare én elbillader kan lade om gangen og en annen elbillader aktiveres (LAD-029).
Relatert: LAD-004, LAD-013, LAD-017, LAD-023, LAD-029, LAD-030.

**LAD-020 Retting av gjeldende ladeprioritering**
Når en elbillader har alle sine fiktive apparater på, skal gjeldende ladeprioritering rettes mot den konfigurerte ladeprioriteringen. Rettingen går ut på å sette gjeldende ladeprioritering lik den konfigurerte for elbilladere som ikke er forbigått. Elbilladere som er forbigått, står fortsatt bakerst.
Eksempel: Konfigurert ladeprioritering er A, B. A står uten bil og er forbigått, så gjeldende ladeprioritering er B, A. B får alle sine fiktive apparater på. A er ikke slått på og får ikke trekke strøm, siden den midlertidig har lavere prioritet enn B. Kobles det så en bil til A, rettes gjeldende ladeprioritering til A, B. A får da første prioritet til å bli slått på, og B reduseres først hvis det blir for lite ledig effekt.
Relatert: LAD-003, LAD-016, LAD-017, LAD-018.

#### 4.7.5 Én elbillader om gangen

**LAD-021 Aktivt ladende elbillader går foran**
Når bare én elbillader kan lade om gangen, skal en aktivt ladende elbillader få fortsette å lade så lenge den lader, uansett konfigurert ladeprioritering.
Relatert: LAD-002, LAD-008, LAD-018, LAD-022, LAD-023.

**LAD-022 Valg av elbillader**
Når bare én elbillader kan lade om gangen og ingen elbillader lader aktivt, skal gjeldende ladeprioritering (LAD-016) avgjøre hvilken elbillader som først får slått på sine fiktive apparater.
Relatert: LAD-003, LAD-016, LAD-021.

**LAD-023 Ventende elbillader**
Når bare én elbillader kan lade om gangen og en elbillader lader aktivt, skal en bil som kobles til en annen elbillader, ikke få lade, uansett hvilken prioritet den andre elbilladeren har (LAD-028). Elbilladeren er da en ventende elbillader. Om en elbillader er ventende, skal vurderes ved hver avgjørelse. Den ventende elbilladeren skal ikke få lade før den aktivt ladende elbilladeren slutter å lade, fordi bilen er koblet fra eller ferdig ladet. Dette gjelder uansett rekkefølgen i elbilladerlisten.
Relatert: LAD-002, LAD-010, LAD-019, LAD-021, LAD-028, LAD-029.

#### 4.7.6 Del av reguleringen og ladetidsrom

**LAD-024 Elbillader midlertidig utenfor reguleringen**
Når en elbillader midlertidig er utenfor reguleringen (ENT-003), skal ingen av dens fiktive apparater slås på, og bilen skal aldri lades. Pågående lading skal stoppes ved første avgjørelse etter at elbilladeren er tatt ut av reguleringen: alle dens fiktive apparater slås av samtidig, og elbilladeren deaktiveres.
Relatert: ENT-003, REG-004, REG-005, REG-007.

**LAD-025 Ladetidsrom**
Hver elbillader skal kunne ha ett valgfritt ladetidsrom i døgnet. Ladetidsrommet skal kunne strekke seg over midnatt. Det angis med start og slutt som klokkeslett i hele minutter, i Home Assistants tidssone. Start og slutt skal ikke være like. Utenfor ladetidsrommet skal elbilladeren ikke lade. Pågående lading skal stoppes ved første avgjørelse etter at ladetidsrommet slutter: alle dens fiktive apparater slås av samtidig, og elbilladeren deaktiveres.
Begrunnelse: Gjøre det mulig å lade bare om natten, når nettleien er lavere.
Relatert: REG-004, REG-005, REG-007, LAD-026, LAD-027, GUI-010.

**LAD-026 Uten ladetidsrom**
En elbillader uten angitt ladetidsrom skal alltid ha lov til å lade, med mindre den midlertidig er utenfor reguleringen (ENT-003).
Relatert: LAD-024, LAD-025, ENT-003.

**LAD-027 Overstyring av ladetidsrom**
Når overstyring er slått på for en elbillader (ENT-004), skal den ha lov til å lade også utenfor ladetidsrommet. Overstyringen skal opphøre automatisk ved første avgjørelse etter at neste ladetidsrom har startet, slik at den ikke gjelder neste dag. Over en omstart bevares stillingen (GEN-011), men ikke når overstyringen ble slått på (GEN-007). Etter en omstart opphører overstyringen derfor ved første avgjørelse etter at neste ladetidsrom har startet etter omstarten. Har elbilladeren ikke ladetidsrom (LAD-026), har overstyringen ingen virkning. Slås overstyringen av, stoppes pågående lading utenfor ladetidsrommet på samme måte som i LAD-025.
Begrunnelse: Gjøre det mulig å tillate lading midt på dagen ved behov.
Relatert: GEN-007, GEN-011, REG-005, LAD-025, ENT-004.

#### 4.7.7 Ny bil og samtidig lading

En ny bil som kobles til en elbillader, må ikke føre til at to elbilladere lader samtidig og at forbruket plutselig øker. Det forstyrrer reguleringen og skal unngås, særlig når bare én elbillader kan lade om gangen. Kravene i dette avsnittet løser det i reguleringen.

**LAD-028 Ingen lading uten lov fra reguleringen**
En elbillader skal bare kunne lade når reguleringen har aktivert den, det vil si når minst ett av dens fiktive apparater er på. Alle andre elbilladere skal være deaktivert (LAD-013), slik at en bil som kobles til en deaktivert elbillader, ikke begynner å lade av seg selv. Reguleringen skal først aktivere en elbillader når den står for tur etter gjeldende ladeprioritering og vilkårene for å slå på dens første fiktive apparat er oppfylt (REG-006, REG-012), slik at effektreserve er satt av til oppstarten.
Eksempel: Konfigurert ladeprioritering er A, B, og B lader. En ny bil kobles til A, som har høyere prioritet enn B. A er deaktivert, så bilen begynner ikke å lade. Når bare én elbillader kan lade om gangen, er A en ventende elbillader til B er ferdig (LAD-023). Når flere kan lade samtidig, får A sitt første fiktive apparat slått på først når reguleringen har ledig effekt og effektreserve til det. I begge tilfeller øker ikke forbruket plutselig.
Begrunnelse: Starter to elbilladere samtidig, øker forbruket brått, og det forstyrrer reguleringen.
Relatert: REG-006, REG-012, LAD-004, LAD-009, LAD-012, LAD-013, LAD-023, LAD-029.

**LAD-029 Én aktivert elbillader om gangen**
Når bare én elbillader kan lade om gangen, skal det aldri være mer enn én aktivert elbillader. Før en elbillader aktiveres, det vil si før dens første fiktive apparat slås på, skal enhver annen aktivert elbillader deaktiveres ved samme avgjørelse, og alle dens fiktive apparater slås av. Det kan bare gjelde en forbigått elbillader, siden en aktivt ladende elbillader går foran (LAD-021).
Begrunnelse: En forbigått elbillader står aktivert uten å trekke strøm. Hvis en ny bil kobles til den, eller bilen begynner å lade igjen, mens en annen elbillader er aktivert, lader to elbilladere samtidig.
Relatert: REG-004, LAD-002, LAD-004, LAD-019, LAD-021, LAD-023, LAD-028.

**LAD-030 Forbigått elbillader begrenses til minste ladestrøm**
Når en elbillader blir forbigått, skal alle dens fiktive apparater utenom det første slås av ved samme avgjørelse, hvis flere er på. Så lenge elbilladeren er forbigått, skal ikke flere fiktive apparater slås på. Slik kan en bil som kobles til, eller som begynner å lade igjen, høyst trekke minste ladestrøm, ikke den høye ladestrømmen elbilladeren sto på før.
Begrunnelse: Uten dette kan en ny bil som kobles til en forbigått elbillader med høy ladestrøm, få forbruket til å øke brått og forstyrre reguleringen.
Relatert: REG-004, LAD-007, LAD-009, LAD-017, LAD-019.

### 4.8 ENT – Eksponerte entiteter

**ENT-001 Sensor for reguleringssnitt**
Reguleringssnittet skal eksponeres som en sensor som andre integrasjoner og dashbord kan bruke. Sensoren skal oppdateres hver gang et nytt reguleringssnitt er beregnet. Verdien oppgis i kW.
Relatert: MAL-001.

**ENT-002 Sensor for snittforbruk**
Snittforbruket skal eksponeres som en sensor som andre integrasjoner og dashbord kan bruke. Sensoren skal oppdateres hver gang et nytt reguleringssnitt er beregnet. Verdien oppgis i kW.
Relatert: MAL-003.

**ENT-003 Elbillader midlertidig utenfor reguleringen**
For hver elbillader skal løsningen lage en entitet som brukeren kan slå av og på, og som er på når elbilladeren midlertidig er tatt ut av reguleringen. Er den på, skal bilen aldri lades. Standard er av. Stillingen er konfigurasjon og bevares over enhver form for omstart (GEN-011). Brytere kan brukes mens reguleringen kjører, og endringen trer i kraft ved første avgjørelse (LAD-024).
Begrunnelse: Å ta en elbillader ut av reguleringen er et unntak som brukeren må velge aktivt. En utilgjengelig verdi skal derfor ikke ta den ut, og valget skal ikke forsvinne av seg selv.
Relatert: GEN-007, GEN-011, REG-010, LAD-024, LAD-026.

**ENT-004 Overstyring av ladetidsrom**
For hver elbillader skal løsningen lage en entitet som brukeren kan slå av og på, og som overstyrer ladetidsrommet. Standard er av. Stillingen er konfigurasjon og bevares over enhver form for omstart (GEN-011). Entiteten skal settes tilbake til av når overstyringen opphører (LAD-027). Bryteren kan brukes mens reguleringen kjører.
Relatert: GEN-007, GEN-011, REG-010, LAD-027.

**ENT-005 Varsel om sikker tilstand**
Løsningen skal eksponere en sann/usann-sensor som er sann så lenge reguleringen er i sikker tilstand (REG-011). Sensoren skal kunne brukes som utløser i automasjoner, for eksempel for å varsle brukeren.
Begrunnelse: Når effektsensoren faller bort, er alle regulerte apparater avslått. Brukeren bør få vite det.
Relatert: REG-011.

**ENT-006 Bryter for regulering**
Løsningen skal eksponere en bryter som starter og stopper reguleringen (REG-016). Bryteren er på så lenge reguleringen kjører. Bryteren har ingen lagret stilling: Etter start av Home Assistant eller integrasjonen kjører reguleringen, og bryteren er på (REG-016). Bryteren og start/stopp i panelet (GUI-007) skal henge sammen: slås reguleringen av eller på i panelet, skal bryteren endre status, og omvendt.
Begrunnelse: Gjør det mulig å starte og stoppe reguleringen fra dashbord og automasjoner.
Relatert: GEN-007, REG-016, GUI-007.

### 4.9 GUI – Brukergrensesnitt

Brukergrensesnittet er alt Kraftvakt viser i panelet som legges til i sidemenyen i Home Assistant. Kravene i denne kategorien gjelder visningen i panelet. Hva som kan konfigureres, og hvordan reguleringen virker, er beskrevet i de andre kategoriene.

#### 4.9.1 Panel og navigasjon

**GUI-001 Eget panel**
Løsningen skal legge til et eget panel i sidemenyen i Home Assistant. All konfigurasjon av Kraftvakt og all visning av reguleringens status skal skje i panelet. Panelet skal bare være tilgjengelig for administratorer i Home Assistant.
Relatert: GUI-002, GUI-003, GUI-004.

**GUI-002 Toppmeny**
Panelet skal ha en meny øverst, som er synlig på alle sider i panelet. Menyen skal la brukeren velge mellom statussiden (GUI-005) og konfigurasjonssidene (GUI-008 til GUI-010).
Relatert: GUI-001, GUI-005, GUI-008, GUI-009, GUI-010.

**GUI-003 Åpning fra konfigureringsknappen**
Når brukeren trykker på konfigureringsknappen for Kraftvakt i Home Assistant, skal Home Assistants standard konfigurasjonsdialog for integrasjoner ikke vises. I stedet skal Home Assistant åpne Kraftvakts panel og gå til konfigurasjonssiden for apparater og prioritetsliste (GUI-009).
Begrunnelse: All konfigurasjon gjøres i panelet (GUI-001).
Relatert: GUI-001, GUI-004, GUI-009.

**GUI-004 Ingen innstillinger ved tilføyelse av integrasjonen**
Når brukeren legger til Kraftvakt som integrasjon i Home Assistant, skal brukeren ikke måtte gjøre noen innstillinger i Home Assistants standarddialog for å legge til integrasjoner. Konfigurasjonen skal gjøres i panelet (GUI-001).
Begrunnelse: All konfigurasjon gjøres på ett sted.
Relatert: GUI-001, GUI-003.

#### 4.9.2 Statusside

Statussiden gir brukeren oversikt over hvordan reguleringen står akkurat nå.

**GUI-005 Statusside**
Panelet skal ha en statusside som viser status for reguleringen. Statussiden skal alltid vise om reguleringen kjører eller er stoppet (REG-016). Er konfigurasjonen ikke fullstendig, skal statussiden vise hva som mangler.
Relatert: GUI-002, GUI-006, GUI-007, REG-016.

**GUI-006 Status mens reguleringen kjører**
Mens reguleringen kjører, skal statussiden i tillegg vise:
- om reguleringen er i sikker tilstand (REG-011),
- om en straffeperiode pågår (STR-001),
- gjeldende reguleringssnitt (MAL-001) og snittforbruk (MAL-003), sammen med effektgrensen (REG-001),
- for hvert apparat i konfigurasjonen om det er på eller av (GEN-006), og hvilken variant som gjelder (APP-007), og
- for hver elbillader om den er aktivert (LAD-012).

Relatert: GEN-006, MAL-001, MAL-003, REG-001, REG-011, STR-001, APP-007, LAD-012, GUI-005.

**GUI-007 Start og stopp**
Statussiden skal la brukeren stoppe og starte reguleringen (REG-016). Statusen og start/stopp skal henge sammen med bryteren (ENT-006): slås reguleringen av eller på med bryteren, skal statussiden endre status, og omvendt.
Relatert: REG-016, ENT-006, GUI-005, GUI-012.

#### 4.9.3 Konfigurasjonssider

Konfigurasjonen er delt på konfigurasjonssider. Hva hver innstilling betyr, er beskrevet i kravene det henvises til.

**GUI-008 Generelle parametere**
Konfigurasjonssiden for generelle parametere skal samle: effektsensor (GEN-003), effektgrense (REG-001), reguleringsvindu (MAL-002), reguleringsintervall (REG-002), ventetid ved effektgrensen (REG-014) og straffeterskel (STR-002).
Relatert: GUI-002, GUI-012.

**GUI-009 Apparater og prioritetsliste**
Konfigurasjonssiden for apparater og prioritetsliste skal la brukeren definere og konfigurere apparatene (APP-002 til APP-004), med varianter (APP-006), velge entitet for hvert apparat (GEN-013) og sortere prioritetslisten (APP-001).
Relatert: APP-001, APP-006, GUI-002, GUI-003, GUI-011, GUI-012.

**GUI-010 Billading**
Konfigurasjonssiden for billading skal samle all konfigurasjon av billading. Det gjelder de felles innstillingene (LAD-001 til LAD-003) og innstillingene per elbillader (LAD-004 til LAD-010 og LAD-025).
Relatert: GUI-002, GUI-011, GUI-012.

**GUI-011 Advarsel om manuell styring**
Konfigurasjonssidene for apparater og prioritetsliste (GUI-009) og for billading (GUI-010) skal vise en kort advarsel om at brukeren ikke bør slå regulerte apparater av eller på utenom Kraftvakt. Advarselen skal si at manuell styring kan forstyrre reguleringen, kan gå ut over apparater med høyere prioritet og kan utløse straff.
Begrunnelse: Kraftvakt tar ikke hensyn til styring utenom Kraftvakt (GEN-006) og kan ikke rette den opp.
Relatert: GEN-006, GUI-009, GUI-010.

**GUI-012 Låst konfigurasjon**
Mens reguleringen kjører, skal konfigurasjonen være låst (REG-010). Alle konfigurasjonssider skal da vise at konfigurasjonen er låst, og at reguleringen må stoppes før den kan endres.
Relatert: REG-010, REG-016, GUI-007, GUI-008, GUI-009, GUI-010.
