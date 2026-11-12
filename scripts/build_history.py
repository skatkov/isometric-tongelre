"""Tongelre van toen: a guided tour along the village's history, as an overlay for the viewer.

Texts are written for this map from the erfgoedborden and the monument descriptions of the gemeente Eindhoven
(data.eindhoven.nl, publiek domein), the Rijksmonumentenregister and Wikipedia. Photos come from Wikimedia Commons;
the licence of every one was checked and is named in its credit. They are downloaded once and published with the
site.

Output: data/build/history.json and data/build/history/*.jpg
"""


import hashlib
import json
import re
import subprocess
import time
import urllib.parse
import urllib.request

from config import BUILD, CX, CY
from geo import wgs_to_rd

BORD = ("Erfgoedborden, gemeente Eindhoven", "https://data.eindhoven.nl/explore/dataset/erfgoedbordjes/")
RCE = "Rijksdienst voor het Cultureel Erfgoed, Gerard Dukker, CC BY-SA 4.0"
ROSE = "Rosemoon, CC BY-SA 4.0"
WAGGEL = "Wammes Waggel, CC BY-SA 3.0"
ANEFO = "W. Punt voor Anefo, Nationaal Archief, CC0"

STOPS = [
    {
        "year": "1241",
        "title": "Tongelre in de stukken",
        "at": (164190, 384345),
        "zoom": 0.45,
        "text": "Uit archeologisch onderzoek weten we dat het dorp aan het begin van de dertiende eeuw ontstond, op de hoge grond langs de Dommel. De oudste geschreven vermeldingen staan in akten van 1241 en 1244: Herman Freso Hanegreve doet afstand van zijn aanspraken op een paar eigendommen, en keizerin Maria schenkt haar belastingopbrengst in Tongelre aan het klooster van Binderen bij Helmond. De gemeente Tongelre bestond uit de dorpskern hier, en de gehuchten Urkhoven, 't Coll en Klein Tongelre.",
        "photos": [("1868 Tongelre.gif", "De gemeente Tongelre op de kaart van J. Kuyper, 1868 (publiek domein)")],
        "source": BORD,
    },
    {
        "year": "ca. 1558",
        "title": "Kasteel Coudenhove",
        "at": (162857, 385483),
        "text": "Kasteel Het Borchsken, ook Coudenhove en Beauregard genoemd, werd rond 1558 gebouwd voor jonkheer Rutger van Berckel, schepen van 's-Hertogenbosch en heer van Tongelre, en zijn vrouw Livina van Coudenhove. In 1705 worden een grote zaal, een eetzaal, een kapel, een keuken, een kelderkamertje, een slaapkamer, een maagdenkamer en een knechtkamer genoemd. In 1793 was het al zwaar vervallen; zeven jaar later blies een orkaan de resten omver. Op de kadasterkaart was alleen de ronde gracht nog te zien.",
        "source": BORD,
    },
    {
        "year": "1584",
        "title": "De boerderij van Van Poppel",
        "at": (164198, 384336),
        "h": 8,
        "text": "Een driebeukig hallehuis met een brede middenbeuk en twee smalle zijbeuken, woonhuis en stal onder één dak: een van de oudste panden van Eindhoven. Rond 1600 kwam er een opkamer met kelder bij; in de achttiende eeuw werden de kopgevel, de straatgevel en de stal vernieuwd. De boerderij stond pal aan het dorpsplein, dat inmiddels verdwenen is. Bij een opgraving in 1993 kwam er een afvalkuil naast tevoorschijn met zeventiende-eeuws Delfts aardewerk en gebrandschilderd glas.",
        "photos": [("0772 WN126 Jeroen Boschlaan 1, Eindhoven.jpg", f"Een andere oude Tongelrese boerderij, aan de Jeroen Boschlaan, 2020. {ROSE}")],
        "source": BORD,
    },
    {
        "year": "1743",
        "title": "De watermolen van Opwetten",
        "at": (164880, 385598),
        "h": 8,
        "text": "De molen op de Kleine Dommel, op de grens met Nuenen, is in de dertiende eeuw voor het eerst vermeld en in 1743 in zijn huidige vorm herbouwd: een korenmolen en een oliemolen naast elkaar, elk met een onderslagrad. Vincent van Gogh woonde in 1884 en 1885 bij zijn ouders in Nuenen en liep hier langs op zijn tochten naar Eindhoven; in november 1884 schilderde hij de molen.",
        "photos": [
            ("Vincent van Gogh - Water mill at Opwetten (1884).jpg", "Vincent van Gogh, De watermolen van Opwetten, november 1884 (publiek domein)"),
            ("Opwettense-watermolen.jpg", f"De molen in 2007. {WAGGEL}"),
        ],
        "source": ("Opwettense watermolen, Wikipedia", "https://nl.wikipedia.org/wiki/Opwettense_watermolen"),
        "more": "https://nl.wikipedia.org/wiki/Opwettense_watermolen",
    },
    {
        "year": "1846",
        "title": "Het kasteeltje van Tongelre",
        "at": (163686, 384458),
        "h": 8,
        "text": "Hier stond in 1375 al 'Het goed Ten Hove', in 1637 een bakstenen huis genaamd Musberg. Jonkheer Theodorus Smits-van Eckart kocht het op 25 september 1846, met alle bijgebouwen en een boerderij, en liet landhuis en boerderij in 1872 afbreken en groter terugbouwen. Omdat het complex op een kasteel leek, heette het voortaan het kasteeltje van Tongelre.",
        "source": BORD,
    },
    {
        "year": "1877",
        "title": "Tongelre gaat op de sigaren",
        "at": (162327, 383255),
        "h": 8,
        "text": "Tongelre had een grote boerenbevolking; de nijverheid kwam op de tweede plaats, maar groeide hard. Langs de Lakerstraat en de Tongelresestraat verrezen sigarenfabrieken, met de arbeiderswoningen er direct omheen. Van de sigaren leefden ook de bedrijven die kisten, luciferdoosjes en sigarenbandjes maakten, zoals de sigarenkistenfabriek van J. Brüning en zoon, later NV Houtindustrie Picus.",
        "photos": [("0772 WN278 Tongelresestraat 29, Eindhoven.jpg", f"De kantoorvilla van Picus aan de Tongelresestraat, 2020. {ROSE}")],
        "source": BORD,
    },
    {
        "year": "1911",
        "title": "Het raadhuis van Tongelre",
        "at": (164222, 384327),
        "h": 8,
        "text": "Het laatste gemeentehuis van de zelfstandige gemeente Tongelre, naar een ontwerp van Jan Stuyt. Het staat er nog, aan de bocht van 't Hofke, en wordt nog altijd gebruikt voor het buurtleven.",
        "photos": [
            ("Schetsontwerp raadhuis Tongelre.jpg", "Schetsontwerp van Jan Stuyt, september 1910 (publiek domein)"),
            ("Voor en rechterzijgevel - Tongelre - 20209751 - RCE.jpg", f"Voor- en rechterzijgevel in 1974. {RCE}"),
        ],
        "source": BORD,
    },
    {
        "year": "1917",
        "title": "De Sint-Martinuskerk",
        "at": (164108, 384353),
        "h": 16,
        "text": "Een driebeukige neogotische kruisbasiliek op de plek waar Tongelre al sinds de dertiende eeuw om een kerk heen ligt. De twee torens die het hoofdportaal zouden flankeren zijn nooit afgebouwd. Op de gevel van de pastorie ernaast staat een Goede Herder van de Eindhovense beeldhouwer Jan Custers uit 1918.",
        "photos": [("Exterieur - Tongelre - 20209739 - RCE.jpg", f"De kerk in januari 1973. {RCE}")],
        "source": ("Sint-Martinuskerk (Tongelre), Wikipedia", "https://nl.wikipedia.org/wiki/Sint-Martinuskerk_(Tongelre)"),
        "more": "https://nl.wikipedia.org/wiki/Sint-Martinuskerk_(Tongelre)",
    },
    {
        "year": "1920",
        "title": "Bij Eindhoven gevoegd",
        "at": (162960, 383514),
        "text": "Op 1 januari 1920 werden Tongelre, Stratum, Gestel, Strijp en Woensel samengevoegd met het stadje Eindhoven, dat ruimte nodig had. Eindhoven had 6.500 inwoners, Tongelre 3.200. Zowel de bevolking als het gemeentebestuur van Tongelre was tegen: men vreesde hogere belastingen, een landelijk dorp dat door de stad werd opgeslokt en meer criminaliteit. Honderd jaar later, in 2020, is in elk van de vijf voormalige gemeenten een zomerlinde als gedenkboom geplant; die van Tongelre staat hier, in Klein Tongelre.",
        "source": BORD,
    },
    {
        "year": "ca. 1920",
        "title": "Lakerlopen",
        "at": (162748, 383433),
        "h": 8,
        "text": "De buurt heet naar het stroompje de Lakerloop, dat liep waar nu de Ruysdaelbaan en de Fazantlaan liggen. Stadsarchitect Louis Kooken ontwierp hier sociale woningbouw voor arbeiders: poortgebouwen, bakstenen gevels en hoge rode daken, met een beeld van Sint-Joseph als teken van de katholieke oorsprong. In 2005 werd een groot deel gesloopt en vervangen door nieuwbouw; de Van Dijckstraat en het poortgebouw aan de Bosboomstraat bleven.",
        "photos": [
            ("Bosboomstraat-36-38-Eindhoven.jpg", f"Het poortgebouw aan de Bosboomstraat, 2007. {WAGGEL}"),
            ("0772 WN290 Van Dijckstraat 1-13, Eindhoven.jpg", f"De Van Dijckstraat, 2020. {ROSE}"),
        ],
        "source": BORD,
    },
    {
        "year": "1941",
        "title": "De Philipsboerderij",
        "at": (163686, 384458),
        "h": 8,
        "text": "Philips kocht het kasteeltje en de boerderij in 1920 om er woningen te bouwen. Het liep anders: pas in 1930 werden de panden gesloopt, en in 1941 zette Philips er in plaats van woningen een boerderij neer, die nog lang in bedrijf bleef. De funderingen van het oude landhuis liggen, in kaart gebracht en weer toegedekt met zand, nog onder het gras. Nu zijn de boerderij, de bakkerij en de streekwinkel het hart van Groendomein Wasven.",
        "source": BORD,
        "more": "https://www.wasven.nl",
    },
    {
        "year": "1971",
        "title": "De brand bij Karel I",
        "at": (162103, 383023),
        "text": "Vroeg in de ochtend van 19 februari 1971 brak brand uit in de Karel I sigarenfabriek; het hele bedrijf ging in de as. Henri van Abbe was in 1908 in Gestel sigaren gaan maken en zette de productie vanaf 1915 hier voort; in 1927 kwam er een complex van vier verdiepingen bij. Hij was een van de grootste werkgevers van Eindhoven. Alleen de muur met geglazuurde tegels staat er nog.",
        "photos": [
            ("Brand in sigarenfabriek Karel I , Eindhoven afgebrande Karel I fabriek, Bestanddeelnr 924-2821.jpg", f"De afgebrande fabriek, 19 februari 1971. {ANEFO}"),
            ("Brand in sigarenfabriek Karel I , Eindhoven, Bestanddeelnr 924-2823.jpg", f"Blussen op de ochtend van de brand. {ANEFO}"),
        ],
        "source": BORD,
    },
    {
        "year": "1973",
        "title": "'t Karregat",
        "at": (164430, 384002),
        "h": 6,
        "text": "Frank van Klingeren bouwde hier een wijkgebouw zonder muren: school, winkels, bibliotheek en buurthuis onder één groot dak, met als idee dat mensen elkaar dan niet kunnen ontlopen. Het werd wereldberoemd en onleefbaar luidruchtig; later zijn er alsnog wanden ingezet. Het dak met zijn ronde lichtkoepels staat er nog.",
        "photos": [("Basisschool 't Karregat Eindhoven.JPG", f"Basisschool 't Karregat, 2012. Rosemoon, CC BY-SA 3.0")],
        "source": ("'t Karregat, Wikipedia", "https://nl.wikipedia.org/wiki/%27t_Karregat"),
    },
]


