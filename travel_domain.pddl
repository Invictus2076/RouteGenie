;;; ============================================================
;;; TRAVEL PLANNER — PDDL 1.2 DOMAIN DEFINITION
;;; Concepts: STRIPS operators, typed predicates, action schemas
;;; ============================================================

(define (domain travel-planner)

  (:requirements
    :strips
    :typing
    :equality
    :negative-preconditions
  )

  ;; ── Types ──────────────────────────────────────────────────
  (:types
    agent
    city
    hotel
    attraction
    transport-mode
    ticket
    meal-type
  )

  ;; ── Predicates (world-state atoms) ────────────────────────
  (:predicates

    ;; Location & movement
    (at              ?a - agent   ?c - city)
    (connected       ?c1 - city   ?c2 - city)       ; flight route exists

    ;; Ticket & booking
    (has-ticket      ?a - agent   ?c1 - city  ?c2 - city)
    (has-reservation ?a - agent   ?h - hotel)

    ;; Accommodation
    (hotel-in        ?h - hotel   ?c - city)
    (staying-at      ?a - agent   ?h - hotel)
    (base-established ?a - agent  ?c - city)

    ;; Transport
    (transport-available ?t - transport-mode  ?c - city)
    (transport-arranged  ?a - agent           ?c - city)

    ;; Attractions
    (attraction-in   ?att - attraction  ?c - city)
    (attraction-open ?att - attraction)
    (visited         ?a - agent  ?att - attraction)

    ;; Goals & experience
    (culture-experienced   ?a - agent  ?c - city)
    (trip-complete         ?a - agent  ?c - city)

    ;; Budget (simplified as boolean tiers)
    (budget-sufficient    ?a - agent)
    (affordable-hotel     ?h - hotel  ?a - agent)
    (affordable-flight    ?c1 - city  ?c2 - city  ?a - agent)
    (affordable-entry     ?att - attraction  ?a - agent)
  )

  ;; ══════════════════════════════════════════════════════════
  ;; OPERATOR 1 — BUY_FLIGHT_TICKET
  ;; Pre : agent is at origin, route exists, budget ok
  ;; Add : agent holds a ticket origin→dest
  ;; Del : (none — budget handled externally)
  ;; ══════════════════════════════════════════════════════════
  (:action BUY_FLIGHT_TICKET
    :parameters  (?a - agent  ?origin - city  ?dest - city)
    :precondition
      (and
        (at ?a ?origin)
        (connected ?origin ?dest)
        (affordable-flight ?origin ?dest ?a)
        (budget-sufficient ?a)
        (not (has-ticket ?a ?origin ?dest))
      )
    :effect
      (and
        (has-ticket ?a ?origin ?dest)
      )
  )

  ;; ══════════════════════════════════════════════════════════
  ;; OPERATOR 2 — TAKE_FLIGHT
  ;; Pre : agent at origin with valid ticket
  ;; Add : agent now at destination
  ;; Del : agent no longer at origin, ticket consumed
  ;; ══════════════════════════════════════════════════════════
  (:action TAKE_FLIGHT
    :parameters  (?a - agent  ?origin - city  ?dest - city)
    :precondition
      (and
        (at ?a ?origin)
        (has-ticket ?a ?origin ?dest)
        (connected ?origin ?dest)
      )
    :effect
      (and
        (at ?a ?dest)
        (not (at ?a ?origin))
        (not (has-ticket ?a ?origin ?dest))
      )
  )

  ;; ══════════════════════════════════════════════════════════
  ;; OPERATOR 3 — BOOK_HOTEL
  ;; Pre : agent at city, hotel is in city, affordable, no existing booking
  ;; Add : reservation granted
  ;; Del : —
  ;; ══════════════════════════════════════════════════════════
  (:action BOOK_HOTEL
    :parameters  (?a - agent  ?h - hotel  ?c - city)
    :precondition
      (and
        (at ?a ?c)
        (hotel-in ?h ?c)
        (affordable-hotel ?h ?a)
        (not (has-reservation ?a ?h))
      )
    :effect
      (and
        (has-reservation ?a ?h)
      )
  )

  ;; ══════════════════════════════════════════════════════════
  ;; OPERATOR 4 — CHECK_IN
  ;; Pre : agent at city, holds reservation, not already staying
  ;; Add : staying-at, base-established
  ;; Del : —
  ;; ══════════════════════════════════════════════════════════
  (:action CHECK_IN
    :parameters  (?a - agent  ?h - hotel  ?c - city)
    :precondition
      (and
        (at ?a ?c)
        (has-reservation ?a ?h)
        (hotel-in ?h ?c)
        (not (staying-at ?a ?h))
      )
    :effect
      (and
        (staying-at ?a ?h)
        (base-established ?a ?c)
      )
  )

  ;; ══════════════════════════════════════════════════════════
  ;; OPERATOR 5 — ARRANGE_LOCAL_TRANSPORT
  ;; Pre : agent at city, transport mode available there
  ;; Add : transport-arranged for agent in city
  ;; Del : —
  ;; ══════════════════════════════════════════════════════════
  (:action ARRANGE_LOCAL_TRANSPORT
    :parameters  (?a - agent  ?t - transport-mode  ?c - city)
    :precondition
      (and
        (at ?a ?c)
        (transport-available ?t ?c)
        (not (transport-arranged ?a ?c))
      )
    :effect
      (and
        (transport-arranged ?a ?c)
      )
  )

  ;; ══════════════════════════════════════════════════════════
  ;; OPERATOR 6 — VISIT_ATTRACTION
  ;; Pre : agent based in city, attraction open & affordable, transport ready
  ;; Add : visited(agent, attraction)
  ;; Del : —
  ;; ══════════════════════════════════════════════════════════
  (:action VISIT_ATTRACTION
    :parameters  (?a - agent  ?att - attraction  ?c - city)
    :precondition
      (and
        (at ?a ?c)
        (base-established ?a ?c)
        (transport-arranged ?a ?c)
        (attraction-in ?att ?c)
        (attraction-open ?att)
        (affordable-entry ?att ?a)
        (not (visited ?a ?att))
      )
    :effect
      (and
        (visited ?a ?att)
      )
  )

  ;; ══════════════════════════════════════════════════════════
  ;; OPERATOR 7 — EXPERIENCE_LOCAL_CULTURE
  ;; Pre : agent based in city, has visited at least one attraction
  ;; Add : culture-experienced
  ;; Del : —
  ;; ══════════════════════════════════════════════════════════
  (:action EXPERIENCE_LOCAL_CULTURE
    :parameters  (?a - agent  ?c - city  ?att - attraction)
    :precondition
      (and
        (at ?a ?c)
        (base-established ?a ?c)
        (visited ?a ?att)
        (attraction-in ?att ?c)
        (not (culture-experienced ?a ?c))
      )
    :effect
      (and
        (culture-experienced ?a ?c)
      )
  )

  ;; ══════════════════════════════════════════════════════════
  ;; OPERATOR 8 — COMPLETE_TRIP
  ;; Pre : all goals satisfied — base established, culture experienced
  ;; Add : trip-complete
  ;; Del : staying-at (check out), base-established
  ;; ══════════════════════════════════════════════════════════
  (:action COMPLETE_TRIP
    :parameters  (?a - agent  ?c - city  ?h - hotel)
    :precondition
      (and
        (at ?a ?c)
        (staying-at ?a ?h)
        (base-established ?a ?c)
        (culture-experienced ?a ?c)
        (hotel-in ?h ?c)
      )
    :effect
      (and
        (trip-complete ?a ?c)
        (not (staying-at ?a ?h))
        (not (base-established ?a ?c))
      )
  )

)
;; ── End of domain ──────────────────────────────────────────
