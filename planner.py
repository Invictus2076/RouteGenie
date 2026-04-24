"""
planner.py
═══════════════════════════════════════════════════════════════
STRIPS + Goal Stack Planning Engine
Reads PDDL domain/problem, runs forward state-space search,
returns a sequenced, conflict-free action plan.
"""

from knowledge_base import (
    CITIES, get_flight_cost, get_flight_hours, get_airline,
    ORIGIN_CITIES, ALL_CITY_NAMES
)
from pddl_generator import generate_problem
import datetime, random


# ── STRIPS World State ────────────────────────────────────────────────

class WorldState:
    def __init__(self):
        self.atoms: set = set()

    def add(self, *predicates):
        for p in predicates:
            self.atoms.add(p)

    def remove(self, *predicates):
        for p in predicates:
            self.atoms.discard(p)

    def holds(self, predicate) -> bool:
        return predicate in self.atoms

    def copy(self):
        ws = WorldState()
        ws.atoms = set(self.atoms)
        return ws

    def __repr__(self):
        return f"WorldState({len(self.atoms)} atoms)"


# ── STRIPS Operator ───────────────────────────────────────────────────

class Operator:
    def __init__(self, name, params, preconditions, add_effects, del_effects,
                 action_type="action", cost=0, description=""):
        self.name         = name
        self.params       = params
        self.preconditions = preconditions   # list of strings
        self.add_effects  = add_effects      # list of strings
        self.del_effects  = del_effects      # list of strings
        self.action_type  = action_type      # flight | hotel | transport | activity
        self.cost         = cost             # USD
        self.description  = description

    def is_applicable(self, state: WorldState) -> bool:
        return all(state.holds(p) for p in self.preconditions)

    def apply(self, state: WorldState) -> WorldState:
        new_state = state.copy()
        for eff in self.del_effects:
            new_state.remove(eff)
        for eff in self.add_effects:
            new_state.add(eff)
        return new_state


# ── Goal Stack Planner ────────────────────────────────────────────────

class GoalStackPlanner:
    """
    Classic Goal Stack / Means-Ends Analysis planner.
    Pushes goals onto a stack, selects relevant operators,
    and resolves sub-goals recursively.
    """

    def __init__(self, initial_state: WorldState, goal_atoms: list, operators: list):
        self.initial_state = initial_state
        self.goal_atoms    = goal_atoms
        self.operators     = operators
        self.plan          = []
        self.goal_stack    = []          # planning trace for UI
        self.state_trace   = []          # world state at each step

    def find_operator(self, goal: str):
        """Return the first operator whose add-effects contain the goal."""
        for op in self.operators:
            if goal in op.add_effects:
                return op
        return None

    def solve(self) -> list:
        state = self.initial_state.copy()
        stack = list(reversed(self.goal_atoms))   # push all top-level goals
        visited_goals = set()

        self.goal_stack.append({
            "type": "goal",
            "label": f"ACHIEVE: {' ∧ '.join(self.goal_atoms[:2])} … ({len(self.goal_atoms)} goals)",
            "level": 0
        })

        while stack:
            current = stack.pop()

            if isinstance(current, str):
                # It's a goal atom
                if state.holds(current):
                    self.goal_stack.append({
                        "type": "satisfied",
                        "label": f"✓ {current}",
                        "level": 1
                    })
                    continue

                if current in visited_goals:
                    continue
                visited_goals.add(current)

                op = self.find_operator(current)
                if op is None:
                    continue

                self.goal_stack.append({
                    "type": "subgoal",
                    "label": f"SUB-GOAL: {current}",
                    "level": 1,
                    "operator": op.name
                })

                # Push: operator, then its preconditions as sub-goals
                stack.append(op)
                for pre in reversed(op.preconditions):
                    if not state.holds(pre):
                        stack.append(pre)

            elif isinstance(current, Operator):
                if current.is_applicable(state):
                    state = current.apply(state)
                    self.plan.append(current)
                    self.state_trace.append(set(state.atoms))
                    self.goal_stack.append({
                        "type": "action",
                        "label": f"APPLY: {current.name}",
                        "level": 2,
                        "operator": current.name
                    })

        self.goal_stack.append({
            "type": "satisfied",
            "label": "✓ All goals achieved — TRIP COMPLETE",
            "level": 0
        })
        return self.plan


# ── Travel Planner (main interface) ───────────────────────────────────

