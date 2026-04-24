"""
app.py — Flask Web Server
Run: python app.py
Visit: http://localhost:5000
"""

import os, sys, traceback, json, dataclasses

# ── Force UTF-8 on all platforms (fixes Windows charmap errors) ──────
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from flask import Flask, render_template, request, jsonify, send_file, Response
from knowledge_base import CITIES, ORIGIN_CITIES, DESTINATION_IDS, ORIGIN_IDS
from planner import TravelPlanner

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False


class DataclassEncoder(json.JSONEncoder):
    """Serialize dataclass instances (Attraction, Hotel …) inside result dicts."""
    def default(self, obj):
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            return dataclasses.asdict(obj)
        return super().default(obj)


def safe_jsonify(data):
    return Response(
        json.dumps(data, cls=DataclassEncoder, ensure_ascii=False),
        mimetype="application/json; charset=utf-8"
    )


@app.route("/")
def index():
    origins      = [(k, v["name"], v["flag"]) for k, v in ORIGIN_CITIES.items()]
    destinations = [(k, v.name, v.flag)        for k, v in CITIES.items()]
    return render_template("index.html", origins=origins, destinations=destinations)


@app.route("/api/plan", methods=["POST"])
def api_plan():
    data = request.get_json(force=True)
    try:
        planner = TravelPlanner(
            origin       = data["origin"],
            destination  = data["destination"],
            budget       = int(data["budget"]),
            duration     = int(data["duration"]),
            hotel_style  = data["hotel_style"],
            interests    = data.get("interests", ["culture", "food"]),
            travellers   = int(data.get("travellers", 2)),
            dep_date_str = data.get("dep_date", "2025-06-15"),
        )
        result = planner.generate()
        return safe_jsonify({"ok": True, "result": result})
    except Exception as e:
        return safe_jsonify({"ok": False, "error": str(e),
                             "trace": traceback.format_exc()})


@app.route("/api/kb")
def api_kb():
    cities = []
    for k, v in CITIES.items():
        cities.append({
            "id": k, "name": v.name, "country": v.country, "flag": v.flag,
            "climate": v.climate, "cost_per_day": v.cost_per_day,
            "best_season": v.best_season, "transport": v.transport_mode,
            "tags": v.tags, "timezone": v.timezone,
            "num_hotels": len(v.hotels),
            "num_attractions": len(v.attractions),
            "hotels": {s: {"name": h.name, "cost": h.cost_per_night, "stars": h.stars}
                       for s, h in v.hotels.items()},
            "attractions": [
                {"name": a.name, "category": a.category,
                 "entry_cost": a.entry_cost, "tip": a.tip}
                for a in v.attractions
            ]
        })
    return safe_jsonify(cities)


@app.route("/api/pddl/<filename>")
def get_pddl(filename):
    path = os.path.join("pddl_output", filename)
    if os.path.exists(path):
        content = open(path, encoding="utf-8").read()
        return Response(content, mimetype="text/plain; charset=utf-8")
    return "Not found", 404


@app.route("/api/domain")
def get_domain():
    content = open("travel_domain.pddl", encoding="utf-8").read()
    return Response(content, mimetype="text/plain; charset=utf-8")


if __name__ == "__main__":
    os.makedirs("pddl_output", exist_ok=True)
    print("\n" + "="*55)
    print("  AI Travel Planner — STRIPS + Goal Stack + PDDL")
    print("="*55)
    print("  Open your browser at:  http://localhost:5000")
    print("="*55 + "\n")
    app.run(debug=True, port=5000)
