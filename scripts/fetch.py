# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Download the raw open data for the area: 3D BAG, BGT, aerial photos and AHN."""

import json
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from config import CHUNK, NX, NY, PLACE, RAW, XMAX, XMIN, YMAX, YMIN

UA = {"User-Agent": "isometric-tongelre/0.1"}
RD = "http://www.opengis.net/def/crs/EPSG/0/28992"

BGT_COLLECTIONS = [
    "begroeidterreindeel",
    "onbegroeidterreindeel",
    "wegdeel",
    "ondersteunendwegdeel",
    "waterdeel",
    "ondersteunendwaterdeel",
    "overbruggingsdeel",
    "overigbouwwerk",
    "kunstwerkdeel_vlak",
    "scheiding_vlak",
    "scheiding_lijn",
    "vegetatieobject_punt",
    "vegetatieobject_vlak",
    "vegetatieobject_lijn",
    "pand",
    "spoor",
    "weginrichtingselement_lijn",
    "weginrichtingselement_vlak",
    "straatmeubilair",
    "paal",
    "mast",
]


def get(url, binary=False, tries=5):
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
                data = r.read()
                return data if binary else json.loads(data)
        except Exception as e:  # noqa: BLE001
            if attempt == tries - 1:
                raise
            print(f"retry {attempt + 1} {url[:100]}: {e}", file=sys.stderr)
            time.sleep(2 * (attempt + 1))


def fetch_3dbag():
    out = RAW / "3dbag.jsonl"
    if out.exists():
        return
    url = f"https://api.3dbag.nl/collections/pand/items?bbox={XMIN},{YMIN},{XMAX},{YMAX}&limit=100"
    n = 0
    with open(out.with_suffix(".tmp"), "w") as f:
        while url:
            page = get(url)
            transform = page["metadata"]["transform"]
            for feat in page["features"]:
                feat["transform"] = transform
                f.write(json.dumps(feat) + "\n")
                n += 1
            url = next((l["href"] for l in page["links"] if l["rel"] == "next"), None)
            print(f"3dbag {n}/{page['numberMatched']}", file=sys.stderr)
    out.with_suffix(".tmp").rename(out)


def fetch_bgt(coll):
    out = RAW / f"bgt_{coll}.geojson"
    if out.exists():
        return
    q = urllib.parse.urlencode(
        {"bbox": f"{XMIN},{YMIN},{XMAX},{YMAX}", "bbox-crs": RD, "crs": RD, "limit": 1000, "f": "json"}
    )
    url = f"https://api.pdok.nl/lv/bgt/ogc/v1/collections/{coll}/items?{q}"
    feats = []
    while url:
        page = get(url)
        feats += page["features"]
        url = next((l["href"] for l in page["links"] if l["rel"] == "next"), None)
    # The API also serves retired versions of objects; keep only the current ones.
    current = [f for f in feats if not f["properties"].get("eind_registratie")]
    out.write_text(json.dumps({"type": "FeatureCollection", "features": current}))
    print(f"bgt {coll}: {len(current)} current of {len(feats)}", file=sys.stderr)


def fetch_aerial(ix, iy, chunk=CHUNK, res=0.25):
    d = RAW / "aerial"
    d.mkdir(exist_ok=True)
    out = d / f"{ix}_{iy}.jpg"
    if out.exists():
        return
    x0, y0 = XMIN + ix * chunk, YMIN + iy * chunk
    px = int(chunk / res)
    q = urllib.parse.urlencode(
        {
            "SERVICE": "WMS",
            "VERSION": "1.3.0",
            "REQUEST": "GetMap",
            "LAYERS": "Actueel_orthoHR",
            "STYLES": "",
            "CRS": "EPSG:28992",
            "BBOX": f"{x0},{y0},{x0 + chunk},{y0 + chunk}",
            "WIDTH": px,
            "HEIGHT": px,
            "FORMAT": "image/jpeg",
        }
    )
    out.write_bytes(get(f"https://service.pdok.nl/hwh/luchtfotorgb/wms/v1_0?{q}", binary=True))


def fetch_ahn(cov, ix, iy, chunk=CHUNK):
    # The WCS refuses anything over 4000 px a side, so fetch it in chunks (1000 px at 0.5 m).
    d = RAW / "ahn"
    d.mkdir(exist_ok=True)
    out = d / f"{cov}_{ix}_{iy}.tif"
    if out.exists():
        return
    x0, y0 = XMIN + ix * chunk, YMIN + iy * chunk
    url = (
        "https://service.pdok.nl/rws/ahn/wcs/v1_0?SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage"
        f"&COVERAGEID={cov}&SUBSET=x({x0},{x0 + chunk})&SUBSET=y({y0},{y0 + chunk})&FORMAT=image/tiff"
    )
    out.write_bytes(get(url, binary=True))


