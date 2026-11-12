# /// script
# requires-python = ">=3.11"
# dependencies = ["numpy"]
# ///
"""Named places of Tongelre: style overrides and extra geometry for buildings, plus the viewer's place list.

Sources: the erfgoedborden and the monumentenlijst of the gemeente Eindhoven (data.eindhoven.nl, publiek domein), the
Rijksmonumentenregister via Wikidata (CC0), OpenStreetMap (ODbL) and AHN for tower positions and heights.

Output: data/build/landmarks.json
"""

import json

import numpy as np

from config import BUILD, PLACE, RAW
from geo import wgs_to_rd

# Erfgoedborden van de gemeente Eindhoven: het bord zelf staat bij het gebouw, de tekst staat online.
BORD = "https://data.eindhoven.nl/explore/dataset/erfgoedbordjes/"
MON = "https://beeldmateriaal.eindhoven.nl/monumenten/"  # de monumentbeschrijvingen van de gemeente, als pdf

# Buildings found by an address or point; `pand` is resolved to the 3D BAG building under that point.
BUILDINGS = [
    # --- De dorpskern: 't Hofke, de hoefijzervormige straat die tot 1920 Marktstraat heette -------------------
    {
        "name": "Sint-Martinuskerk",
        "stop": "De Sint-Martinuskerk",
        "note": "Driebeukige neogotische kruisbasiliek; de twee torens naast het portaal zijn nooit afgebouwd",
        "kind": "Rijksmonument · 1917",
        "addr": "'t Hofke 1",
        "address": "'t Hofke 1",
        "text": "De kerk staat op de plek waar Tongelre al sinds de dertiende eeuw om een kerk heen ligt: op de hoge grond langs de Dommel, aan de binnenbocht van 't Hofke. De huidige kerk is een driebeukige neogotische kruisbasiliek; de twee torens die het hoofdportaal zouden flankeren zijn nooit voltooid, zodat het front laag bleef en het schip des te langer lijkt. De pastorie staat er met de kerk onder één dak aan vast; op de gevel staat een Goede Herder van de Eindhovense beeldhouwer Jan Custers uit 1918.",
        "more": "https://nl.wikipedia.org/wiki/Sint-Martinuskerk_(Tongelre)",
        "style": "church",
        "wall": (150, 84, 66),
        "roof": (74, 76, 84),
    },
    {
        "name": "Oude raadhuis van Tongelre",
        "stop": "Het raadhuis van Tongelre",
        "note": "Het laatste gemeentehuis van de zelfstandige gemeente Tongelre, nu buurthuis 't Oude Raadhuis",
        "kind": "Rijksmonument · 1911",
        "addr": "'t Hofke 15",
        "address": "'t Hofke 15",
        "text": "Op 1 januari 1920 werden Tongelre, Stratum, Gestel, Strijp en Woensel bij het stadje Eindhoven gevoegd, dat ruimte nodig had: Eindhoven had toen 6.500 inwoners, Tongelre 3.200. Dit pand uit 1911 was het laatste gemeentehuis van Tongelre. Zowel de inwoners als het gemeentebestuur waren tegen de annexatie: ze vreesden hogere belastingen, een dorp dat door de stad werd opgeslokt en meer criminaliteit. Het heeft niet geholpen. Het gebouw doet nog altijd dienst voor het buurtleven.",
        "more": BORD,
        "style": "house",
        "wall": (152, 92, 72),
        "roof": (70, 72, 80),
        "frame": (238, 236, 228),
    },
    {
        "name": "Boerderij van Poppel",
        "stop": "De boerderij van Van Poppel",
        "note": "Driebeukig hallehuis uit 1584, een van de oudste panden van Eindhoven",
        "kind": "Rijksmonument · 1584",
        "addr": "'t Hofke 13",
        "address": "'t Hofke 13",
        "text": "Een van de oudste panden van Eindhoven, uit 1584: een driebeukig hallehuis met een brede middenbeuk en twee smalle zijbeuken, woonhuis en stal onder één dak. Rond 1600 kwam er een opkamer met kelder bij, in de achttiende eeuw werden de kopgevel, de straatgevel en de stal vernieuwd. De boerderij stond pal aan het inmiddels verdwenen dorpsplein van Tongelre, naast het raadhuis. Bij een opgraving in 1993 kwam er een afvalkuil naast tevoorschijn met zeventiende-eeuws Delfts aardewerk en gebrandschilderd glas.",
        "more": BORD,
        "style": "house",
        "wall": (140, 118, 96),
        "roof": (82, 70, 62),
    },
    {
        "name": "Oude pastorie ('t Hofke 22)",
        "kind": "Gemeentelijk monument · eind 18e eeuw",
        "addr": "'t Hofke 22",
        "address": "'t Hofke 22",
        "text": "De pastorie van vóór de huidige kerk, uit het eind van de achttiende eeuw, aan de buitenbocht van 't Hofke.",
        "more": MON + "GM0026.pdf",
    },
    {
        "name": "Looiershuis (Oude Urkhovenseweg 2)",
        "note": "Zestiende-eeuws huis van een leerlooier",
        "kind": "Gemeentelijk monument · 16e eeuw",
        "addr": "Oude Urkhovenseweg 2",
        "address": "Oude Urkhovenseweg 2",
        "text": "Een zestiende-eeuws huis aan de oude weg naar Urkhoven, waar een leerlooier woonde en werkte. Het staat op de rand van de dorpskern, waar de weg naar Zesgehuchten begon.",
        "more": MON + "GM0018.pdf",
    },
    {
        "name": "De Merckthoeve",
        "note": "Boerderij van vóór 1800 aan de oude weg naar Urkhoven",
        "kind": "Gemeentelijk monument · vóór 1800",
        "addr": "Oude Urkhovenseweg 4",
        "address": "Oude Urkhovenseweg 4",
        "more": MON + "GM0019.pdf",
    },
    # --- Landgoederen, water en de Dommel -------------------------------------------------------------------
    {
        "name": "Wasvenboerderij",
        "stop": "De Philipsboerderij",
        "note": "Philipsboerderij uit 1941 op de plek van landhuis 't Hof, het kasteeltje van Tongelre",
        "kind": "Gemeentelijk monument · 1941",
        "addr": "Celebeslaan 30",
        "address": "Celebeslaan 30",
        "web": "https://www.wasven.nl",
        "text": "Hier stond in 1375 al 'Het goed Ten Hove', in 1637 een bakstenen huis genaamd Musberg. Jonkheer Smits-van Eckart kocht het in 1846 en liet het landhuis en de boerderij in 1872 afbreken en groter terugbouwen; omdat het complex op een kasteel leek, heette het het kasteeltje van Tongelre. Philips kocht het in 1920 om er woningen te bouwen, sloopte het in 1930 en zette er in 1941 toch een boerderij neer: de Philipsboerderij. De funderingen van het oude landhuis liggen nog onder het zand. Nu zijn de boerderij, de bakkerij en de streekwinkel het kloppend hart van Groendomein Wasven.",
        "more": BORD,
        "style": "house",
        "wall": (146, 96, 74),
        "roof": (76, 66, 60),
        "frame": (240, 238, 230),
    },
    {
        "name": "De Karpendonkse Hoeve",
        "note": "Achttiende-eeuwse boerderij aan de Karpendonkse Plas",
        "kind": "Gemeentelijk monument · 18e eeuw",
        "addr": "Sumatralaan 3",
        "address": "Sumatralaan 3",
        "text": "Een achttiende-eeuwse boerderij op de donk, de hoge zandkop in het beekdal waar Karpendonk naar heet. De plas ernaast werd pas in de twintigste eeuw gegraven; de hoeve was er al.",
        "more": MON + "GM0252.pdf",
    },
    {
        "name": "Opwettense watermolen",
        "stop": "De watermolen van Opwetten",
        "note": "Dubbele watermolen op de Kleine Dommel, door Van Gogh getekend",
        "kind": "Rijksmonument · 1743",
        "at": (164880, 385598),
        "address": "Opwettenseweg 203, Nuenen",
        "text": "De molen op de Kleine Dommel, op de grens met Nuenen, is in de dertiende eeuw voor het eerst vermeld en in 1743 in zijn huidige vorm herbouwd: een korenmolen en een oliemolen naast elkaar, elk met een onderslagrad. Vincent van Gogh woonde in 1884 en 1885 in Nuenen en liep hier langs; hij schilderde de watermolen van Opwetten en die van Collen, een eindje stroomopwaarts.",
        "more": "https://nl.wikipedia.org/wiki/Opwettense_watermolen",
        "style": "house",
        "wall": (236, 232, 220),
        "roof": (84, 72, 64),
    },
    {
        "name": "Mariakapel aan de Loostraat",
        "kind": "Gemeentelijk monument · 1954",
        "addr": "Loostraat 22",
        "address": "Loostraat 22",
        "text": "Een kapelletje van 1954 aan de Loostraat, in het gehucht 't Coll tussen de boerderijen en de Kleine Dommel.",
        "more": MON + "GM0355.pdf",
        "style": "church",
        "wall": (234, 230, 218),
        "roof": (86, 74, 66),
    },
    {
        "name": "Boerderij Loostraat 20",
        "kind": "Gemeentelijk monument · ca. 1750",
        "addr": "Loostraat 20",
        "address": "Loostraat 20",
        "more": MON + "GM0168.pdf",
    },
    {
        "name": "Boerderij Loostraat 11",
        "kind": "Gemeentelijk monument · 1897",
        "addr": "Loostraat 11",
        "address": "Loostraat 11",
        "more": MON + "GM0167.pdf",
    },
    {
        "name": "Boerderij Loostraat 1",
        "kind": "Gemeentelijk monument · ca. 1800",
        "addr": "Loostraat 1",
        "address": "Loostraat 1",
        "more": MON + "GM0166.pdf",
    },
    # --- Boerderijen en gehuchten: Urkhoven, Koudenhoven, Klein Tongelre ------------------------------------
    {
        "name": "Boerderij Jeroen Boschlaan 1",
        "note": "Zestiende-eeuwse kern, in 1925 vernieuwd; het oudste gebouw van Klein Tongelre",
        "kind": "Gemeentelijk monument · 16e eeuw",
        "addr": "Jeroen Boschlaan 1",
        "address": "Jeroen Boschlaan 1",
        "text": "Klein Tongelre was een van de gehuchten van de gemeente Tongelre, naast de dorpskern, Urkhoven en 't Coll. Deze boerderij en de Veestraat zijn er de oudste sporen van; de arbeiderswijk Lakerlopen groeide er in de jaren twintig om heen.",
        "more": MON + "GM0312.pdf",
    },
    {
        "name": "Boerderij Urkhovenseweg 71",
        "kind": "Gemeentelijk monument · 17e eeuw",
        "addr": "Urkhovenseweg 71",
        "address": "Urkhovenseweg 71",
        "text": "Een zeventiende-eeuwse boerderij in Urkhoven, in 1850 verbouwd. Urkhoven is het zuidelijkste gehucht van Tongelre en nog altijd een lint van boerderijen tussen de weilanden.",
        "more": MON + "GM0029.pdf",
    },
    {
        "name": "Boerderij Oude Doornakkersweg 1",
        "kind": "Gemeentelijk monument · 1845",
        "addr": "Oude Doornakkersweg 1",
        "address": "Oude Doornakkersweg 1",
        "more": MON + "GM0017.pdf",
    },
    {
        "name": "Boerderij Doolstraat 4",
        "kind": "Gemeentelijk monument · 1907",
        "addr": "Doolstraat 4",
        "address": "Doolstraat 4",
        "more": MON + "GM0310.pdf",
    },
    {
        "name": "Boerderij Oude Muschbergweg 1C",
        "kind": "Gemeentelijk monument · 1934",
        "addr": "Oude Muschbergweg 1C",
        "address": "Oude Muschbergweg 1C",
        "more": MON + "GM0286.pdf",
    },
    # --- Industrie en arbeiderswijken langs de Tongelresestraat --------------------------------------------
    {
        "name": "Sigarenfabriek Crielaars",
        "stop": "Tongelre gaat op de sigaren",
        "note": "Fabriek met directiewoning uit 1877-1884 aan de Lakerstraat",
        "kind": "Gemeentelijk monument · 1877-1884",
        "addrs": ["Lakerstraat 59", "Lakerstraat 61"],
        "address": "Lakerstraat 59 en 61",
        "text": "Tongelre leefde van de boeren en daarna van de sigaren. De fabriek van Crielaars staat met de directiewoning ernaast nog zoals ze in de jaren tachtig van de negentiende eeuw werd gebouwd, midden tussen de arbeiderswoningen van de Lakerstraat.",
        "more": MON + "GM0160.pdf",
    },
    {
        "name": "Het Apollohuis",
        "note": "Voormalige sigarenfabriek uit 1899, later podium voor experimentele kunst en muziek",
        "kind": "Gemeentelijk monument · 1899",
        "addr": "Tongelresestraat 81",
        "address": "Tongelresestraat 81",
        "more": MON + "GM0305.pdf",
    },
    {
        "name": "Kantoorvilla Picus",
        "stop": "Tongelre gaat op de sigaren",
        "note": "Kantoor van de sigarenkistenfabriek J. Brüning en zoon, later NV Houtindustrie Picus",
        "kind": "Gemeentelijk monument · 1912",
        "addr": "Tongelresestraat 29",
        "address": "Tongelresestraat 29",
        "text": "Van de sigarenindustrie leefden ook de bedrijven die kisten, luciferdoosjes en sigarenbandjes maakten. De kantoorvilla op de hoek van de Tongelresestraat en de Dommelhoefstraat is wat er over is van de sigarenkistenfabriek van J. Brüning en zoon, later NV Houtindustrie Picus.",
        "more": MON + "GM0256.pdf",
    },
    {
        "name": "Café en woonhuis Tongelresestraat 62-64",
        "kind": "Gemeentelijk monument · 1879",
        "addrs": ["Tongelresestraat 62", "Tongelresestraat 64"],
        "address": "Tongelresestraat 62-64",
        "more": MON + "GM0044.pdf",
    },
    {
        "name": "Poortgebouw Lakerlopen",
        "stop": "Lakerlopen",
        "note": "Poortgebouw met woningen in traditionele stijl, rijksmonument sinds 2002",
        "kind": "Rijksmonument · ca. 1920",
        "addrs": ["Bosboomstraat 36", "Bosboomstraat 38"],
        "address": "Bosboomstraat 36-38",
        "text": "De buurt Lakerlopen heet naar het stroompje de Lakerloop, dat liep waar nu de Ruysdaelbaan en de Fazantlaan liggen. Stadsarchitect Louis Kooken ontwierp de wijk rond 1920 als sociale woningbouw voor arbeiders: poortgebouwen, bakstenen gevels en hoge rode daken. In 2005 werd een groot deel gesloopt en vervangen door nieuwbouw; de Van Dijckstraat en dit poortgebouw bleven.",
        "more": BORD,
    },
    {
        "name": "Botercontrolestation",
        "note": "Botercontrolestation, later woonhuis",
        "kind": "Rijksmonument",
        "addr": "Fazantlaan 23",
        "address": "Fazantlaan 23",
    },
    {
        "name": "Granville",
        "note": "Villa aan de Parklaan, rijksmonument",
        "kind": "Rijksmonument · 1925",
        "addr": "Parklaan 95",
        "address": "Parklaan 95",
    },
    {
        "name": "Huize de Goren",
        "kind": "Rijksmonument",
        "addr": "Parklaan 54",
        "address": "Parklaan 54",
    },
    {
        "name": "School aan de Reigerlaan",
        "note": "Schoolgebouw met hoofdonderwijzerswoning en Fröbelschool",
        "kind": "Rijksmonument",
        "addr": "Reigerlaan 3",
        "address": "Reigerlaan 3",
        "style": "school",
        "wall": (168, 106, 90),
        "roof": (176, 86, 58),
    },
    {
        "name": "'t Karregat",
        "stop": "'t Karregat",
        "note": "Open wijkgebouw van Frank van Klingeren uit 1973: school, winkels en buurthuis onder één dak",
        "kind": "Wijkgebouw · 1973",
        "addr": "Urkhovenseweg 6",
        "address": "Urkhovenseweg 6",
        "text": "Frank van Klingeren bouwde hier in 1973 een wijkgebouw zonder muren: school, winkels, bibliotheek en buurthuis onder één groot dak, met als idee dat mensen elkaar dan niet kunnen ontlopen. Het werd wereldberoemd en onleefbaar luidruchtig; later zijn er wanden ingezet. Het dak met zijn ronde lichtkoepels staat er nog.",
        "style": "school",
        "wall": (196, 192, 184),
        "roof": (96, 100, 106),
    },
    # --- Het dorp nu -----------------------------------------------------------------------------------------
    {
        "name": "DoDee Salon",
        "kind": "Salon",
        "addr": "Radiostraat 34",
        "address": "Radiostraat 34",
    },
    # --- Geloof ----------------------------------------------------------------------------------------------
    {
        "name": "Ontmoetingskerk",
        "note": "Protestantse kerk uit 1967",
        "kind": "Kerk · 1967",
        "at": (162982, 383877),
        "more": "https://nl.wikipedia.org/wiki/Ontmoetingskerk_(Eindhoven)",
        "style": "church",
        "wall": (182, 112, 90),
        "roof": (84, 86, 92),
    },
    {
        "name": "Mevlana Moskee",
        "note": "Moskee in een gebouw uit 1953 aan de Tongelresestraat",
        "kind": "Moskee",
        "at": (163713, 383431),
        "style": "church",
        "wall": (206, 196, 176),
        "roof": (90, 110, 120),
    },
]

