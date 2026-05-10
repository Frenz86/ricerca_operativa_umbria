"""Modello Strategico (Livello 1): Allocazione Territorio.
Assegna i vettori alle 9 zone di servizio minimizzando i km attesi pesati per costo.
Risolvibile trimestralmente."""
import pulp
import numpy as np
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.synthetic_data import (
    build_nodes, build_carriers, build_zone_demand,
    ZONES, ZONE_NAMES, ZONE_DISTRICT, DISTRICTS,
    haversine_km
)


def compute_carrier_zone_distances(carriers, zones, district_centers):
    dist = {}
    for c in carriers:
        for z in zones:
            dc = district_centers[ZONE_DISTRICT[z]]
            d = haversine_km(c["base_lat"], c["base_lon"], dc[0], dc[1]) * 1.35
            dist[(c["id"], z)] = round(d, 1)
    return dist


def solve_strategic(carriers=None, zones=None, demand=None, dist=None, max_zones_per_carrier=3):
    if carriers is None:
        carriers = build_carriers()
    if zones is None:
        zones = ZONES
    if demand is None:
        demand = build_zone_demand()
    if dist is None:
        district_centers = {
            "Alto Tevere": (43.40, 12.27), "Alto Chiascio": (43.30, 12.68),
            "Perugino": (43.08, 12.37), "Trasimeno": (43.05, 12.05),
            "Assisano": (43.04, 12.60), "Media Valle": (42.85, 12.43),
        }
        dist = compute_carrier_zone_distances(carriers, zones, district_centers)

    vtypes = ["ambulance", "attrezzato"]
    carrier_ids = [c["id"] for c in carriers]
    carrier_map = {c["id"]: c for c in carriers}

    model = pulp.LpProblem("Allocazione_Territoriale", pulp.LpMinimize)

    # Variabili decisionali
    x = pulp.LpVariable.dicts("veicoli",
        ((c, z, v) for c in carrier_ids for z in zones for v in vtypes),
        lowBound=0, cat='Integer')

    y = pulp.LpVariable.dicts("attivo",
        ((c, z) for c in carrier_ids for z in zones),
        cat='Binary')

    # Obiettivo: minimizzare costo atteso (km * costo/km / affidabilità)
    model += pulp.lpSum(
        dist[(c, z)] * (carrier_map[c]["cost_per_km"] / carrier_map[c]["reliability"]) * x[c, z, v] * 2
        for c in carrier_ids for z in zones for v in vtypes
    )

    M = 10  # big-M: nessun vettore ha più di 10 veicoli di un tipo per zona

    # C1: Copertura domanda
    for z in zones:
        for v in vtypes:
            needed = demand[z][0 if v == "ambulance" else 1]
            model += pulp.lpSum(x[c, z, v] for c in carrier_ids) >= needed, f"domanda_{z}_{v}"

    # C2: Capacità vettore
    for c in carrier_ids:
        cap_amb = carrier_map[c]["n_ambulance"]
        cap_att = carrier_map[c]["n_attrezzato"]
        model += pulp.lpSum(x[c, z, "ambulance"] for z in zones) <= cap_amb, f"cap_amb_{c}"
        model += pulp.lpSum(x[c, z, "attrezzato"] for z in zones) <= cap_att, f"cap_att_{c}"

    # C3: Linking x-y
    for c in carrier_ids:
        for z in zones:
            for v in vtypes:
                model += x[c, z, v] <= M * y[c, z], f"link_{c}_{z}_{v}"

    # C4: Limite zone per vettore
    for c in carrier_ids:
        model += pulp.lpSum(y[c, z] for z in zones) <= max_zones_per_carrier, f"max_zone_{c}"

    # C5: Prossimità geografica (max 60 km dal base)
    for c in carrier_ids:
        for z in zones:
            if dist[(c, z)] > 60:
                model += y[c, z] == 0, f"prox_{c}_{z}"

    # C6: Minimo 2 vettori per zona
    for z in zones:
        model += pulp.lpSum(y[c, z] for c in carrier_ids) >= 2, f"ridondanza_{z}"

    # C7: Bilanciamento federazioni (max 60% vettori di una federazione per zona)
    federations = set(c["federation"] for c in carriers)
    for z in zones:
        for fed in federations:
            fed_carriers = [c["id"] for c in carriers if c["federation"] == fed]
            if len(fed_carriers) > 0:
                model += (
                    pulp.lpSum(y[c, z] for c in fed_carriers) <=
                    pulp.lpSum(y[c, z] for c in carrier_ids) * 0.6 + 0.5,
                    f"fed_balance_{z}_{fed}"
                )

    model.solve(pulp.PULP_CBC_CMD(msg=0))

    if model.status != 1:
        print(f"ATTENZIONE: modello non risolto ottimamente. Status: {pulp.LpStatus[model.status]}")
        return None

    # Estrai risultati
    assignments = []
    for c in carrier_ids:
        for z in zones:
            if pulp.value(y[c, z]) and pulp.value(y[c, z]) > 0.5:
                for v in vtypes:
                    n_veh = int(round(pulp.value(x[c, z, v]) or 0))
                    if n_veh > 0:
                        assignments.append({
                            "carrier_id": c,
                            "carrier_name": carrier_map[c]["name"],
                            "federation": carrier_map[c]["federation"],
                            "zone": z,
                            "zone_name": ZONE_NAMES[z],
                            "vehicle_type": v,
                            "n_vehicles": n_veh,
                            "avg_km": dist[(c, z)],
                            "cost_per_km": carrier_map[c]["cost_per_km"],
                        })

    total_cost = pulp.value(model.objective)
    return {
        "status": pulp.LpStatus[model.status],
        "total_daily_cost_km": round(total_cost, 2),
        "assignments": assignments,
        "model": model,
    }


def get_baseline_assignment(carriers, zones, dist):
    """Simula l'assegnamento AS-IS: ogni vettore serve solo il proprio distretto."""
    assignments = []
    for c in carriers:
        # Trova la zona del distretto base
        base_dist = c["base_district"]
        matching_zones = [z for z in zones if ZONE_DISTRICT[z] == base_dist]
        for z in matching_zones:
            for v, n in [("ambulance", c["n_ambulance"]), ("attrezzato", c["n_attrezzato"])]:
                if n > 0:
                    assignments.append({
                        "carrier_id": c["id"],
                        "carrier_name": c["name"],
                        "federation": c["federation"],
                        "zone": z,
                        "zone_name": ZONE_NAMES[z],
                        "vehicle_type": v,
                        "n_vehicles": n,
                        "avg_km": dist.get((c["id"], z), 25),
                        "cost_per_km": c["cost_per_km"],
                    })
    return assignments


if __name__ == "__main__":
    result = solve_strategic()
    if result:
        print(f"\nStato: {result['status']}")
        print(f"Costo giornaliero atteso (km * costo/affidabilità): {result['total_daily_cost_km']:.2f}")
        print(f"\nAssegnamenti ({len(result['assignments'])}):")
        df = pd.DataFrame(result["assignments"])
        print(df.to_string(index=False))
