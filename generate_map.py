import os
import osmnx as ox
import srtm
from PIL import Image
import numpy as np
import json
import argparse
import math
import random
from shapely.geometry import Polygon
from sklearn.cluster import DBSCAN


def fetch_heightmap(north, south, east, west, size=512):
    data = srtm.get_data()
    lat_grid = np.linspace(north, south, size)
    lon_grid = np.linspace(west, east, size)
    heightmap = np.zeros((size, size), dtype=np.float32)
    for i, lat in enumerate(lat_grid):
        for j, lon in enumerate(lon_grid):
            elev = data.get_elevation(lat, lon)
            if elev is None:
                elev = 0
            heightmap[i, j] = elev
    max_e = np.max(heightmap)
    min_e = np.min(heightmap)
    if max_e == min_e:
        scaled = np.zeros_like(heightmap, dtype=np.uint8)
    else:
        scaled = ((heightmap - min_e) / (max_e - min_e) * 255).astype(np.uint8)
    img = Image.fromarray(scaled)
    return img, heightmap.tolist()


def extract_buildings(north, south, east, west):
    tags = {"building": True}
    gdf = ox.features_from_bbox((west, south, east, north), tags)

    prefabs = {
        "residential": [
            {"name": "Small_House_A", "width": 10, "length": 8},
            {"name": "Small_House_B", "width": 12, "length": 9},
        ],
        "commercial": [{"name": "Shop_A", "width": 20, "length": 15}],
        "industrial": [{"name": "Warehouse_B", "width": 30, "length": 20}],
        "generic": [{"name": "Apartment_Block_C", "width": 40, "length": 15}],
    }

    def match_prefab(w, l, b_type):
        options = prefabs.get(b_type, prefabs["generic"])
        best = None
        best_score = float("inf")
        for p in options:
            score = abs(p["width"] - w) + abs(p["length"] - l)
            if score < best_score:
                best_score = score
                best = p["name"]
        return best

    buildings = []
    for _, row in gdf.iterrows():
        geom = row.geometry
        if geom is None:
            continue
        poly = None
        if geom.geom_type == "Polygon":
            poly = geom
        elif geom.geom_type == "MultiPolygon":
            poly = geom.geoms[0]
        if poly is None:
            continue

        coords = list(poly.exterior.coords)
        rect = poly.minimum_rotated_rectangle
        rect_coords = list(rect.exterior.coords)
        side_lengths = [
            math.hypot(
                rect_coords[i + 1][0] - rect_coords[i][0],
                rect_coords[i + 1][1] - rect_coords[i][1],
            )
            for i in range(4)
        ]
        width, length = sorted(side_lengths)[0:2]
        dx = rect_coords[1][0] - rect_coords[0][0]
        dy = rect_coords[1][1] - rect_coords[0][1]
        orientation = (math.degrees(math.atan2(dy, dx)) + 360) % 360
        b_type = str(row.get("building", "generic"))
        if b_type not in prefabs:
            if b_type in ["house", "residential", "detached", "apartments"]:
                b_type = "residential"
            elif b_type in ["commercial", "retail"]:
                b_type = "commercial"
            elif b_type in ["industrial", "warehouse"]:
                b_type = "industrial"
            else:
                b_type = "generic"
        prefab = match_prefab(width, length, b_type)
        centroid = poly.centroid

        buildings.append(
            {
                "coords": coords,
                "prefab": prefab,
                "position": [centroid.y, centroid.x],
                "orientation": orientation,
                "width": width,
                "length": length,
            }
        )
    return buildings


def extract_roads(north, south, east, west):
    G = ox.graph_from_bbox((west, south, east, north), network_type="drive")
    roads = []
    for u, v, data in G.edges(data=True):
        coords = [(G.nodes[u]["y"], G.nodes[u]["x"])]
        if "geometry" in data and data["geometry"] is not None:
            coords = [(lat, lon) for lat, lon in data["geometry"].coords]
        else:
            coords.append((G.nodes[v]["y"], G.nodes[v]["x"]))
        roads.append({"coords": coords})
    return roads


def detect_towns(buildings, eps=0.001, min_samples=5):
    if not buildings:
        return []
    coords = np.array([b["position"] for b in buildings])
    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(coords)
    return clustering.labels_


def generate_scatter_props(buildings, labels):
    prop_types = ["street_light", "mailbox", "bench"]
    props = []
    for b, label in zip(buildings, labels):
        if label == -1:
            continue
        num = random.randint(0, 2)
        for _ in range(num):
            offset_x = random.uniform(-0.0001, 0.0001)
            offset_y = random.uniform(-0.0001, 0.0001)
            props.append(
                {
                    "type": random.choice(prop_types),
                    "position": [
                        b["position"][0] + offset_x,
                        b["position"][1] + offset_y,
                    ],
                }
            )
    return props


def main():
    parser = argparse.ArgumentParser(
        description="Generate map data from real-world location"
    )
    parser.add_argument("--north", type=float, required=True)
    parser.add_argument("--south", type=float, required=True)
    parser.add_argument("--east", type=float, required=True)
    parser.add_argument("--west", type=float, required=True)
    parser.add_argument("--size", type=int, default=512, help="heightmap resolution")
    parser.add_argument("--outdir", default="output")
    args = parser.parse_args()

    img, height_data = fetch_heightmap(
        args.north, args.south, args.east, args.west, args.size
    )
    os.makedirs(args.outdir, exist_ok=True)
    img.save(os.path.join(args.outdir, "heightmap.png"))

    buildings = extract_buildings(args.north, args.south, args.east, args.west)
    roads = extract_roads(args.north, args.south, args.east, args.west)
    labels = detect_towns(buildings)
    props = generate_scatter_props(buildings, labels)

    with open(os.path.join(args.outdir, "buildings.json"), "w") as f:
        json.dump(buildings, f)
    with open(os.path.join(args.outdir, "roads.json"), "w") as f:
        json.dump(roads, f)
    with open(os.path.join(args.outdir, "heightmap.json"), "w") as f:
        json.dump(height_data, f)
    with open(os.path.join(args.outdir, "scatter_props.json"), "w") as f:
        json.dump(props, f)


if __name__ == "__main__":
    import os

    main()