POINTS = [
    # --- Water en groen ---------------------------------------------------------------------------------------
    {
        "name": "Karpendonkse Plas",
        "kind": "Plas",
        "at": (162874, 384947),
        "text": "De plas is gegraven voor het zand van het spoorviaduct, dat Eindhoven noord en zuid met elkaar verbond. Er omheen staat een naaldbos met rododendrons en jeneverbessen; in het water zit vis en op de oever zitten vogelaars.",
    },
    {
        "name": "IJzeren Man",
        "kind": "Zwemplas",
        "at": (162874, 384427),
        "text": "Een tweede gegraven plas, een halve kilometer zuidelijker, genoemd naar de dragline die hem uitgroef. In de zomer wordt er gezwommen; het water hoort bij de groene wig die midden door de stad loopt.",
    },
    {
        "name": "Groendomein Wasven",
        "kind": "Landgoed",
        "at": (163790, 384620),
        "web": "https://www.wasven.nl",
        "text": "Het Wasven heet naar het ven waar de schapen werden gewassen voordat ze geschoren werden. Het landgoed rond de Philipsboerderij is nu bos, boomgaard, akker en moestuin bij elkaar, beheerd door een stichting met vrijwilligers, met een bakkerij en een streekwinkel in de boerderij.",
    },
    # --- Verdwenen --------------------------------------------------------------------------------------------
    {
        "name": "Kasteel Coudenhove (verdwenen)",
        "stop": "Kasteel Coudenhove",
        "kind": "Verdwenen kasteel · ca. 1558",
        "at": (162857, 385483),
        "text": "Kasteel Het Borchsken, ook Coudenhove en Beauregard genoemd, stond hier vlak bij het huidige gildehuis van het Sint-Catharinagilde. Het werd rond 1558 gebouwd voor jonkheer Rutger van Berckel, schepen van 's-Hertogenbosch en heer van Tongelre, en zijn vrouw Livina van Coudenhove; haar neef Jacob werd in 1585 oppervalkenier van de koning van Spanje. In 1702 gaat het over 'het casteel met hof en sijn grachten'; in 1705 worden een grote zaal, een eetzaal, een kapel, een keuken, een kelderkamertje, een slaapkamer, een maagdenkamer en een knechtkamer genoemd. In 1793 was het al zwaar vervallen en zeven jaar later blies een orkaan de resten omver. Op de kadasterkaart was alleen de ronde gracht nog te zien.",
        "more": BORD,
    },
    {
        "name": "Karel I sigarenfabriek: de Van Abbe-muur",
        "stop": "De brand bij Karel I",
        "kind": "Fabrieksmuur · 1927",
        "at": (162103, 383023),
        "text": "Deze muur met geglazuurde tegels is het enige dat over is van de Karel I sigarenfabriek, die hier stond tot de ochtend van 19 februari 1971, toen een brand het hele bedrijf in de as legde. Henri van Abbe begon in 1908 in Gestel sigaren te maken en zette de productie vanaf 1915 hier voort; in 1927 kwam er een industrieel complex van vier verdiepingen bij, waar deze muur een onderdeel van was. Van Abbe was een van de grootste werkgevers van Eindhoven: in de hoogtijdagen werkten er honderden mensen.",
        "more": BORD,
    },
    # --- Oorlog en herdenking ---------------------------------------------------------------------------------
    {
        "name": "Verzetsmonument Lakerlopen",
        "kind": "Oorlogsmonument",
        "at": (162621, 383608),
        "text": "Een gedenksteen met de regel: In trouw onwrikbaar schraagden zij de weerstand 1940-1944.",
    },
    {
        "name": "Stolpersteine Ekstein",
        "kind": "Stolpersteine",
        "latlon": (51.43889, 5.49416),
        "text": "Vijf struikelstenen in de stoep voor het huis van de familie Ekstein: Aaltje, Esther, Levie, Hartog en Rosa Ekstein-Sleutelberg, die hier woonden tot ze werden weggevoerd.",
        "more": "https://nl.wikipedia.org/wiki/Lijst_van_Stolpersteine_in_Eindhoven",
    },
    {
        "name": "Stolpersteine Van Vlijmen",
        "kind": "Stolpersteine",
        "latlon": (51.44061, 5.49512),
        "text": "Struikelstenen voor Joseph van Vlijmen en Bernard André van Vlijmen.",
        "more": "https://nl.wikipedia.org/wiki/Lijst_van_Stolpersteine_in_Eindhoven",
    },
    {
        "name": "Stolpersteine Slijper, Hess en Oettinger",
        "kind": "Stolpersteine",
        "latlon": (51.44316, 5.49573),
        "text": "Struikelstenen voor Helena Slijper-van Staveren, Otto Josef Hess en Karl Oettinger.",
        "more": "https://nl.wikipedia.org/wiki/Lijst_van_Stolpersteine_in_Eindhoven",
    },
    {
        "name": "Stolperstein Hertzberger",
        "kind": "Stolperstein",
        "latlon": (51.44152, 5.49895),
        "text": "Een struikelsteen voor Jacob Hertzberger.",
        "more": "https://nl.wikipedia.org/wiki/Lijst_van_Stolpersteine_in_Eindhoven",
    },
    {
        "name": "Gedenkboom Tongelre",
        "stop": "Bij Eindhoven gevoegd",
        "kind": "Gedenkboom · 2020",
        "at": (162960, 383514),
        "text": "In 2020 was het honderd jaar geleden dat Gestel, Stratum, Strijp, Tongelre en Woensel bij Eindhoven werden gevoegd. In elk van die voormalige gemeenten is daarvoor een zomerlinde geplant; deze staat in het gehucht Klein Tongelre. Uit archeologisch onderzoek weten we dat het dorp Tongelre aan het begin van de dertiende eeuw is ontstaan; de oudste vermeldingen staan in akten van 1241 en 1244.",
        "more": BORD,
    },
    # --- Buurt en bedrijvigheid -------------------------------------------------------------------------------
    {
        "name": "Sectie-C",
        "kind": "Ateliers",
        "at": (164493, 384145),
        "web": "https://www.sectie-c.com",
        "text": "Een oud bedrijventerrein aan de Daalakkersweg, volgebouwd met ateliers en werkplaatsen van ontwerpers en kunstenaars; tijdens de Dutch Design Week staat het vol bezoekers.",
    },
    {
        "name": "Cruyff Court Tongelre",
        "kind": "Voetbalveld",
        "at": (164153, 383739),
    },
    {
        "name": "RK Begraafplaats St. Calixtus",
        "kind": "Begraafplaats",
        "at": (163547, 383087),
    },
    {
        "name": "Speeltuinvereniging St. Joseph",
        "kind": "Speeltuin",
        "at": (163691, 383121),
    },
    {
        "name": "Mandir Triloki Dhaam",
        "kind": "Hindoetempel",
        "at": (163555, 383748),
        "web": "https://www.trilokidhaam.nl/",
    },
    {
        "name": "Auberge Eeckaerde",
        "note": "Herberg Eeckaerde, rijksmonument",
        "kind": "Rijksmonument",
        "addr": "Icaruslaan 28A",
        "address": "Icaruslaan 28A",
    },
]

