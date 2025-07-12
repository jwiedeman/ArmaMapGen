# ArmaMapGen

This repository contains a prototype script for generating Arma Reforger map data from real world locations. The script uses OpenStreetMap to fetch roads and building footprints and SRTM elevation data to create a simple heightmap.  
Building footprints are analysed to approximate size and orientation and then matched against a small set of example Arma building prefabs.

## Usage

```bash
pip install -r requirements.txt  # install dependencies (osmnx, rasterio, pillow, numpy, SRTM.py, shapely)
python generate_map.py --north <lat> --south <lat> --east <lon> --west <lon> --size 512 --outdir output
```

The script will create `heightmap.png`, `roads.json`, and `buildings.json` in the specified output directory.  
Each building entry now contains a chosen prefab name, rotation angle and approximate dimensions.