def commons_thumb(name, width=960):  # Wikimedia only serves a fixed set of thumbnail widths
    name = name.replace(" ", "_")  # Commons hashes and serves the underscore form of a file name
    h = hashlib.md5(name.encode()).hexdigest()
    q = urllib.parse.quote(name)
    return f"https://upload.wikimedia.org/wikipedia/commons/thumb/{h[0]}/{h[:2]}/{q}/{width}px-{q}"


def download(url, tries=6):
    """Wikimedia rate-limits bursts of thumbnail requests; wait politely and retry."""
    req = urllib.request.Request(url, headers={"User-Agent": "isometric-tongelre/0.1 (personal map)"})
    for attempt in range(tries):
        try:
            data = urllib.request.urlopen(req, timeout=60).read()
            time.sleep(3)
            return data
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == tries - 1:
                raise
            time.sleep(15 * (attempt + 1))


def route_order(stops):
    """Visit the stops as a route over the map instead of by date: the first and last stay put, the rest is a
    nearest-neighbour path tidied with 2-opt, so dots that lie together come one after another. Stops on the same
    spot (the old and the new church) keep their chronological order."""
    if len(stops) < 3:
        return stops
    first, last, middle = stops[0], stops[-1], stops[1:-1]
    dist = lambda a, b: ((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2) ** 0.5
    path, todo = [first], middle[:]
    while todo:
        nxt = min(todo, key=lambda s: (dist(path[-1], s), stops.index(s)))
        path.append(nxt)
        todo.remove(nxt)
    path.append(last)
    improved = True
    while improved:
        improved = False
        for i in range(1, len(path) - 2):
            for j in range(i + 1, len(path) - 1):
                before = dist(path[i - 1], path[i]) + dist(path[j], path[j + 1])
                after = dist(path[i - 1], path[j]) + dist(path[i], path[j + 1])
                if after < before - 0.01:
                    path[i : j + 1] = path[i : j + 1][::-1]
                    improved = True
    # Places within 40 m of each other (church, parsonage, Sunday school) in chronological order.
    i = 0
    while i < len(path):
        j = i
        while j + 1 < len(path) - 1 and i > 0 and dist(path[j + 1], path[i]) < 40:
            j += 1
        year = lambda st: int(m.group()) if (m := re.search(r"\d{4}", st["year"])) else 9999
        path[i : j + 1] = sorted(path[i : j + 1], key=lambda st: (year(st), stops.index(st)))
        i = j + 1
    return path


def main():
    out_dir = BUILD / "history"
    out_dir.mkdir(parents=True, exist_ok=True)
    stops = []
    for i, s in enumerate(STOPS, start=1):
        x, y = s["at"] if "at" in s else wgs_to_rd(*s["latlon"])
        stop = {"n": i, "year": s["year"], "title": s["title"], "text": s["text"], "x": round(x, 1), "y": round(y, 1),
                "h": s.get("h", 0), "zoom": s.get("zoom", 1.2),
                "source": {"label": s["source"][0], "url": s["source"][1]}, "more": s.get("more")}
        stop["photos"] = []
        for k, (name, credit) in enumerate(s.get("photos", [])):
            dst = out_dir / f"{i:02d}_{k}.jpg"
            if not dst.exists():
                dst.write_bytes(download(commons_thumb(name)))
                subprocess.run(["magick", str(dst), "-resize", "640x640>", "-quality", "82", str(dst)], check=True)
            stop["photos"].append({"src": f"history/{dst.name}", "credit": credit,
                                   "url": f"https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(name)}"})
        stops.append(stop)
    stops = route_order(stops)
    for n, stop in enumerate(stops, start=1):
        stop["n"] = n
    # A version in every photo URL, so browsers never show a cached photo that has since been replaced.
    version = hashlib.md5(b"".join(f.read_bytes() for f in sorted(out_dir.glob("*.jpg")))).hexdigest()[:8]
    for stop in stops:
        for ph in stop["photos"]:
            ph["src"] += f"?v={version}"
    (BUILD / "history.json").write_text(json.dumps({"stops": stops}, ensure_ascii=False, indent=1))
    print(f"{len(stops)} stops, {sum(len(s['photos']) for s in stops)} photos on {sum(bool(s['photos']) for s in stops)} stops")


if __name__ == "__main__":
    main()
