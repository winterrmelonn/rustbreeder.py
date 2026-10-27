# ============================================================================
# api/plan.py — THE WEB ENDPOINT (Vercel serverless function)
#
# The web version of gui.py's finalize(): takes the genomes you entered and
# returns what layout.py decides. No genetics or planning logic lives here.
#
#   GET /api/plan?plants=GGGYYY,GGGGGG,...
#   -> {"scores": [...], "best": ..., "plant": 3x3, "result": 3x3, "fitness": n}
#
# Named plan.py, not layout.py, so it doesn't shadow the real layout module.
# ============================================================================

import json
import os
import sys
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Vercel runs this file from api/, so add the project root to the import path
# to reach rustbreeder.py and layout.py.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rustbreeder import score
from layout import best_layout

VALID_GENES = set("GYHXW")
MAX_PLANTS = 50  # anyone can call this URL, so cap the work per request


def plan(plants):
    """Same checks as gui.py's add_plant, then the same call as finalize()."""
    plants = [p.upper() for p in plants]
    if not plants or len(plants) > MAX_PLANTS:
        raise ValueError(f"Enter between 1 and {MAX_PLANTS} plants.")
    for p in plants:
        if len(p) != 6 or any(g not in VALID_GENES for g in p):
            raise ValueError(f"Invalid gene {p!r}: need exactly 6 letters from G/Y/H/X/W.")

    assignment, offspring, fitness = best_layout(plants)
    # Tuple keys like (1, 1) aren't valid JSON, so send each grid as a 3x3
    # list with null for unplanted cells.
    grid = lambda cells: [[cells.get((r, c)) for c in range(3)] for r in range(3)]
    return {
        "scores": [score(p) for p in plants],
        "best": max(plants, key=score),
        "plant": grid(assignment),
        "result": grid(offspring),
        "result_scores": grid({pos: score(g) for pos, g in offspring.items()}),
        "fitness": fitness,
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        raw = parse_qs(urlparse(self.path).query).get("plants", [""])[0]
        try:
            status, body = 200, plan([p for p in raw.split(",") if p])
        except ValueError as e:
            status, body = 400, {"error": str(e)}
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    out = plan(["GGGYYY", "GGGGGG", "YYYYYY", "GYHXWG", "GGGHHH"])
    assert out["best"] == "GGGYYY" and out["plant"][1][1] is not None
    try:
        plan(["GGGYY"])
        raise AssertionError("short genome accepted")
    except ValueError:
        pass
    print("demo: ok", out["fitness"])
