"""Modello Tattico (Livello 2): Assegnamento Giornaliero.
Assegna i trasporti pianificati del giorno seguente (~50-70 richieste) ai vettori.
Risolvibile ogni notte per il giorno dopo."""
import pulp
import numpy as np
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.synthetic_data import (
    build_nodes, build_carriers, haversine_km, generate_daily_requests, ZONES
)


def compute_trip_km(nodes, origin, dest):
    h = haversine_km(nodes[origin]["lat"], nodes[origin]["lon"],
                     nodes[dest]["lat"], nodes[dest]["lon"])
    return round(h * 1.35, 1)


def compute_travel_km(nodes, carrier, origin, dest):
    h = haversine_km(carrier["base_lat"], carrier["base_lon"],
                     nodes[origin]["lat"], nodes[origin]["lon"])
    go = h * 1.35
    trip = compute_trip_km(nodes, origin, dest)
    h2 = haversine_km(nodes[dest]["lat"], nodes[dest]["lon"],
                      carrier["base_lat"], carrier["base_lon"])
    ret = h2 * 1.35
    return round(go + trip + ret, 1)


def time_to_minutes(t):
    h, m = map(int, t.split(":"))
    return h * 60 + m


def solve_tactical(requests=None, carriers=None, strategic_assignments=None):
    if carriers is None:
        carriers = build_carriers()
    nodes = build_nodes()

    if requests is None:
        requests = generate_daily_requests(n_planned=55, n_urgent=12)

    # Filtra solo richieste pianificate per il solver LP
    planned = [r for r in requests if r["priority"] == 2]

    carrier_ids = [c["id"] for c in carriers]
    carrier_map = {c["id"]: c for c in carriers}
    request_ids = [r["id"] for r in planned]
    request_map = {r["id"]: r for r in planned}

    # Matrice km: km[r][c] = km totali se richiesta r è assegnata a vettore c
    km_matrix = {}
    for r in planned:
        for c in carriers:
            km_matrix[(r["id"], c["id"])] = compute_travel_km(
                nodes, c, r["origin"], r["destination"])

    model = pulp.LpProblem("Assegnamento_Giornaliero", pulp.LpMinimize)

    # Variabili decisionali
    a = pulp.LpVariable.dicts("assign",
        ((r, c) for r in request_ids for c in carrier_ids),
        cat='Binary')

    slack = pulp.LpVariable.dicts("slack", request_ids, lowBound=0, cat='Binary')

    # Penalità fuori territorio per ogni coppia (richiesta, vettore)
    out_territory_penalty = {}
    for r in planned:
        for c in carriers:
            if c["base_district"] != r["district"]:
                out_territory_penalty[(r["id"], c["id"])] = 80  # 80 km-equivalenti di penalità
            else:
                out_territory_penalty[(r["id"], c["id"])] = 0

    # Obiettivo: minimizzare km + penalità fuori territorio + penalità richieste non assegnate
    model += (
        pulp.lpSum((km_matrix[(r, c)] + out_territory_penalty[(r, c)]) * a[r, c]
                   for r in request_ids for c in carrier_ids)
        + 500 * pulp.lpSum(slack[r] for r in request_ids)
    )

    # Vincolo 1: ogni richiesta assegnata a un solo vettore o slack
    for r in request_ids:
        model += pulp.lpSum(a[r, c] for c in carrier_ids) + slack[r] == 1, f"assign_{r}"

    # Vincolo 2: compatibilità tipo veicolo (semplificata: ambulance = n_ambulance > 0)
    for r in request_ids:
        req_service = request_map[r]["service"]
        if req_service == "ambulance":
            for c in carriers:
                if c["n_ambulance"] == 0:
                    model += a[r, c["id"]] == 0, f"veh_compat_{r}_{c['id']}"

    # Vincolo 3: limite viaggi giornalieri per vettore
    for c in carriers:
        model += (
            pulp.lpSum(a[r, c["id"]] for r in request_ids) <= c["max_daily_trips"],
            f"max_trips_{c['id']}"
        )

    # Vincolo 4: preferenza vettori vicini (soft constraint tramite proximinity)
    # Se il vettore è a >80 km dall'origine, penalizza fortemente
    for r in planned:
        for c in carriers:
            dist_origin = haversine_km(c["base_lat"], c["base_lon"],
                                       nodes[r["origin"]]["lat"], nodes[r["origin"]]["lon"]) * 1.35
            if dist_origin > 80:
                model += a[r["id"], c["id"]] == 0, f"too_far_{r['id']}_{c['id']}"

    model.solve(pulp.PULP_CBC_CMD(msg=0, timeLimit=60))

    if model.status != 1:
        print(f"Attenzione: status {pulp.LpStatus[model.status]}")

    # Estrai risultati
    assignments = []
    unassigned = []
    carrier_stats = {c: {"trips": 0, "km": 0} for c in carrier_ids}

    for r in planned:
        if pulp.value(slack[r["id"]]) and pulp.value(slack[r["id"]]) > 0.5:
            unassigned.append(r["id"])
            continue
        for c in carrier_ids:
            if pulp.value(a[r["id"], c]) and pulp.value(a[r["id"], c]) > 0.5:
                km = km_matrix[(r["id"], c)]
                assignments.append({
                    "request_id": r["id"],
                    "request_type": r["type"],
                    "origin": r["origin"],
                    "origin_name": nodes[r["origin"]]["name"],
                    "destination": r["destination"],
                    "dest_name": nodes[r["destination"]]["name"],
                    "district": r["district"],
                    "carrier_id": c,
                    "carrier_name": carrier_map[c]["name"],
                    "federation": carrier_map[c]["federation"],
                    "service": r["service"],
                    "km": km,
                    "time_window": f"{r['time_window_start']}-{r['time_window_end']}",
                    "is_out_of_territory": carrier_map[c]["base_district"] != r["district"],
                })
                carrier_stats[c]["trips"] += 1
                carrier_stats[c]["km"] += km

    total_km = sum(a["km"] for a in assignments)
    out_territory = sum(1 for a in assignments if a["is_out_of_territory"])

    return {
        "status": pulp.LpStatus[model.status],
        "total_km": round(total_km, 1),
        "n_assigned": len(assignments),
        "n_unassigned": len(unassigned),
        "pct_out_territory": round(out_territory / max(len(assignments), 1) * 100, 1),
        "assignments": assignments,
        "unassigned": unassigned,
        "carrier_stats": carrier_stats,
    }


