"""Build output/campus_customs_clean.db from data/campus_customs.db.

The original database is never modified. Run from the hw4 folder:
    python output/clean_db.py
"""
import json
import re
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "campus_customs.db"
DST = ROOT / "output" / "campus_customs_clean.db"

# --- 1. Standard categories --------------------------------------------------
# Order matters: the first rule whose keyword appears in garment_type wins.
CATEGORY_RULES = [
    ("fleece jacket", "fleece jacket"),
    ("quarter-zip", "quarter-zip"),
    ("full-zip hooded", "full-zip hoodie"),
    ("hood", "hoodie"),
    ("performance shirt", "long-sleeve shirt"),
    ("t-shirt", "t-shirt"),
    ("crewneck", "sweatshirt"),
    ("mockneck", "sweatshirt"),
    ("jacket", "jacket"),
]

# garment_type fixes (found by looking at the product photos)
GARMENT_TYPE_FIXES = {
    "benjamin-franklin-t-shirt": "short-sleeve t-shirt",
    "berkeley-sweater-fleece-jacket": "full-zip sweater fleece jacket",
    "timothy-dwight-college-crewneck": "crewneck sweatshirt",
}

# --- 2. The three placeholder products (written from their photos) -----------
STUB_FIXES = {
    "benjamin-franklin-t-shirt": {
        "description": "Heather gray short-sleeve crew-neck T-shirt with a large "
        "blue-and-red Benjamin Franklin College shield (white lightning bolts and "
        "fleurs-de-lis) centered on the chest above black BENJAMIN FRANKLIN COLLEGE "
        "lettering.",
        "colors": ["heather gray", "blue", "red", "white", "black"],
        "search_tags": ["Yale", "Benjamin Franklin College", "Franklin", "residential "
        "college", "college shield", "crest", "t-shirt", "short sleeve", "gray t-shirt",
        "Campus Customs"],
    },
    "berkeley-sweater-fleece-jacket": {
        "description": "Light heather gray full-zip sweater fleece jacket with a "
        "stand collar, charcoal zipper and trim, zippered side pockets, and a small "
        "red Berkeley College shield with BERKELEY lettering on the left chest.",
        "colors": ["heather gray", "charcoal gray", "red", "white"],
        "search_tags": ["Yale", "Berkeley College", "Berkeley", "residential college",
        "fleece", "fleece jacket", "sweater fleece", "full zip", "jacket",
        "gray jacket", "college shield", "Campus Customs"],
    },
    "timothy-dwight-college-crewneck": {
        "description": "Heather gray long-sleeve crewneck sweatshirt with ribbed "
        "collar, cuffs, and waistband, featuring a small red-and-white Timothy Dwight "
        "College shield with a lion and TIMOTHY DWIGHT lettering on the left chest.",
        "colors": ["heather gray", "red", "white", "black"],
        "search_tags": ["Yale", "Timothy Dwight College", "TD", "residential college",
        "crewneck", "sweatshirt", "gray sweatshirt", "left chest crest",
        "college shield", "Campus Customs"],
    },
}

# --- 3. Color names ----------------------------------------------------------
COLOR_MAP = {
    "navy": "navy blue",
    "gray": "heather gray",
    "light gray": "heather gray",
    "dark heather gray": "charcoal gray",
    "dark heather charcoal": "charcoal gray",
    "heather charcoal gray": "charcoal gray",
    "ivory": "cream",
}

# base_color = main fabric color, taken from the first color word in the description
BASE_COLOR_KEYWORDS = [
    ("dark heather", "charcoal gray"),
    ("charcoal", "charcoal gray"),
    ("navy", "navy blue"),
    ("gray", "heather gray"),
    ("white", "white"),
    ("cream", "cream"),
    ("ivory", "cream"),
    ("coral", "dusty coral"),
]

# --- 4. Search tag additions / removals --------------------------------------
HANDSOME_DAN = {  # items that show the bulldog mascot itself
    "district-vit-crewneck-vintage-bulldog",
    "district-vit-crewneck-vintage-standing-bulldog",
    "district-vit-hoodie-vintage-bulldog",
    "district-vit-hoodie-vintage-sailor-bulldog",
    "super-heavyweight-crewneck-arched-yale-crest",
}
BULLDOGS_WORD = {  # items with the word BULLDOGS printed on them
    "dry-zone-long-sleeve",
    "ua-mens-tech-l-s-2-0",
    "yale-maplehouse-diana-mockneck",
}
TAG_REMOVALS = {
    "school-of-art-1-4-zip": {"fleece"},     # a quarter-zip, not a fleece
    "squash-left-chest-tennis": {"tennis"},  # the graphic says YALE SQUASH only
}
RESIDENTIAL_COLLEGES = [
    "Benjamin Franklin", "Berkeley", "Branford", "Davenport", "Grace Hopper",
    "Jonathan Edwards", "Morse", "Pierson", "Saybrook", "Timothy Dwight", "Trumbull",
]

