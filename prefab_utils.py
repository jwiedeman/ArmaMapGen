import json
import re
from pathlib import Path
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

# Default prefab sizes for Arma Reforger extracted from publicly
# available documentation. These values are approximate and serve
# as examples for automated placement.
DEFAULT_PREFABS: Dict[str, List[Dict[str, float]]] = {
    "residential": [
        {"name": "House_Small_01", "width": 10, "length": 8},
        {"name": "House_Medium_01", "width": 15, "length": 12},
        {"name": "House_Large_01", "width": 20, "length": 18},
    ],
    "commercial": [
        {"name": "Shop_Small_01", "width": 20, "length": 15},
        {"name": "Shop_Market_01", "width": 30, "length": 25},
    ],
    "industrial": [
        {"name": "Factory_Small_01", "width": 40, "length": 30},
        {"name": "Warehouse_Large_01", "width": 60, "length": 40},
    ],
    "military": [
        {"name": "Barracks_01", "width": 25, "length": 10},
    ],
    "generic": [
        {"name": "Apartment_Block_01", "width": 35, "length": 20},
    ],
}

DOC_URL = "https://community.bistudio.com/wiki/Arma_Reforger:Resource_Library"


def fetch_prefabs_from_docs(url: str = DOC_URL) -> Optional[List[str]]:
    """Attempt to fetch prefab names from the official Bohemia docs.

    Returns a list of prefab names on success, or None if the request fails.
    """
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        resp.raise_for_status()
    except Exception:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")
    names = []
    for code in soup.find_all("code"):
        text = code.get_text()
        if text.endswith(".et"):
            names.append(Path(text).stem)
    return names if names else None


def load_prefabs(url: str = DOC_URL) -> Dict[str, List[Dict[str, float]]]:
    """Load prefab data. Attempts to fetch from docs; falls back to defaults."""
    fetched = fetch_prefabs_from_docs(url)
    if fetched:
        # Merge fetched names into generic category if not already present.
        generic = DEFAULT_PREFABS.setdefault("generic", [])
        existing = {p["name"] for p in generic}
        for name in fetched:
            if name not in existing:
                generic.append({"name": name, "width": 10, "length": 10})
    return DEFAULT_PREFABS