def simulate_baseline_assignment(requests, carriers):
    """Simula AS-IS: assegnamento sub-ottimale che replica il problema del 15% fuori territorio.
    I vettori locali vengono saturati rapidamente (capacità ridotta nella pratica),
    e le richieste eccedenti vengono assegnate casualmente, spesso fuori territorio."""
    nodes = build_nodes()
    carrier_map = {c["id"]: c for c in carriers}
    planned = [r for r in requests if r["priority"] == 2]

    assignments = []
    # Simula capacità effettiva ridotta (turni, disponibilità volontari)
    effective_max = {c["id"]: max(2, c["max_daily_trips"] // 2) for c in carriers}
    carrier_load = {c["id"]: 0 for c in carriers}

    for r in planned:
        # 15% delle volte il personale non verifica prima il vettore locale (simulazione caos)
        use_local = np.random.random() > 0.15

        district_carriers = [c for c in carriers
                             if c["base_district"] == r["district"]
                             and carrier_load[c["id"]] < effective_max[c["id"]]]

        if use_local and district_carriers:
            # Prende il primo disponibile del distretto (non ottimizzato per vicinanza)
            chosen = district_carriers[0]
        else:
            # Cerca qualsiasi vettore disponibile - spesso fuori territorio
            available = [c for c in carriers if carrier_load[c["id"]] < effective_max[c["id"]]]
            if available:
                # Sceglie casualmente, simulando la mancanza di coordinamento
                chosen = available[np.random.randint(len(available))]
            else:
                assignments.append({
                    "request_id": r["id"], "km": 0, "carrier_id": "NONE",
                    "carrier_name": "Non assegnato", "federation": "N/A",
                    "is_out_of_territory": True, "service": r["service"],
                    "origin": r["origin"], "destination": r["destination"],
                    "origin_name": nodes[r["origin"]]["name"],
                    "dest_name": nodes[r["destination"]]["name"],
                    "district": r["district"], "request_type": r["type"],
                    "time_window": f"{r['time_window_start']}-{r['time_window_end']}",
                })
                continue

        km = compute_travel_km(nodes, chosen, r["origin"], r["destination"])
        carrier_load[chosen["id"]] += 1

        assignments.append({
            "request_id": r["id"],
            "request_type": r["type"],
            "origin": r["origin"],
            "origin_name": nodes[r["origin"]]["name"],
            "destination": r["destination"],
            "dest_name": nodes[r["destination"]]["name"],
            "district": r["district"],
            "carrier_id": chosen["id"],
            "carrier_name": chosen["name"],
            "federation": chosen["federation"],
            "service": r["service"],
            "km": km,
            "time_window": f"{r['time_window_start']}-{r['time_window_end']}",
            "is_out_of_territory": chosen["base_district"] != r["district"],
        })

    total_km = sum(a["km"] for a in assignments if a["carrier_id"] != "NONE")
    out_territory = sum(1 for a in assignments if a.get("is_out_of_territory"))
    n_assigned = sum(1 for a in assignments if a["carrier_id"] != "NONE")

    return {
        "total_km": round(total_km, 1),
        "n_assigned": n_assigned,
        "n_unassigned": len(planned) - n_assigned,
        "pct_out_territory": round(out_territory / max(n_assigned, 1) * 100, 1),
        "assignments": assignments,
    }


if __name__ == "__main__":
    np.random.seed(42)
    carriers = build_carriers()
    requests = generate_daily_requests(n_planned=55, n_urgent=12)

    print("=== BASELINE (AS-IS) ===")
    baseline = simulate_baseline_assignment(requests, carriers)
    print(f"km totali: {baseline['total_km']}")
    print(f"Assegnati: {baseline['n_assigned']}, Non assegnati: {baseline['n_unassigned']}")
    print(f"% fuori territorio: {baseline['pct_out_territory']}%")

    print("\n=== OTTIMIZZATO (TO-BE) ===")
    result = solve_tactical(requests, carriers)
    print(f"km totali: {result['total_km']}")
    print(f"Assegnati: {result['n_assigned']}, Non assegnati: {result['n_unassigned']}")
    print(f"% fuori territorio: {result['pct_out_territory']}%")
    print(f"Risparmio km: {baseline['total_km'] - result['total_km']} "
          f"({(baseline['total_km'] - result['total_km']) / baseline['total_km'] * 100:.1f}%)")
