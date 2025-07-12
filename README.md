# ArmaMapGen

This repository contains a prototype script for generating Arma Reforger map data from real world locations. The script uses OpenStreetMap to fetch roads and building footprints and SRTM elevation data to create a simple heightmap.  
Building footprints are analysed to approximate size and orientation and then matched against example Arma building prefabs.  
Basic building type detection (residential, commercial, industrial) chooses a more appropriate prefab for each footprint.

## Usage

```bash
pip install -r requirements.txt  # install dependencies (osmnx, rasterio, pillow, numpy, SRTM.py, shapely, scikit-learn)
python generate_map.py --north <lat> --south <lat> --east <lon> --west <lon> --size 512 --outdir output
```
The bounding box parameters follow the order **north, south, east, west** as required by OSMnx.

The script will create `heightmap.png`, `roads.json`, `buildings.json` and `scatter_props.json` in the specified output directory.
Each building entry contains a chosen prefab name, rotation angle and approximate dimensions. The script clusters buildings into towns using DBSCAN and scatters simple props (street lights, mailboxes, benches) around clustered buildings.