# --- 5. Display names --------------------------------------------------------
NAME_OVERRIDES = {
    "school-of-architecture-crewneck": "School of Architecture Quarter-Zip",
    "squash-left-chest-tennis": "Squash Left Chest Crewneck",
    "ua-mens-tech-l-s-2-0": "UA Men's Tech Long Sleeve 2.0",
    "2025-yale-vs-harvard-t-shirt": "2025 Yale vs. Harvard T-Shirt",
    "champion-reverse-weave-hoodie-1": "Champion Reverse Weave Hoodie",
    "yale-sports-creqneck-field-hockey": "Yale Sports Crewneck Field Hockey",
    "track-field-left-chest-t-shirt": "Track & Field Left Chest T-Shirt",
}
NAME_REPLACEMENTS = [
    (r"\b1 4 Zip\b", "Quarter-Zip"),
    (r"\bT Shirt\b", "T-Shirt"),
    (r"\bTri Blend\b", "Tri-Blend"),
    (r"\bFull Zip\b", "Full-Zip"),
    (r"\bDouble Knit\b", "Double-Knit"),
    (r"\bUa\b", "UA"),
    (r"\bMens\b", "Men's"),
    (r"\bVit\b", "VIT"),
    (r"(?<=\w )(Of|And|The)\b", lambda m: m.group(1).lower()),
]


def add_tags(tags, *new):
    lower = {t.lower() for t in tags}
    for t in new:
        if t.lower() not in lower:
            tags.append(t)
            lower.add(t.lower())


def main():
    # Rebuilding copies the original database over DST, which would erase any
    # accounts created through the website (they live in DST's users table).
    # Refuse to overwrite an existing copy unless --force is given.
    if DST.exists() and "--force" not in sys.argv:
        raise SystemExit(
            f"{DST} already exists. Delete it or pass --force to rebuild "
            "(this discards any accounts created on the website)."
        )
    shutil.copyfile(SRC, DST)
    con = sqlite3.connect(DST)
    con.execute("ALTER TABLE catalogue ADD COLUMN category TEXT")
    con.execute("ALTER TABLE catalogue ADD COLUMN base_color TEXT")

    rows = con.execute(
        "SELECT product_id, name, garment_type, description, colors, search_tags "
        "FROM catalogue").fetchall()
    for pid, name, gtype, desc, colors, tags in rows:
        colors, tags = json.loads(colors), json.loads(tags)

        if pid in STUB_FIXES:
            fix = STUB_FIXES[pid]
            desc, colors, tags = fix["description"], list(fix["colors"]), list(fix["search_tags"])

        gtype = GARMENT_TYPE_FIXES.get(pid, gtype).replace("T-shirt", "t-shirt")
        category = next(c for kw, c in CATEGORY_RULES if kw in gtype.lower())

        colors = list(dict.fromkeys(COLOR_MAP.get(c, c) for c in colors))
        d = desc.lower()
        hits = [(d.find(kw), base) for kw, base in BASE_COLOR_KEYWORDS if kw in d]
        base_color = min(hits)[1]

        tags = [t for t in tags if t.lower() not in TAG_REMOVALS.get(pid, set())]
        if pid in HANDSOME_DAN:
            add_tags(tags, "Handsome Dan", "bulldog", "mascot", "Bulldogs")
        if pid in BULLDOGS_WORD:
            add_tags(tags, "Bulldogs", "bulldog")
        if category == "quarter-zip":
            add_tags(tags, "quarter zip", "1/4 zip", "quarter-zip")
        if category == "fleece jacket":
            add_tags(tags, "fleece", "fleece jacket", "full zip", "jacket")
        if "harvard" in pid:
            add_tags(tags, "Harvard-Yale", "The Game")
        for college in RESIDENTIAL_COLLEGES:
            if college.lower() in name.lower():
                add_tags(tags, f"{college} College", "residential college")

        if pid in NAME_OVERRIDES:
            name = NAME_OVERRIDES[pid]
        else:
            for pat, rep in NAME_REPLACEMENTS:
                name = re.sub(pat, rep, name)

        con.execute(
            "UPDATE catalogue SET name=?, garment_type=?, description=?, colors=?, "
            "search_tags=?, category=?, base_color=? WHERE product_id=?",
            (name, gtype, desc, json.dumps(colors), json.dumps(tags), category,
             base_color, pid))

    con.commit()

    print("Categories:", con.execute(
        "SELECT category, COUNT(*) FROM catalogue GROUP BY 1 ORDER BY 2 DESC").fetchall())
    print("Base colors:", con.execute(
        "SELECT base_color, COUNT(*) FROM catalogue GROUP BY 1 ORDER BY 2 DESC").fetchall())
    print("Distinct garment types:", con.execute(
        "SELECT COUNT(DISTINCT garment_type) FROM catalogue").fetchone()[0])
    print("Stubs left:", con.execute(
        "SELECT COUNT(*) FROM catalogue WHERE description LIKE '%stub%' OR colors='[]'"
    ).fetchone()[0])
    print("Handsome Dan items:", con.execute(
        "SELECT COUNT(*) FROM catalogue WHERE search_tags LIKE '%Handsome Dan%'").fetchone()[0])
    con.close()
    print(f"Wrote {DST}")


if __name__ == "__main__":
    main()
