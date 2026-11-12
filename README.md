# Isometric Tongelre

A zoomable isometric pixel-art map of **Tongelre**, the old village on the Dommel that became the eastern district of
Eindhoven in 1920: 3 × 3 km, from the Lakerlopen and the Van Abbe wall in the south-west to the Opwetten watermill on
the Nuenen border, with 't Hofke, the Wasven, the Karpendonkse Plas and the hamlets of Urkhoven and 't Coll in between.

Built with the pipeline of [Isometric Helenaveen](https://github.com/jankeesvw/isometric-helenaveen) by
[@jankeesvw](https://x.com/intent/follow?screen_name=jankeesvw), in the spirit of
[isometric.nyc](https://cannoneyed.com/projects/isometric-nyc). Where that project painted every tile with a
fine-tuned image model, this one is rendered procedurally from Dutch open data, so it is exact, seamless and rebuilds
in minutes.

## Pipeline

Run `./build.sh` for everything. The area is set once, in RD New (EPSG:28992) meters, in `scripts/config.py`. The
steps:

1. `scripts/fetch.py` downloads the raw data into `data/raw/`: 3D BAG buildings (LoD2.2 with roof shapes), BGT
   surfaces (roads, water, plots, vegetation), the PDOK aerial photo at 25 cm, AHN surface and terrain heights at
   50 cm, every BAG address in the area and the OpenStreetMap roads, routes and points of interest. A village can be
   looked up by its `woonplaatsnaam`, but a city has far too many addresses to page through, so the script first
   reverse-geocodes a grid over the area to learn which neighbourhoods it touches and then fetches only those.
2. `scripts/landmarks.py` names the places people look for: the Sint-Martinuskerk and the old town hall on 't Hofke,
   the Van Poppel farm of 1584, the Wasven farm on the site of the little castle of Tongelre, the old farms of
   Urkhoven and the Loostraat, the cigar factories along the Tongelresestraat, the Lakerlopen gatehouse,
   't Karregat, the Stolpersteine and the lost castle Coudenhove — each with its own story, colours and links.
   `scripts/build_buildings.py` triangulates the 3D BAG solids and lays the aerial photo on every roof
   (`scripts/roof_atlas.py`): the photo is lined up with each footprint by matching edges, each roof face is evened
   out so the photo's sun and shade don't double up with the renderer's lighting, and the result is reduced to a few
   flat colors so solar panels, skylights and chimneys show as clean shapes. 3D BAG cannot reconstruct glass roofs
   (lidar goes through glass), so those are extruded from their footprint. Water tanks, silos and sheds come from the
   BGT.
3. `scripts/build_trees.py` finds individual trees in the canopy height model (AHN surface minus terrain): local
   maxima for the tops, watershed segmentation for crown size, and the spring aerial photo to tell evergreens from
   deciduous trees. Municipal street trees from the BGT fill in what the lidar missed.
4. `scripts/build_ground.py` paints the BGT polygons, plus pitches and graveyards from OpenStreetMap, in a fixed
   palette with patterns (furrows along each field's long axis, paving grids, ripples, a dark far bank on every
   ditch) and bakes hard sun shadows of the buildings and tree crowns into it.
5. `render/scene.js` is a three.js scene with a 2:1 isometric orthographic camera. Window grids, brick plinths, metal
   cladding and greenhouse glass are drawn in the building shader, a post pass smooths the image with a Kuwahara
   filter and inks every depth step as an outline. Tree crowns are cel-shaded with three tones. `render/run.mjs`
   renders it in headless Chromium on the GPU, tile by tile with a view offset, so tiles line up exactly.
6. `vips dzsave` cuts the stitched image into a Deep Zoom pyramid of WebP tiles, and `viewer/index.html` shows it
   with OpenSeadragon: tilt-shift blur, GPS coordinates under the cursor, a search box over every place and address
   (`scripts/build_places.py`), named buildings and places that light up on hover and open a card with their story
   and links when clicked, grouped into series to step through (`scripts/build_hotspots.py`; a link ending in
   `#dorpskern` opens a series), and a toggle for the walking-junction network and the long-distance paths that cross
   Tongelre — the Hertog Hendrikpad, Het Groene Woud Pad, the Grensdijkjespad and the Airbornepad
   (`scripts/build_routes.py`). Little cars, vans, trucks and cyclists drive the OpenStreetMap roads and cycle paths
   on the right-hand side, keeping their distance and passing behind buildings and under tree crowns: the renderer
   also writes a mask of everything that stands more than 30 cm above the ground (`--pass objects`), `site.sh` turns
   the map under that mask into a second, transparent tile layer, and the viewer draws whatever is behind something
   between the two layers (`scripts/build_traffic.py`). A link ending in `#Sint-Martinuskerk` opens on that place. A
   compass button turns the map a quarter: the map is rendered from all four diagonal directions (`VIEWS` in
   `scripts/config.py`, `render/run.mjs --look`), and the viewer turns a still of the old view about the middle of
   the screen like a turntable while the new view turns in after it. The map opens on the Sint-Martinuskerk, and the
   home button goes back there. A music button plays [My Street](https://opengameart.org/content/my-street) by
   congusbongus (CC0, from OpenGameArt) on a loop. A moon button turns the map to evening: an SVG colour matrix puts
   the map, its traffic and the minimap in moonlight, and a canvas above it lights a lamp every 34 m along the
   streets and the headlights and rear lights of every car and bike. A click on the map, not on a place, drops a pin
   and writes it into the address with the zoom and direction
   (`?pin=51.44824,5.51848&zoom=1.23&view=135`), so that link opens on the same spot. Six people take a cold dip in a
   circle in the IJzeren Man. The viewer speaks Dutch and English, after the browser's language (`?lang=en` or
   `?lang=nl` asks for one); static text carries its English in `data-en*` attributes, and the stories and kinds from
   the data files are looked up by their Dutch in `viewer/en.json`.

`./site.sh` cuts the rendered image into tiles and assembles `site/` without rendering anything; each run writes its
tiles to a fresh `tiles-<stamp>/` folder so browsers never mix cached tiles of two versions. `./deploy.sh` publishes
`site/` to the `gh-pages` branch as a single fresh commit, so the tiles never pile up in the history of `main`.

The camera looks north-east and the sun comes from the west-south-west (`scripts/sun.py`, mirrored in
`render/scene.js`).

Overlays (search, hover outlines, walking routes, the tour, traffic) are JSON files next to the tiles: changing them
needs no rendering, only the small build script and `./deploy.sh`.

`scripts/build_history.py` builds the guided tour. It is empty for this map: fill `STOPS` with years, places, texts
and Wikimedia Commons photos and the viewer shows the tour button again.

## Iterating

`node render/run.mjs crop <x> <y> <w> <h> --scale 4 --out out/crop.png` renders one region of the full image in a
second, which is the fastest way to try a shader or palette change. `node render/run.mjs crop 0 0 2546 1303 --scale
0.6` gives an overview of the whole map.

## Data

3D BAG (TU Delft, 3DGI, CC BY 4.0), BGT (CC0), AHN (CC0), BAG addresses and the aerial photo (Beeldmateriaal
Nederland, CC BY 4.0), all via [PDOK](https://www.pdok.nl). Roads, paths, routes, pitches, graveyards and points of
interest from [OpenStreetMap](https://www.openstreetmap.org/copyright) (ODbL). The monument list and the texts of the
erfgoedborden from the [open data of the gemeente Eindhoven](https://data.eindhoven.nl) (publiek domein). Rijksmonument
numbers and inception dates from [Wikidata](https://www.wikidata.org) (CC0).
