#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cull_segments.py — Inkscape Extension: Cull Segments by Length
===============================================================
Author  : DeepfishAI  (https://github.com/DeepfishAI)
License : MIT — see LICENSE file
Requires: Inkscape 1.2+, Python 3.8+

Navigation model
----------------
The extension auto-ranges to the actual segment lengths in the document:

    min_len  = shortest path length found
    max_len  = longest  path length found
    base     = max_len - min_len

Two spinners give two levels of navigation:

    Coarse (0-10)  — each ↑↓ step = 10% of base  (big jumps)
    Fine   (0-9)   — each ↑↓ step =  1% of base  (bracketing)

    combined_pct = min( coarse×10 + fine , 100 )
    cutoff       = min_len + (combined_pct / 100) × base

All segments with length ≤ cutoff are hidden (Preview) or moved to the
"Culled" layer (Commit).  No manual threshold entry required.

Performance
-----------
Path lengths are computed once and cached to ~/.cache/deepfish/.
Cache is keyed by file path + mtime — auto-invalidates on save/commit.
"""

import json
import math
import os

import inkex


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

_CACHE_DIR  = os.path.join(os.path.expanduser("~"), ".cache", "deepfish")
_CACHE_FILE = os.path.join(_CACHE_DIR, "cull_segments.json")


def _cache_key(svg_path: str) -> str | None:
    try:
        mtime = os.path.getmtime(svg_path)
        return f"{svg_path}::{mtime}"
    except Exception:
        return None


def _load_cache(key: str):
    """Return (id_lengths, min_len, max_len) or (None, 0, 0) on miss."""
    try:
        with open(_CACHE_FILE) as fh:
            data = json.load(fh)
        if data.get("key") == key:
            return data["lengths"], data["min_len"], data["max_len"]
    except Exception:
        pass
    return None, 0.0, 0.0


def _save_cache(key: str, id_lengths: dict,
                min_len: float, max_len: float) -> None:
    try:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        with open(_CACHE_FILE, "w") as fh:
            json.dump({
                "key":     key,
                "lengths": id_lengths,
                "min_len": min_len,
                "max_len": max_len,
            }, fh)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _point_distance(x1: float, y1: float,
                    x2: float, y2: float) -> float:
    return math.hypot(x2 - x1, y2 - y1)


def _total_path_length(node: inkex.PathElement) -> float:
    SAMPLES = 32
    total   = 0.0
    try:
        path = node.path.to_absolute()
    except Exception:
        return 0.0

    prev_x = prev_y = 0.0
    start_x = start_y = 0.0

    for cmd in path:
        letter = cmd.letter.upper()
        args   = cmd.args

        if letter == "M":
            prev_x, prev_y   = args[0], args[1]
            start_x, start_y = prev_x, prev_y

        elif letter == "L":
            x, y = args[0], args[1]
            total += _point_distance(prev_x, prev_y, x, y)
            prev_x, prev_y = x, y

        elif letter == "H":
            total += _point_distance(prev_x, prev_y, args[0], prev_y)
            prev_x = args[0]

        elif letter == "V":
            total += _point_distance(prev_x, prev_y, prev_x, args[0])
            prev_y = args[0]

        elif letter == "C":
            p = [(prev_x, prev_y),
                 (args[0], args[1]),
                 (args[2], args[3]),
                 (args[4], args[5])]
            px, py = p[0]
            for i in range(1, SAMPLES + 1):
                t = i / SAMPLES; mt = 1 - t
                nx = mt**3*p[0][0] + 3*mt**2*t*p[1][0] + 3*mt*t**2*p[2][0] + t**3*p[3][0]
                ny = mt**3*p[0][1] + 3*mt**2*t*p[1][1] + 3*mt*t**2*p[2][1] + t**3*p[3][1]
                total += _point_distance(px, py, nx, ny)
                px, py = nx, ny
            prev_x, prev_y = args[4], args[5]

        elif letter == "Q":
            p = [(prev_x, prev_y),
                 (args[0], args[1]),
                 (args[2], args[3])]
            px, py = p[0]
            for i in range(1, SAMPLES + 1):
                t = i / SAMPLES; mt = 1 - t
                nx = mt**2*p[0][0] + 2*mt*t*p[1][0] + t**2*p[2][0]
                ny = mt**2*p[0][1] + 2*mt*t*p[1][1] + t**2*p[2][1]
                total += _point_distance(px, py, nx, ny)
                px, py = nx, ny
            prev_x, prev_y = args[2], args[3]

        elif letter == "Z":
            d = _point_distance(prev_x, prev_y, start_x, start_y)
            if d > 0:
                total += d
            prev_x, prev_y = start_x, start_y

    return total


# ---------------------------------------------------------------------------
# Layer helper
# ---------------------------------------------------------------------------

def _get_or_create_culled_layer(svg: inkex.SvgDocumentElement) -> inkex.Layer:
    for layer in svg.xpath("//svg:g[@inkscape:groupmode='layer']"):
        if layer.get("inkscape:label") == "Culled":
            return layer
    layer = inkex.Layer()
    layer.set("inkscape:label",    "Culled")
    layer.set("inkscape:groupmode","layer")
    layer.set("style",             "display:none;color:#ff0000")
    svg.append(layer)
    return layer


# ---------------------------------------------------------------------------
# Style helper
# ---------------------------------------------------------------------------

def _set_display(style_str: str, value: str | None) -> str:
    parts = [p for p in style_str.split(";")
             if ":" in p and not p.strip().startswith("display")]
    if value is not None:
        parts.append(f"display:{value}")
    return ";".join(parts)


# ---------------------------------------------------------------------------
# Extension entry point
# ---------------------------------------------------------------------------

class CullSegments(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--position", type=int, default=0)

    def effect(self):
        position = max(0, min(100, self.options.position))  # 0–100

        # ── Load or build the length cache ──────────────────────────────────
        svg_path  = self.options.input_file
        cache_key = _cache_key(svg_path)
        id_lengths, min_len, max_len = _load_cache(cache_key) \
            if cache_key else (None, 0.0, 0.0)

        if id_lengths is None:
            # First run — measure every path (slow once, cached after)
            id_lengths = {}
            for node in self.svg.xpath("//svg:path"):
                length = _total_path_length(node)
                if length > 0:
                    node_id = node.get_id()
                    if node_id:
                        id_lengths[node_id] = length

            if id_lengths:
                min_len = min(id_lengths.values())
                max_len = max(id_lengths.values())
            else:
                min_len = max_len = 0.0

            if cache_key:
                _save_cache(cache_key, id_lengths, min_len, max_len)

        # ── Derive cutoff from auto-ranged min/max ───────────────────────────
        # baseline = 20% of longest line; each step = 1% of baseline = 0.2% of max_len
        cutoff = position * (max_len * 0.002)

        all_paths = self.svg.xpath("//svg:path")

        # Always move qualifying segments to the Culled layer.
        # Live preview: Inkscape shows this temporarily; Apply makes it permanent.
        layer = _get_or_create_culled_layer(self.svg)
        for node in all_paths:
            node_id = node.get_id()
            length  = id_lengths.get(node_id, 0)
            if 0 < length <= cutoff:
                layer.append(node)


if __name__ == "__main__":
    CullSegments().run()
