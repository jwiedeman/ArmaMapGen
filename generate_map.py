import os
import osmnx as ox
import srtm
from PIL import Image
import numpy as np
import json
import argparse


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
    tags = {'building': True}
    gdf = ox.features_from_bbox((west, south, east, north), tags)
    buildings = []
    for _, row in gdf.iterrows():
        if row.geometry is None:
            continue
        if row.geometry.geom_type == 'Polygon':
            coords = list(row.geometry.exterior.coords)
        elif row.geometry.geom_type == 'MultiPolygon':
            coords = list(row.geometry.geoms[0].exterior.coords)
        else:
            continue
        buildings.append({'coords': coords})
    return buildings


def extract_roads(north, south, east, west):
    G = ox.graph_from_bbox((west, south, east, north), network_type="drive")
    roads = []
    for u, v, data in G.edges(data=True):
        coords = [(G.nodes[u]['y'], G.nodes[u]['x'])]
        if 'geometry' in data and data['geometry'] is not None:
            coords = [(lat, lon) for lat, lon in data['geometry'].coords]
        else:
            coords.append((G.nodes[v]['y'], G.nodes[v]['x']))
        roads.append({'coords': coords})
    return roads


def main():
    parser = argparse.ArgumentParser(description='Generate map data from real-world location')
    parser.add_argument('--north', type=float, required=True)
    parser.add_argument('--south', type=float, required=True)
    parser.add_argument('--east', type=float, required=True)
    parser.add_argument('--west', type=float, required=True)
    parser.add_argument('--size', type=int, default=512, help='heightmap resolution')
    parser.add_argument('--outdir', default='output')
    args = parser.parse_args()

    img, height_data = fetch_heightmap(args.north, args.south, args.east, args.west, args.size)
    os.makedirs(args.outdir, exist_ok=True)
    img.save(os.path.join(args.outdir, 'heightmap.png'))

    buildings = extract_buildings(args.north, args.south, args.east, args.west)
    roads = extract_roads(args.north, args.south, args.east, args.west)

    with open(os.path.join(args.outdir, 'buildings.json'), 'w') as f:
        json.dump(buildings, f)
    with open(os.path.join(args.outdir, 'roads.json'), 'w') as f:
        json.dump(roads, f)
    with open(os.path.join(args.outdir, 'heightmap.json'), 'w') as f:
        json.dump(height_data, f)


if __name__ == '__main__':
    import os
    main()