class TravelPlanner:

    def __init__(self, origin, destination, budget, duration, hotel_style,
                 interests, travellers, dep_date_str):
        self.origin       = origin
        self.destination  = destination
        self.budget       = int(budget)
        self.duration     = int(duration)
        self.hotel_style  = hotel_style
        self.interests    = interests
        self.travellers   = int(travellers)

        try:
            self.dep_date = datetime.date.fromisoformat(dep_date_str)
        except Exception:
            self.dep_date = datetime.date.today() + datetime.timedelta(days=30)

        self.ret_date = self.dep_date + datetime.timedelta(days=self.duration)
        self.city     = CITIES[destination]
        self.hotel    = self.city.hotels[hotel_style]
        self.warnings = []

    # ── Currency ─────────────────────────────────────────────
    USD_TO_INR = 83.5   # 1 USD ≈ ₹83.5

    def _inr(self, usd: float) -> str:
        """Format USD amount as Indian Rupees (Indian comma system)."""
        rupees = round(usd * self.USD_TO_INR)
        s = str(rupees)
        if len(s) <= 3:
            return f"₹{s}"
        last3 = s[-3:]
        rest = s[:-3]
        groups = []
        while len(rest) > 2:
            groups.append(rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.append(rest)
        return "₹" + ",".join(reversed(groups)) + "," + last3

        # ── Cost Calculations ────────────────────────────────────

    def _flight_cost(self):
        base = get_flight_cost(self.origin, self.destination) or 700
        return base * self.travellers

    def _hotel_cost(self):
        return self.hotel.cost_per_night * self.duration * self.travellers

    def _daily_cost(self):
        return self.city.cost_per_day * self.duration * self.travellers * 0.4

    def _total_est(self):
        return self._flight_cost() + self._hotel_cost() + self._daily_cost()

    def _budget_remaining(self):
        return self.budget - self._total_est()

    # ── Attraction Filtering ─────────────────────────────────

    def _selected_attractions(self):
        city = self.city
        budget_per_person = self.budget // self.travellers
        affordable = [a for a in city.attractions
                      if a.entry_cost <= budget_per_person * 0.06]

        interest_match = [a for a in affordable
                          if any(i in a.category or i in a.name.lower()
                                 for i in self.interests)]
        others = [a for a in affordable if a not in interest_match]
        combined = interest_match + others
        return combined[:min(len(combined), self.duration * 2)]

    # ── Build STRIPS Operators ───────────────────────────────

    def _build_operators(self, target_attrs, pddl_meta):
        a   = "traveller1"
        org = self.origin
        dst = self.destination
        hid = pddl_meta["hotel_id"]
        tid = pddl_meta["transport_id"]
        fc  = self._flight_cost()
        hc  = self._hotel_cost()

        ops = []

        ops.append(Operator(
            name=f"BUY_FLIGHT_TICKET({org.upper()}→{dst.upper()})",
            params=f"?a={a}, ?origin={org}, ?dest={dst}",
            preconditions=[f"at({a},{org})", f"connected({org},{dst})",
                           f"budget-sufficient({a})", f"affordable-flight({org},{dst},{a})"],
            add_effects=[f"has-ticket({a},{org},{dst})"],
            del_effects=[],
            action_type="flight",
            cost=fc,
            description=f"Purchase {self.travellers} economy ticket(s) — "
                        f"{get_airline(org,dst)} — {self._inr(fc)} total"
        ))

        ops.append(Operator(
            name=f"TAKE_FLIGHT({org.upper()}→{dst.upper()})",
            params=f"?a={a}, ?origin={org}, ?dest={dst}",
            preconditions=[f"at({a},{org})", f"has-ticket({a},{org},{dst})",
                           f"connected({org},{dst})"],
            add_effects=[f"at({a},{dst})"],
            del_effects=[f"at({a},{org})", f"has-ticket({a},{org},{dst})"],
            action_type="flight",
            cost=0,
            description=f"Depart {ALL_CITY_NAMES.get(org, org)} → {self.city.name}. "
                        f"~{get_flight_hours(org,dst):.0f}h flight."
        ))

        ops.append(Operator(
            name=f"BOOK_HOTEL({hid.upper()})",
            params=f"?a={a}, ?h={hid}, ?c={dst}",
            preconditions=[f"at({a},{dst})", f"hotel-in({hid},{dst})",
                           f"affordable-hotel({hid},{a})"],
            add_effects=[f"has-reservation({a},{hid})"],
            del_effects=[],
            action_type="hotel",
            cost=hc,
            description=f"Reserve {self.hotel.name} — "
                        f"{self._inr(self.hotel.cost_per_night)}/night × {self.duration} nights "
                        f"× {self.travellers} = {self._inr(hc)}"
        ))

        ops.append(Operator(
            name=f"CHECK_IN({hid.upper()})",
            params=f"?a={a}, ?h={hid}, ?c={dst}",
            preconditions=[f"at({a},{dst})", f"has-reservation({a},{hid})",
                           f"hotel-in({hid},{dst})"],
            add_effects=[f"staying-at({a},{hid})", f"base-established({a},{dst})"],
            del_effects=[],
            action_type="hotel",
            cost=0,
            description=f"Check in to {self.hotel.name}. "
                        f"Collect key cards. Base established in {self.city.name}."
        ))

        ops.append(Operator(
            name=f"ARRANGE_LOCAL_TRANSPORT({tid.upper()})",
            params=f"?a={a}, ?t={tid}, ?c={dst}",
            preconditions=[f"at({a},{dst})", f"transport-available({tid},{dst})"],
            add_effects=[f"transport-arranged({a},{dst})"],
            del_effects=[],
            action_type="transport",
            cost=40 * self.travellers,
            description=f"Arrange {self.city.transport_mode} pass/rental for "
                        f"{self.travellers} traveller(s) in {self.city.name}."
        ))

        # Attraction operators
        first_attr = None
        for att in target_attrs:
            aid = att.pddl_id()
            if first_attr is None:
                first_attr = aid
            ops.append(Operator(
                name=f"VISIT_ATTRACTION({att.name[:30]})",
                params=f"?a={a}, ?att={aid}, ?c={dst}",
                preconditions=[f"at({a},{dst})", f"base-established({a},{dst})",
                               f"transport-arranged({a},{dst})",
                               f"attraction-in({aid},{dst})", f"attraction-open({aid})",
                               f"affordable-entry({aid},{a})"],
                add_effects=[f"visited({a},{aid})"],
                del_effects=[],
                action_type="activity",
                cost=att.entry_cost * self.travellers,
                description=att.tip or f"Visit {att.name} in {self.city.name}."
            ))

        # Culture experience (needs at least one visit)
        if first_attr:
            ops.append(Operator(
                name=f"EXPERIENCE_LOCAL_CULTURE({dst.upper()})",
                params=f"?a={a}, ?c={dst}, ?att={first_attr}",
                preconditions=[f"at({a},{dst})", f"base-established({a},{dst})",
                               f"visited({a},{first_attr})",
                               f"attraction-in({first_attr},{dst})"],
                add_effects=[f"culture-experienced({a},{dst})"],
                del_effects=[],
                action_type="activity",
                cost=0,
                description=f"Cultural immersion achieved in {self.city.name}."
            ))

        # Complete trip
        ops.append(Operator(
            name=f"COMPLETE_TRIP({dst.upper()})",
            params=f"?a={a}, ?c={dst}, ?h={hid}",
            preconditions=[f"at({a},{dst})", f"staying-at({a},{hid})",
                           f"base-established({a},{dst})",
                           f"culture-experienced({a},{dst})",
                           f"hotel-in({hid},{dst})"],
            add_effects=[f"trip-complete({a},{dst})"],
            del_effects=[f"staying-at({a},{hid})", f"base-established({a},{dst})"],
            action_type="activity",
            cost=0,
            description=f"Check out of {self.hotel.name}. Trip to {self.city.name} complete."
        ))

        return ops

    # ── Build Initial State ──────────────────────────────────

    def _build_initial_state(self, pddl_meta, target_attrs):
        ws = WorldState()
        a   = "traveller1"
        org = self.origin
        dst = self.destination
        hid = pddl_meta["hotel_id"]
        tid = pddl_meta["transport_id"]
        budget_per_person = self.budget // self.travellers

        ws.add(f"at({a},{org})")
        ws.add(f"connected({org},{dst})")
        ws.add(f"connected({dst},{org})")
        ws.add(f"hotel-in({hid},{dst})")
        ws.add(f"transport-available({tid},{dst})")

        if (self._flight_cost() + self._hotel_cost()) <= self.budget * 0.85:
            ws.add(f"budget-sufficient({a})")
            ws.add(f"affordable-flight({org},{dst},{a})")

        if self.hotel.cost_per_night <= budget_per_person * 0.15:
            ws.add(f"affordable-hotel({hid},{a})")

        for att in target_attrs:
            aid = att.pddl_id()
            ws.add(f"attraction-in({aid},{dst})")
            ws.add(f"attraction-open({aid})")
            if att.entry_cost <= budget_per_person * 0.06:
                ws.add(f"affordable-entry({aid},{a})")

        return ws

    # ── Build Goal Atoms ─────────────────────────────────────

    def _build_goal_atoms(self, pddl_meta, target_attrs):
        a   = "traveller1"
        dst = self.destination
        hid = pddl_meta["hotel_id"]
        goals = [
            f"at({a},{dst})",
            f"staying-at({a},{hid})",
            f"base-established({a},{dst})",
            f"transport-arranged({a},{dst})",
        ]
        for att in target_attrs:
            goals.append(f"visited({a},{att.pddl_id()})")
        goals.append(f"culture-experienced({a},{dst})")
        goals.append(f"trip-complete({a},{dst})")
        return goals

    # ── Main entry point ─────────────────────────────────────

    def generate(self):
        # 1. Generate PDDL files
        pddl_str, pddl_path, pddl_meta = generate_problem(
            origin=self.origin,
            destination=self.destination,
            budget=self.budget,
            duration=self.duration,
            hotel_style=self.hotel_style,
            interests=self.interests,
            travellers=self.travellers
        )

        target_attrs = self._selected_attractions()

        # 2. Build world state & operators
        initial_state = self._build_initial_state(pddl_meta, target_attrs)
        goal_atoms    = self._build_goal_atoms(pddl_meta, target_attrs)
        operators     = self._build_operators(target_attrs, pddl_meta)

        # 3. Run Goal Stack Planner
        planner       = GoalStackPlanner(initial_state, goal_atoms, operators)
        plan_ops      = planner.solve()

        # Budget warning
        remaining = self._budget_remaining()
        if remaining < 0:
            self.warnings.append(
                f"Estimated cost {self._inr(self._total_est())} exceeds budget "
                f"{self._inr(self.budget)} by {self._inr(abs(remaining))}. "
                f"Consider reducing hotel style or duration."
            )

        # 4. Build rich action list for UI
        actions = self._enrich_plan(plan_ops, pddl_meta)

        return {
            "summary": {
                "origin":       self.origin,
                "destination":  self.destination,
                "city_name":    self.city.name,
                "origin_name":  ALL_CITY_NAMES.get(self.origin, self.origin),
                "country":      self.city.country,
                "flag":         self.city.flag,
                "duration":     self.duration,
                "travellers":   self.travellers,
                "hotel":        self.hotel.name,
                "hotel_style":  self.hotel_style,
                "hotel_stars":  self.hotel.stars,
                "dep_date":     self.dep_date.strftime("%a, %d %b %Y"),
                "ret_date":     self.ret_date.strftime("%a, %d %b %Y"),
                "flight_cost":  self._inr(self._flight_cost()),
                "hotel_cost":   self._inr(self._hotel_cost()),
                "daily_cost":   self._inr(self._daily_cost()),
                "total_cost":   self._inr(self._total_est()),
                "remaining":    self._inr(max(0, remaining)),
                "transport":    self.city.transport_mode,
                "best_season":  self.city.best_season,
                "timezone":     self.city.timezone,
                "airline":      get_airline(self.origin, self.destination),
                "flight_hours": get_flight_hours(self.origin, self.destination),
                "num_attractions": len(target_attrs),
                "warnings":     self.warnings,
            },
            "actions":    actions,
            "goal_stack": planner.goal_stack,
            "pddl_str":   pddl_str,
            "pddl_file":  pddl_path,
            "pddl_meta":  {
                k: v for k, v in pddl_meta.items()
                if k != "attractions"          # Attraction objects — not JSON-safe
            },
            "initial_state": sorted(list(initial_state.atoms)),
            "goal_atoms": goal_atoms,
        }

    def _enrich_plan(self, ops, pddl_meta):
        """Add dates, day numbers, and rich details to each operator."""
        enriched = []
        day = 0
        attr_day_counter = {}

        for i, op in enumerate(ops):
            date = self.dep_date + datetime.timedelta(days=day)
            if "VISIT_ATTRACTION" in op.name or "EXPERIENCE" in op.name or "COMPLETE" in op.name:
                if day < self.duration:
                    pass
                if "VISIT_ATTRACTION" in op.name:
                    key = day
                    attr_day_counter[key] = attr_day_counter.get(key, 0) + 1
                    if attr_day_counter[key] > 2:
                        day = min(day + 1, self.duration - 1)
                        date = self.dep_date + datetime.timedelta(days=day)

            enriched.append({
                "step":        i + 1,
                "name":        op.name,
                "params":      op.params,
                "type":        op.action_type,
                "cost":        op.cost,
                "description": op.description,
                "preconditions": op.preconditions,
                "add_effects": op.add_effects,
                "del_effects": op.del_effects,
                "date":        date.strftime("%a %d %b"),
                "day":         day + 1,
            })

            if "TAKE_FLIGHT" in op.name and "→" in op.name:
                day = 1   # arrived; day 1 starts
            elif op.action_type == "activity" and "COMPLETE" not in op.name:
                pass

        return enriched