CATEGORIES = [
    ("dorpskern", "De dorpskern: 't Hofke", [
        "Sint-Martinuskerk", "Oude raadhuis van Tongelre", "Boerderij van Poppel",
        "Oude pastorie ('t Hofke 22)", "Looiershuis (Oude Urkhovenseweg 2)", "De Merckthoeve",
    ]),
    ("landgoed", "Landgoederen en water", [
        "Wasvenboerderij", "Groendomein Wasven", "De Karpendonkse Hoeve", "Karpendonkse Plas", "IJzeren Man",
        "Opwettense watermolen", "Kasteel Coudenhove (verdwenen)", "Auberge Eeckaerde",
    ]),
    ("boerderijen", "Boerderijen en gehuchten", [
        "Boerderij Jeroen Boschlaan 1", "Boerderij Urkhovenseweg 71", "Boerderij Oude Doornakkersweg 1",
        "Boerderij Doolstraat 4", "Boerderij Oude Muschbergweg 1C", "Boerderij Loostraat 1", "Boerderij Loostraat 11",
        "Boerderij Loostraat 20", "Mariakapel aan de Loostraat",
    ]),
    ("industrie", "Industrie en arbeiderswijken", [
        "Sigarenfabriek Crielaars", "Het Apollohuis", "Kantoorvilla Picus", "Café en woonhuis Tongelresestraat 62-64",
        "Karel I sigarenfabriek: de Van Abbe-muur", "Poortgebouw Lakerlopen", "Botercontrolestation", "Granville",
        "Huize de Goren", "School aan de Reigerlaan", "Sectie-C",
    ]),
    ("oorlog", "Oorlog en herdenking", [
        "Verzetsmonument Lakerlopen", "Stolpersteine Ekstein", "Stolpersteine Van Vlijmen",
        "Stolpersteine Slijper, Hess en Oettinger", "Stolperstein Hertzberger", "Gedenkboom Tongelre",
    ]),
    ("nu", "Tongelre nu", [
        "DoDee Salon", "Wasvenboerderij", "Groendomein Wasven", "'t Karregat", "Sectie-C", "Cruyff Court Tongelre",
        "Speeltuinvereniging St. Joseph", "Karpendonkse Plas", "IJzeren Man",
    ]),
    ("geloof", "Kerken, moskee en tempel", [
        "Sint-Martinuskerk", "Ontmoetingskerk", "Mevlana Moskee", "Mandir Triloki Dhaam",
        "Mariakapel aan de Loostraat", "RK Begraafplaats St. Calixtus",
    ]),
]