def fetch_addresses():
    """Every BAG address inside the area, for the viewer's search box.

    A village can be fetched by its woonplaatsnaam, but a city has far too many addresses to page through, so first
    reverse-geocode a grid over the area to learn which neighbourhoods (wijken) it touches, then fetch those.
    """
    out = RAW / "addresses.json"
    if out.exists():
        return
    base = "https://api.pdok.nl/bzk/locatieserver/search/v3_1"

    wijken = set()
    step = 400
    for x in range(XMIN, XMAX + 1, step):
        for y in range(YMIN, YMAX + 1, step):
            q = urllib.parse.urlencode({"X": x, "Y": y, "type": "adres", "rows": 1, "fl": "wijknaam", "distance": 2000})
            for doc in get(f"{base}/reverse?{q}")["response"]["docs"]:
                if doc.get("wijknaam"):
                    wijken.add(doc["wijknaam"])
    print(f"addresses: neighbourhoods {sorted(wijken)}", file=sys.stderr)

    pts, seen = [], set()

    def page(fq):
        start = 0
        while True:
            q = urllib.parse.urlencode(
                {"q": "*:*", "fq": ["type:adres", f"woonplaatsnaam:{PLACE}", fq], "fl": "weergavenaam,centroide_rd", "rows": 100, "start": start},
                doseq=True,
            )
            d = get(f"{base}/free?{q}")["response"]
            for doc in d["docs"]:
                x, y = (float(v) for v in doc["centroide_rd"][6:-1].split())
                if XMIN <= x <= XMAX and YMIN <= y <= YMAX and doc["weergavenaam"] not in seen:
                    seen.add(doc["weergavenaam"])
                    pts.append((x, y, doc["weergavenaam"]))
            start += 100
            if start >= d["numFound"] or start >= 10000:
                return

    for w in sorted(wijken) or [None]:
        page(f'wijknaam:"{w}"' if w else "*:*")
    print(f"addresses: {len(pts)} in the area", file=sys.stderr)
    out.write_text(json.dumps(pts))


def overpass(out, q, what):
    """Run an Overpass query into out (Overpass is often busy, so try a few servers)."""
    for host in ("overpass-api.de/api/interpreter", "overpass.private.coffee/api/interpreter", "maps.mail.ru/osm/tools/overpass/api/interpreter"):
        try:
            req = urllib.request.Request(f"https://{host}", data=urllib.parse.urlencode({"data": q}).encode(), headers=UA)
            with urllib.request.urlopen(req, timeout=180) as r:
                out.write_bytes(r.read())
            return
        except Exception as e:  # noqa: BLE001
            print(f"overpass {host}: {e}", file=sys.stderr)
    print(f"OpenStreetMap unavailable; {what} are skipped", file=sys.stderr)


def osm_bbox():
    from geo import rd_to_wgs

    lats, lons = zip(*(rd_to_wgs(x, y) for x in (XMIN, XMAX) for y in (YMIN, YMAX)))
    return f"{min(lats)},{min(lons)},{max(lats)},{max(lons)}"


def fetch_osm():
    """Pitches, graveyards and points of interest from OpenStreetMap."""
    out = RAW / "osm_landmarks.json"
    if out.exists():
        return
    bbox = osm_bbox()
    q = f"""[out:json][timeout:90];
( nwr["military"]({bbox}); way["leisure"="pitch"]({bbox}); nwr["landuse"="cemetery"]({bbox});
  nwr["amenity"="place_of_worship"]({bbox}); nwr["tourism"]({bbox}); nwr["historic"]({bbox}); );
out geom tags;"""
    overpass(out, q, "pitches and graveyards")


def fetch_routes():
    """Walking routes and the numbered walking-junction network (wandelknooppunten) from OpenStreetMap."""
    out = RAW / "osm_routes.json"
    if out.exists():
        return
    bbox = osm_bbox()
    q = f"""[out:json][timeout:120];
( relation["route"~"^(hiking|foot|walking)$"]({bbox}); node["rwn_ref"]({bbox}); );
out geom;"""
    overpass(out, q, "walking routes")


def fetch_roads():
    """The roads, cycle paths, footpaths and farm tracks that people use, from OpenStreetMap, with node ids to find
    junctions."""
    out = RAW / "osm_roads.json"
    if out.exists():
        return
    bbox = osm_bbox()
    kinds = "motorway|motorway_link|trunk|trunk_link|primary|primary_link|secondary|secondary_link|tertiary|tertiary_link|unclassified|residential|living_street|service"
    q = f"""[out:json][timeout:120];
( way["highway"~"^({kinds})$"]({bbox}); way["highway"~"^(cycleway|footway|path|pedestrian|track|steps|bridleway)$"]({bbox}); );
out geom;"""
    overpass(out, q, "roads and paths for traffic")


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    jobs = [fetch_3dbag, fetch_addresses, fetch_osm, fetch_routes, fetch_roads, *(lambda c=c: fetch_bgt(c) for c in BGT_COLLECTIONS)]
    jobs += [lambda c=c, i=i, j=j: fetch_ahn(c, i, j) for c in ("dsm_05m", "dtm_05m") for i in range(NX) for j in range(NY)]
    jobs += [lambda i=i, j=j: fetch_aerial(i, j) for i in range(NX) for j in range(NY)]
    with ThreadPoolExecutor(8) as pool:
        for fut in [pool.submit(j) for j in jobs]:
            fut.result()
    print("done", file=sys.stderr)


if __name__ == "__main__":
    main()
