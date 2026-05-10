"""Modello Operativo (Livello 3): Dispatch Real-Time.
Euristica greedy per assegnare richieste urgenti/impreviste."""
import numpy as np
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.synthetic_data import build_nodes, build_carriers, haversine_km


def dispatch_urgent(request, carriers, carrier_schedule=None):
    """Assegna una richiesta urgente al vettore migliore disponibile.
    Algoritmo greedy con scoring pesato."""
    nodes = build_nodes()
    carrier_map = {c["id"]: c for c in carriers}

    # Filtra vettori idonei
    eligible = []
    for c in carriers:
        # Tipo veicolo compatibile
        if request["service"] == "ambulance" and c["n_ambulance"] == 0:
            continue

        # Distanza dal vettore all'origine
        dist_to_origin = haversine_km(
            c["base_lat"], c["base_lon"],
            nodes[request["origin"]]["lat"], nodes[request["origin"]]["lon"]
        ) * 1.35

        # Max raggio di risposta: 50 km per urgenti
        if dist_to_origin > 50:
            continue

        # Controlla carico giornaliero
        current_load = 0
        if carrier_schedule and c["id"] in carrier_schedule:
            current_load = len(carrier_schedule[c["id"]])
        if current_load >= c["max_daily_trips"]:
            continue

        # Calcola score
        km = round(dist_to_origin, 1)
        score = (
            -km * 1.0                          # Minimizza distanza
            + c["reliability"] * 30             # Premia affidabilità
            - (current_load / c["max_daily_trips"]) * 20  # Penalizza carico alto
        )

        eligible.append({
            "carrier_id": c["id"],
            "carrier_name": c["name"],
            "federation": c["federation"],
            "km_to_origin": km,
            "score": score,
            "current_load": current_load,
            "reliability": c["reliability"],
        })

    if not eligible:
        return None

    # Ordina per score decrescente
    eligible.sort(key=lambda x: x["score"], reverse=True)
    best = eligible[0]

    return {
        "request_id": request["id"],
        "carrier_id": best["carrier_id"],
        "carrier_name": best["carrier_name"],
        "km_to_origin": best["km_to_origin"],
        "score": round(best["score"], 2),
        "reliability": best["reliability"],
        "current_load": best["current_load"],
    }


def simulate_operational_day(n_urgent=12):
    """Simula una giornata di dispatch operativo."""
    from utils.synthetic_data import generate_daily_requests
    np.random.seed(123)

    carriers = build_carriers()
    requests = generate_daily_requests(n_planned=0, n_urgent=n_urgent)
    nodes = build_nodes()

    # Simula schedule già parziale (mezza giornata di pianificati)
    carrier_schedule = {c["id"]: ["planned"] * np.random.randint(2, 6) for c in carriers}

    results = []
    for req in requests:
        assignment = dispatch_urgent(req, carriers, carrier_schedule)
        if assignment:
            assignment["origin"] = req["origin"]
            assignment["origin_name"] = nodes[req["origin"]]["name"]
            assignment["dest"] = req["destination"]
            assignment["dest_name"] = nodes[req["destination"]]["name"]
            assignment["district"] = req["district"]
            assignment["is_out_of_territory"] = (
                carriers[[c["id"] for c in carriers].index(assignment["carrier_id"])]["base_district"]
                != req["district"]
            )
            carrier_schedule[assignment["carrier_id"]].append(req["id"])
        else:
            assignment = {
                "request_id": req["id"], "carrier_id": "NONE",
                "carrier_name": "Nessun vettore disponibile",
                "km_to_origin": 0, "score": 0, "reliability": 0, "current_load": 0,
                "origin": req["origin"], "origin_name": nodes[req["origin"]]["name"],
                "dest": req["destination"], "dest_name": nodes[req["destination"]]["name"],
                "district": req["district"], "is_out_of_territory": True,
            }
        results.append(assignment)

    n_assigned = sum(1 for r in results if r["carrier_id"] != "NONE")
    avg_km = np.mean([r["km_to_origin"] for r in results if r["carrier_id"] != "NONE"]) if n_assigned > 0 else 0
    out_territory = sum(1 for r in results if r.get("is_out_of_territory"))

    return {
        "n_total": len(results),
        "n_assigned": n_assigned,
        "n_unassigned": len(results) - n_assigned,
        "avg_km_response": round(avg_km, 1),
        "pct_out_territory": round(out_territory / max(n_assigned, 1) * 100, 1),
        "assignments": results,
    }


if __name__ == "__main__":
    result = simulate_operational_day(12)
    print(f"Richieste urgenti: {result['n_total']}")
    print(f"Assegnate: {result['n_assigned']}, Non assegnate: {result['n_unassigned']}")
    print(f"km medi di risposta: {result['avg_km_response']}")
    print(f"% fuori territorio: {result['pct_out_territory']}%")
