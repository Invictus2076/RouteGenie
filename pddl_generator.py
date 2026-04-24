"""
pddl_generator.py
═══════════════════════════════════════════════════════════════
Generates a PDDL problem file from user inputs and the KB.
The resulting .pddl file is valid PDDL 1.2 and can be loaded
by any compliant planner (Fast Downward, ENHSP, Metric-FF …).
"""

from knowledge_base import CITIES, ORIGIN_CITIES, get_flight_cost
import os, datetime


def sanitize(s: str) -> str:
    """Convert a string to a safe PDDL identifier."""
    return s.lower().replace(" ", "_").replace("'","").replace(",","") \
             .replace("-","_").replace("(","").replace(")","").replace("/","_")


def generate_problem(
    origin: str,           # city pddl-id  e.g. "new_york"
    destination: str,      # city pddl-id  e.g. "paris"
    budget: int,           # total USD
    duration: int,         # days
    hotel_style: str,      # budget | midrange | luxury | boutique
    interests: list,       # list of tag strings
    travellers: int,
    output_dir: str = "pddl_output"
) -> tuple:
    """
    Returns (problem_pddl_string, filepath, problem_meta_dict)
    """
    os.makedirs(output_dir, exist_ok=True)

    city = CITIES[destination]
    hotel = city.hotels[hotel_style]
    budget_per_person = budget // travellers

    # Affordable flag logic
    flight_cost = get_flight_cost(origin, destination) or 700
    hotel_total = hotel.cost_per_night * duration
    # Budget sufficient if flight + hotel ≤ 80% of per-person budget
    budget_ok = (flight_cost + hotel_total) <= budget_per_person * 0.85

    # Filter attractions by interest & affordability
    affordable_attractions = [
        att for att in city.attractions
        if att.entry_cost <= (budget_per_person * 0.05)  # ≤5% of per-person budget
    ]
    interest_attractions = [
        att for att in affordable_attractions
        if any(tag in att.category for tag in interests)
           or any(tag in att.name.lower() for tag in interests)
    ]
    # Merge — interest ones first, then others
    all_attrs = interest_attractions + [a for a in affordable_attractions if a not in interest_attractions]
    target_attrs = all_attrs[:min(len(all_attrs), duration * 2)]  # ≤2 per day

    # Objects
    agent_id   = "traveller1"
    origin_id  = origin
    dest_id    = destination
    hotel_id   = hotel.pddl_id()
    transport_id = sanitize(city.transport_mode)
    attr_ids   = [att.pddl_id() for att in target_attrs]

    # Goal attractions (visit all selected)
    goal_visits = "\n".join(
        f"        (visited {agent_id} {aid})" for aid in attr_ids
    )

    # Init predicates
    affordable_flights_init = (
        f"        (affordable-flight {origin_id} {dest_id} {agent_id})"
        if budget_ok else ""
    )
    affordable_hotel_init = (
        f"        (affordable-hotel {hotel_id} {agent_id})"
        if hotel.cost_per_night <= budget_per_person * 0.15 else ""
    )
    affordable_entries = "\n".join(
        f"        (affordable-entry {att.pddl_id()} {agent_id})"
        for att in target_attrs
    )

    attraction_defs = "\n".join(
        f"        (attraction-in {att.pddl_id()} {dest_id})\n"
        f"        (attraction-open {att.pddl_id()})"
        for att in target_attrs
    )

    pddl = f""";; ============================================================
;; PDDL PROBLEM FILE — AUTO-GENERATED
;; Trip  : {city.name} ({duration} days, {travellers} traveller(s))
;; Budget: ${budget:,} USD  |  Hotel style: {hotel_style}
;; Interests: {', '.join(interests)}
;; Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
;; ============================================================

(define (problem trip-{dest_id}-{duration}d)

  (:domain travel-planner)

  ;; ── Object Declarations ────────────────────────────────────
  (:objects
    {agent_id}                                   - agent
    {origin_id} {dest_id}                        - city
    {hotel_id}                                   - hotel
    {' '.join(attr_ids) if attr_ids else '; no-attractions'}  - attraction
    {transport_id}                               - transport-mode
  )

  ;; ── Initial State ──────────────────────────────────────────
  (:init

    ;; Agent starts at origin
    (at {agent_id} {origin_id})

    ;; Flight route exists
    (connected {origin_id} {dest_id})
    (connected {dest_id} {origin_id})    ; return leg

    ;; Hotel is in destination city
    (hotel-in {hotel_id} {dest_id})

    ;; Transport available in destination
    (transport-available {transport_id} {dest_id})

{attraction_defs}

    ;; Budget / affordability atoms
    {"(budget-sufficient " + agent_id + ")" if budget_ok else "; budget-insufficient — planner cannot proceed"}
{affordable_flights_init}
{affordable_hotel_init}
{affordable_entries}
  )

  ;; ── Goal State ─────────────────────────────────────────────
  ;; The planner must achieve ALL of these predicates
  (:goal
    (and
      ;; 1. Agent has flown to destination
      (at {agent_id} {dest_id})

      ;; 2. Accommodation established
      (staying-at {agent_id} {hotel_id})
      (base-established {agent_id} {dest_id})

      ;; 3. Local transport arranged
      (transport-arranged {agent_id} {dest_id})

      ;; 4. Attractions visited (interest-filtered)
{goal_visits}

      ;; 5. Cultural immersion achieved
      (culture-experienced {agent_id} {dest_id})

      ;; 6. Trip complete
      (trip-complete {agent_id} {dest_id})
    )
  )

)
;; ── End of problem ─────────────────────────────────────────
"""

    filename = f"problem_{dest_id}_{duration}d_{hotel_style}.pddl"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(pddl)

    meta = {
        "agent": agent_id,
        "origin": origin_id,
        "destination": dest_id,
        "hotel_id": hotel_id,
        "hotel_name": hotel.name,
        "hotel_cost": hotel.cost_per_night,
        "transport_id": transport_id,
        "attraction_ids": attr_ids,
        "attractions": target_attrs,
        "budget_ok": budget_ok,
        "flight_cost": flight_cost * travellers,
        "hotel_total": hotel_total * travellers,
        "filepath": filepath,
        "filename": filename,
    }
    return pddl, filepath, meta
