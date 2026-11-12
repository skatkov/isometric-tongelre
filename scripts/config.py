"""Shared settings: the area we render, in RD New (EPSG:28992) meters."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
BUILD = ROOT / "data" / "build"

# Tongelre, the old village on the Dommel east of Eindhoven: 3 x 3 km, from Doornakkers and the Lakerlopen in the
# west to the Collse Watermolen on the Nuenen border, and from Urkhoven in the south to the Karpendonkse Plas.
XMIN, YMIN, XMAX, YMAX = 162000, 383000, 165000, 386000
CX, CY = (XMIN + XMAX) / 2, (YMIN + YMAX) / 2

# The town or city the addresses belong to (BAG woonplaatsnaam), for the viewer's search box.
PLACE = "Eindhoven"

# Downloads and ground textures come in square chunks of this many meters.
CHUNK = 500
NX, NY = int((XMAX - XMIN) / CHUNK), int((YMAX - YMIN) / CHUNK)

# Ground raster resolution in meters per pixel.
GROUND_RES = 0.25

# The compass directions the map is rendered from (render/run.mjs --look); the first is the one the viewer opens on.
VIEWS = (45, 135, 225, 315)


def write_area():
    """The renderer and the viewer read the area from here."""
    BUILD.mkdir(parents=True, exist_ok=True)
    (BUILD / "area.json").write_text(
        json.dumps({"xmin": XMIN, "ymin": YMIN, "xmax": XMAX, "ymax": YMAX, "cx": CX, "cy": CY, "chunk": CHUNK, "nx": NX, "ny": NY})
    )
