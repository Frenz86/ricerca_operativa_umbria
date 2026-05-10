"""Sotto-Problema Dialisi: Periodic VRP per pazienti dializzati.
Ottimizza le rotte ricorrenti (2-3 volte/settimana) consolidando pazienti vicini."""
import pulp
import numpy as np
import pandas as pd
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.synthetic_data import (
    build_nodes, build_carriers, haversine_km,
    generate_dialysis_patients, DIALYSIS_CENTERS
)


def cluster_patients(patients, nodes, max_cluster_km=15, max_per_cluster=3):
    """Raggruppa pazienti vicini per potenziale condivisione del veicolo."""
    clusters = []
    assigned = set()

    for i, p1 in enumerate(patients):
        if i in assigned:
            continue
        cluster = [i]
        assigned.add(i)

        for j, p2 in enumerate(patients):
            if j in assigned:
                continue
            if p1["destination"] != p2["destination"]:
                continue
            if p1["pattern"] != p2["pattern"]:
                continue
            if p1["shift"] != p2["shift"]:
                continue

            dist = haversine_km(
                nodes[p1["origin"]]["lat"], nodes[p1["origin"]]["lon"],
                nodes[p2["origin"]]["lat"], nodes[p2["origin"]]["lon"]
            ) * 1.35

            if dist <= max_cluster_km and len(cluster) < max_per_cluster:
                cluster.append(j)
                assigned.add(j)

        clusters.append(cluster)

    return clusters


def compute_route_km(cluster_patients_list, nodes, dialysis_center):
    """Calcola i km di una rotta: base → paz1 → paz2 → ... → dialisi → base (semplificato)."""
    if not cluster_patients_list:
        return 0

    # Per semplicità: somma distanze dirette da ogni paziente al centro dialisi
    # + 20% overhead per la raccolta sequenziale
    total = 0
    for p in cluster_patients_list:
        d = haversine_km(
            nodes[p["origin"]]["lat"], nodes[p["origin"]]["lon"],
            nodes[dialysis_center]["lat"], nodes[dialysis_center]["lon"]
        ) * 1.35
        total += d * 2  # andata e ritorno

    # Sconto per condivisione: se ci sono N pazienti, risparmio (N-1)/N del tratto comune
    n = len(cluster_patients_list)
    if n > 1:
        savings_factor = 1 - (n - 1) * 0.15  # 15% risparmio per ogni paziente aggiuntivo
        savings_factor = max(savings_factor, 0.5)
        total *= savings_factor

    return round(total, 1)


def optimize_dialysis(patients=None, carriers=None):
    if patients is None:
        np.random.seed(42)
        patients = generate_dialysis_patients()
    if carriers is None:
        carriers = build_carriers()
    nodes = build_nodes()

    # Filtra vettori con ambulanze (necessarie per dialisi)
    dialysis_carriers = [c for c in carriers if c["n_ambulance"] > 0]
    carrier_ids = [c["id"] for c in dialysis_carriers]
    carrier_map = {c["id"]: c for c in dialysis_carriers}

    # Raggruppa pazienti per (centro dialisi, pattern, shift)
    groups = {}
    for i, p in enumerate(patients):
        key = (p["destination"], p["pattern"], p["shift"])
        if key not in groups:
            groups[key] = []
        groups[key].append(i)

    # Per ogni gruppo, assegna ai vettori minimizzando km
    all_assignments = []
    total_km_baseline = 0
    total_km_optimized = 0

    for key, patient_indices in groups.items():
        dialysis_center, pattern, shift = key
        group_patients = [patients[i] for i in patient_indices]

        # Clustering pazienti vicini
        clusters = cluster_patients(group_patients, nodes)

        # Per ogni cluster, trova il vettore più vicino
        for cluster in clusters:
            cluster_pats = [group_patients[i] for i in cluster]

            # Centroide del cluster
            avg_lat = np.mean([nodes[p["origin"]]["lat"] for p in cluster_pats])
            avg_lon = np.mean([nodes[p["origin"]]["lon"] for p in cluster_pats])

            # Trova vettore più vicino al centroide
            best_carrier = min(dialysis_carriers,
                               key=lambda c: haversine_km(c["base_lat"], c["base_lon"], avg_lat, avg_lon))

            # km ottimizzati (rotta consolidata)
            km_opt = compute_route_km(cluster_pats, nodes, dialysis_center)

            # km baseline (ogni paziente viaggia da solo)
            km_base = sum(
                haversine_km(nodes[p["origin"]]["lat"], nodes[p["origin"]]["lon"],
                             nodes[dialysis_center]["lat"], nodes[dialysis_center]["lon"]) * 1.35 * 2
                for p in cluster_pats
            )

            # Moltiplica per frequenza settimanale
            freq = 3 if pattern == "MWF" else 2
            km_opt_weekly = km_opt * freq
            km_base_weekly = km_base * freq

            total_km_baseline += km_base_weekly
            total_km_optimized += km_opt_weekly

            for idx in cluster:
                p = group_patients[idx]
                all_assignments.append({
                    "patient_id": p["id"],
                    "origin": p["origin"],
                    "origin_name": nodes[p["origin"]]["name"],
                    "destination": dialysis_center,
                    "dest_name": nodes[dialysis_center]["name"],
                    "district": p["district"],
                    "carrier_id": best_carrier["id"],
                    "carrier_name": best_carrier["name"],
                    "federation": best_carrier["federation"],
                    "pattern": pattern,
                    "shift": shift,
                    "km_per_session_baseline": round(haversine_km(
                        nodes[p["origin"]]["lat"], nodes[p["origin"]]["lon"],
                        nodes[dialysis_center]["lat"], nodes[dialysis_center]["lon"]
                    ) * 1.35 * 2, 1),
                    "km_per_session_optimized": round(km_opt / len(cluster_pats), 1),
                    "cluster_size": len(cluster_pats),
                    "sessions_per_week": freq,
                })

    # Annualizza (52 settimane)
    annual_baseline = total_km_baseline * 52
    annual_optimized = total_km_optimized * 52
    savings_km = annual_baseline - annual_optimized
    savings_pct = (savings_km / annual_baseline * 100) if annual_baseline > 0 else 0

    return {
        "n_patients": len(patients),
        "n_assignments": len(all_assignments),
        "annual_km_baseline": round(annual_baseline),
        "annual_km_optimized": round(annual_optimized),
        "annual_savings_km": round(savings_km),
        "savings_pct": round(savings_pct, 1),
        "weekly_km_baseline": round(total_km_baseline),
        "weekly_km_optimized": round(total_km_optimized),
        "assignments": all_assignments,
    }


if __name__ == "__main__":
    result = optimize_dialysis()
    print(f"Pazienti: {result['n_patients']}")
    print(f"km annuali baseline: {result['annual_km_baseline']:,.0f}")
    print(f"km annuali ottimizzati: {result['annual_km_optimized']:,.0f}")
    print(f"Risparmio: {result['annual_savings_km']:,.0f} km ({result['savings_pct']}%)")
    print(f"\nDettaglio assegnamenti (primi 10):")
    df = pd.DataFrame(result["assignments"]).head(10)
    print(df.to_string(index=False))