# What the viewer shows when a place is clicked; the rest of an entry is for the render.
INFO = ("note", "kind", "text", "address", "web", "more", "photo", "stop")

MASTS = []


def point_in_ring(x, y, ring):
    inside = False
    for (x1, y1), (x2, y2) in zip(ring, np.roll(ring, -1, axis=0)):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


ADDRESSES = None


def address_xy(name):
    """RD position of a BAG address such as "'t Hofke 15" (data/raw/addresses.json, from scripts/fetch.py)."""
    global ADDRESSES
    if ADDRESSES is None:
        ADDRESSES = {label.split(f", {PLACE}")[0].split(", ")[0]: (x, y) for x, y, label in json.loads((RAW / "addresses.json").read_text())}
    return ADDRESSES[name]


def building_at(rings, x, y):
    for rid, ring, a in rings:
        if point_in_ring(x, y, ring):
            return rid, a
    return None, None


def main():
    feats = [json.loads(line) for line in open(RAW / "3dbag.jsonl")]
    rings = []
    for f in feats:
        t = f["transform"]
        V = np.array(f["vertices"], dtype=np.float64) * t["scale"] + t["translate"]
        co = f["CityObjects"][f["id"]]
        rings.append((f["id"], V[co["geometry"][0]["boundaries"][0][0]][:, :2], co["attributes"]))

    out = {"buildings": {}, "places": [], "masts": [], "hotspots": [], "categories": []}
    for b in BUILDINGS:
        if "addrs" in b:
            pts = [address_xy(a) for a in b["addrs"]]
            pids = [building_at(rings, *pt)[0] for pt in pts]
            assert all(pids), f"{b['name']}: no building at {b['addrs']}"
            x, y = np.mean(pts, axis=0)
            out["places"].append({"name": b["name"], "note": b.get("note"), "x": x, "y": y, "h": 4.0})
            out["hotspots"].append({"name": b["name"], "pids": pids, "x": x, "y": y, **{k: b[k] for k in INFO if k in b}})
            print(f"{b['name']}: {', '.join(pids)}")
            continue
        x, y = b["at"] if "at" in b else address_xy(b["addr"]) if "addr" in b else wgs_to_rd(*b["latlon"])
        pid, attrs = None, None
        for rid, ring, a in rings:
            if point_in_ring(x, y, ring):
                pid, attrs = rid, a
                break
        if pid is None:
            d = [(np.hypot(*(ring.mean(0) - (x, y))), rid, a) for rid, ring, a in rings]
            dist, pid, attrs = min(d, key=lambda t: t[0])
            if dist > 20:
                pid = None
        height = ((attrs or {}).get("b3_h_dak_max") or 0) - ((attrs or {}).get("b3_h_maaiveld") or 0)
        if "tower" in b:
            height = b["tower"]["top"]
        elif "turret" in b:
            height = b["turret"]["top"]
        out["places"].append({"name": b["name"], "note": b.get("note"), "x": x, "y": y, "h": round(height, 1)})
        if pid and "style" in b:
            out["buildings"][pid] = {k: v for k, v in b.items() if k not in ("at", "latlon", "addr", "addrs", *INFO)}
        if pid:
            out["hotspots"].append({"name": b["name"], "pid": pid, "x": x, "y": y, **{k: b[k] for k in INFO if k in b}})
        print(f"{b['name']}: {pid or 'no building'}")
    for p in POINTS:
        x, y = p["at"] if "at" in p else address_xy(p["addr"]) if "addr" in p else wgs_to_rd(*p["latlon"])
        out["places"].append({"name": p["name"], "note": p.get("note"), "x": x, "y": y, "h": 2.0})
        out["hotspots"].append({"name": p["name"], "x": x, "y": y, **{k: p[k] for k in INFO if k in p}})
    for m in MASTS:
        x, y = wgs_to_rd(*m["latlon"])
        out["masts"].append({**{k: v for k, v in m.items() if k != "latlon"}, "x": x, "y": y})
    names = {h["name"] for h in out["hotspots"]}
    for key, label, members in CATEGORIES:
        missing = [n for n in members if n not in names]
        assert not missing, f"{label}: no hotspot for {missing}"
        out["categories"].append({"key": key, "label": label, "names": members})
    BUILD.mkdir(parents=True, exist_ok=True)
    (BUILD / "landmarks.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
