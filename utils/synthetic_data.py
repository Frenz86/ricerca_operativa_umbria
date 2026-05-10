"""Dati sintetici per il sistema di trasporti sanitari AUSL Umbria 1.
Basati sui dati reali del file Excel 'Riepilogo Trasp sanitari 2025.xlsx'.
"""
import numpy as np
import pandas as pd
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
np.random.seed(42)

# --- Coordinate reali approssimative dei nodi principali ---

HOSPITALS = {
    "H-CC": {"name": "Ospedale Città di Castello", "lat": 43.4675, "lon": 12.2388, "district": "Alto Tevere"},
    "H-UMB": {"name": "Ospedale Umbertide", "lat": 43.3042, "lon": 12.3381, "district": "Alto Tevere"},
    "H-GUB": {"name": "Ospedale Gubbio", "lat": 43.3519, "lon": 12.5754, "district": "Alto Chiascio"},
    "H-GT": {"name": "Ospedale Gualdo Tadino", "lat": 43.2324, "lon": 12.7822, "district": "Alto Chiascio"},
    "H-POU": {"name": "POU - Assisi/Santa Maria degli Angeli", "lat": 43.0610, "lon": 12.5533, "district": "Assisano"},
    "H-MVT": {"name": "Ospedale Media Valle del Tevere", "lat": 42.9700, "lon": 12.3700, "district": "Media Valle"},
    "H-CL": {"name": "Ospedale Castiglione del Lago", "lat": 43.0333, "lon": 12.0167, "district": "Trasimeno"},
}

DIALYSIS_CENTERS = {
    "D-CC": {"name": "Centro Dialisi Città di Castello", "lat": 43.4675, "lon": 12.2400, "district": "Alto Tevere"},
    "D-PG": {"name": "Centro Dialisi Perugia", "lat": 43.1107, "lon": 12.3908, "district": "Perugino"},
    "D-GUB": {"name": "Centro Dialisi Gubbio", "lat": 43.3550, "lon": 12.5800, "district": "Alto Chiascio"},
}

MUNICIPALITIES = {
    # Distretto Alto Tevere
    "M-CT": {"name": "Città di Castello", "lat": 43.4675, "lon": 12.2388, "district": "Alto Tevere", "pop": 38000},
    "M-UMB": {"name": "Umbertide", "lat": 43.3042, "lon": 12.3381, "district": "Alto Tevere", "pop": 16000},
    "M-SP": {"name": "Sansepolcro", "lat": 43.5755, "lon": 12.1378, "district": "Alto Tevere", "pop": 15000},
    "M-CP": {"name": "Città di Castello periferia", "lat": 43.4300, "lon": 12.2000, "district": "Alto Tevere", "pop": 8000},
    "M-MT": {"name": "Montone", "lat": 43.3267, "lon": 12.3333, "district": "Alto Tevere", "pop": 1500},
    # Distretto Alto Chiascio
    "M-GUB": {"name": "Gubbio", "lat": 43.3519, "lon": 12.5754, "district": "Alto Chiascio", "pop": 32000},
    "M-GT": {"name": "Gualdo Tadino", "lat": 43.2324, "lon": 12.7822, "district": "Alto Chiascio", "pop": 15000},
    "M-SF": {"name": "Scheggia e Pascelupo", "lat": 43.4933, "lon": 12.6286, "district": "Alto Chiascio", "pop": 1400},
    "M-CST": {"name": "Costacciaro", "lat": 43.4017, "lon": 12.6900, "district": "Alto Chiascio", "pop": 1200},
    "M-SAS": {"name": "Sigillo", "lat": 43.3333, "lon": 12.7500, "district": "Alto Chiascio", "pop": 2400},
    # Distretto Perugino
    "M-PG": {"name": "Perugia", "lat": 43.1107, "lon": 12.3908, "district": "Perugino", "pop": 165000},
    "M-COR": {"name": "Corciano", "lat": 43.1167, "lon": 12.3000, "district": "Perugino", "pop": 21000},
    "M-MAG": {"name": "Maggio Perugino", "lat": 43.0500, "lon": 12.3500, "district": "Perugino", "pop": 14000},
    "M-DER": {"name": "Deruta", "lat": 42.9917, "lon": 12.4200, "district": "Perugino", "pop": 9000},
    # Distretto Trasimeno
    "M-CL": {"name": "Castiglione del Lago", "lat": 43.0333, "lon": 12.0167, "district": "Trasimeno", "pop": 15000},
    "M-PA": {"name": "Panicale", "lat": 43.0500, "lon": 12.1167, "district": "Trasimeno", "pop": 5500},
    "M-CT2": {"name": "Città della Pieve", "lat": 42.9333, "lon": 11.9833, "district": "Trasimeno", "pop": 7600},
    "M-TO": {"name": "Tuoro sul Trasimeno", "lat": 43.1500, "lon": 12.1000, "district": "Trasimeno", "pop": 3600},
    "M-PS": {"name": "Passignano sul Trasimeno", "lat": 43.1833, "lon": 12.1500, "district": "Trasimeno", "pop": 5800},
    "M-CH": {"name": "Chiusi (confine)", "lat": 43.0167, "lon": 11.9500, "district": "Trasimeno", "pop": 8500},
    # Distretto Assisano
    "M-ASS": {"name": "Assisi", "lat": 43.0706, "lon": 12.6206, "district": "Assisano", "pop": 28000},
    "M-SMA": {"name": "Santa Maria degli Angeli", "lat": 43.0610, "lon": 12.5533, "district": "Assisano", "pop": 12000},
    "M-VAL": {"name": "Valfabbrica", "lat": 43.0000, "lon": 12.6167, "district": "Assisano", "pop": 3200},
    "M-SPC": {"name": "Spello", "lat": 43.0000, "lon": 12.6667, "district": "Assisano", "pop": 8600},
    "M-NOC": {"name": "Nocera Umbra", "lat": 43.1000, "lon": 12.8000, "district": "Assisano", "pop": 5800},
    # Distretto Media Valle
    "M-MVT": {"name": "Todi", "lat": 42.7833, "lon": 12.4167, "district": "Media Valle", "pop": 17000},
    "M-MA": {"name": "Marsciano", "lat": 42.9167, "lon": 12.3333, "district": "Media Valle", "pop": 18000},
    "M-DO": {"name": "Deruta (Media Valle)", "lat": 42.9917, "lon": 12.4200, "district": "Media Valle", "pop": 9500},
    "M-CA": {"name": "Collazzone", "lat": 42.8500, "lon": 12.5500, "district": "Media Valle", "pop": 3200},
    "M-FR": {"name": "Fratta Todina", "lat": 42.8000, "lon": 12.3500, "district": "Media Valle", "pop": 1900},
    "M-AC": {"name": "Acquasparta", "lat": 42.6833, "lon": 12.5500, "district": "Media Valle", "pop": 5000},
    "M-MN": {"name": "Massa Martana", "lat": 42.7667, "lon": 12.5333, "district": "Media Valle", "pop": 3800},
}

# Genera coordinate per comuni minori mancanti
EXTRA_MUNICIPALITIES = {
    "M-LF": {"name": "Lisciano Niccone", "lat": 43.2167, "lon": 12.1500, "district": "Alto Tevere", "pop": 700},
    "M-PG2": {"name": "Perugia periferia est", "lat": 43.1300, "lon": 12.4500, "district": "Perugino", "pop": 25000},
    "M-BV": {"name": "Bettona", "lat": 43.0333, "lon": 12.4833, "district": "Assisano", "pop": 4600},
    "M-BA": {"name": "Bastia Umbra", "lat": 43.0667, "lon": 12.5500, "district": "Assisano", "pop": 22000},
    "M-PG3": {"name": "Pontificalone/PG ovest", "lat": 43.0833, "lon": 12.3000, "district": "Perugino", "pop": 18000},
}


def build_nodes():
    all_nodes = {}
    for k, v in HOSPITALS.items():
        all_nodes[k] = {**v, "type": "hospital"}
    for k, v in DIALYSIS_CENTERS.items():
        all_nodes[k] = {**v, "type": "dialysis_center"}
    for k, v in {**MUNICIPALITIES, **EXTRA_MUNICIPALITIES}.items():
        all_nodes[k] = {**v, "type": "municipality"}
    return all_nodes


DISTRICTS = ["Alto Tevere", "Alto Chiascio", "Perugino", "Trasimeno", "Assisano", "Media Valle"]

DISTRICT_CENTERS = {
    "Alto Tevere": (43.40, 12.27),
    "Alto Chiascio": (43.30, 12.68),
    "Perugino": (43.08, 12.37),
    "Trasimeno": (43.05, 12.05),
    "Assisano": (43.04, 12.60),
    "Media Valle": (42.85, 12.43),
}

# Zone per il modello strategico (6 distretti + 3 aree ospedaliere)
ZONES = [
    "Z-AT", "Z-AC", "Z-PG", "Z-TR", "Z-AS", "Z-MV",
    "Z-H-CC", "Z-H-GUB", "Z-H-POU",
]

ZONE_NAMES = {
    "Z-AT": "Distretto Alto Tevere",
    "Z-AC": "Distretto Alto Chiascio",
    "Z-PG": "Distretto Perugino",
    "Z-TR": "Distretto Trasimeno",
    "Z-AS": "Distretto Assisano",
    "Z-MV": "Distretto Media Valle",
    "Z-H-CC": "Area Ospedaliera Città di Castello/Umbertide",
    "Z-H-GUB": "Area Ospedaliera Gubbio/Gualdo Tadino",
    "Z-H-POU": "Area Ospedaliera POU",
}

ZONE_DISTRICT = {
    "Z-AT": "Alto Tevere", "Z-AC": "Alto Chiascio", "Z-PG": "Perugino",
    "Z-TR": "Trasimeno", "Z-AS": "Assisano", "Z-MV": "Media Valle",
    "Z-H-CC": "Alto Tevere", "Z-H-GUB": "Alto Chiascio", "Z-H-POU": "Assisano",
}

# Vettori (24 associazioni, dati sintetici ma realistici)
def build_carriers():
    carriers = [
        # CRI
        {"id": "CRI-01", "name": "CRI Città di Castello", "federation": "CRI",
         "base_lat": 43.4600, "base_lon": 12.2400, "base_district": "Alto Tevere",
         "n_ambulance": 2, "n_attrezzato": 3, "max_daily_trips": 12, "cost_per_km": 1.20, "reliability": 0.95},
        {"id": "CRI-02", "name": "CRI Umbertide", "federation": "CRI",
         "base_lat": 43.3000, "base_lon": 12.3400, "base_district": "Alto Tevere",
         "n_ambulance": 1, "n_attrezzato": 2, "max_daily_trips": 8, "cost_per_km": 1.25, "reliability": 0.92},
        {"id": "CRI-03", "name": "CRI Gubbio", "federation": "CRI",
         "base_lat": 43.3500, "base_lon": 12.5700, "base_district": "Alto Chiascio",
         "n_ambulance": 2, "n_attrezzato": 2, "max_daily_trips": 10, "cost_per_km": 1.20, "reliability": 0.94},
        {"id": "CRI-04", "name": "CRI Perugia", "federation": "CRI",
         "base_lat": 43.1000, "base_lon": 12.3900, "base_district": "Perugino",
         "n_ambulance": 3, "n_attrezzato": 4, "max_daily_trips": 18, "cost_per_km": 1.15, "reliability": 0.96},
        {"id": "CRI-05", "name": "CRI Assisi", "federation": "CRI",
         "base_lat": 43.0700, "base_lon": 12.6200, "base_district": "Assisano",
         "n_ambulance": 1, "n_attrezzato": 2, "max_daily_trips": 8, "cost_per_km": 1.25, "reliability": 0.91},
        {"id": "CRI-06", "name": "CRI Todi", "federation": "CRI",
         "base_lat": 42.7800, "base_lon": 12.4100, "base_district": "Media Valle",
         "n_ambulance": 1, "n_attrezzato": 2, "max_daily_trips": 8, "cost_per_km": 1.30, "reliability": 0.90},
        {"id": "CRI-07", "name": "CRI Castiglione del Lago", "federation": "CRI",
         "base_lat": 43.0300, "base_lon": 12.0200, "base_district": "Trasimeno",
         "n_ambulance": 1, "n_attrezzato": 1, "max_daily_trips": 6, "cost_per_km": 1.35, "reliability": 0.88},
        # Misericordie
        {"id": "MIS-01", "name": "Misericordia Città di Castello", "federation": "Misericordie",
         "base_lat": 43.4700, "base_lon": 12.2300, "base_district": "Alto Tevere",
         "n_ambulance": 2, "n_attrezzato": 3, "max_daily_trips": 12, "cost_per_km": 1.10, "reliability": 0.93},
        {"id": "MIS-02", "name": "Misericordia Gubbio", "federation": "Misericordie",
         "base_lat": 43.3600, "base_lon": 12.5800, "base_district": "Alto Chiascio",
         "n_ambulance": 1, "n_attrezzato": 2, "max_daily_trips": 8, "cost_per_km": 1.15, "reliability": 0.91},
        {"id": "MIS-03", "name": "Misericordia Gualdo Tadino", "federation": "Misericordie",
         "base_lat": 43.2300, "base_lon": 12.7800, "base_district": "Alto Chiascio",
         "n_ambulance": 1, "n_attrezzato": 2, "max_daily_trips": 7, "cost_per_km": 1.20, "reliability": 0.89},
        {"id": "MIS-04", "name": "Misericordia Perugia", "federation": "Misericordie",
         "base_lat": 43.1100, "base_lon": 12.4000, "base_district": "Perugino",
         "n_ambulance": 2, "n_attrezzato": 3, "max_daily_trips": 14, "cost_per_km": 1.10, "reliability": 0.95},
        {"id": "MIS-05", "name": "Misericordia Assisi", "federation": "Misericordie",
         "base_lat": 43.0800, "base_lon": 12.6100, "base_district": "Assisano",
         "n_ambulance": 1, "n_attrezzato": 2, "max_daily_trips": 8, "cost_per_km": 1.20, "reliability": 0.92},
        {"id": "MIS-06", "name": "Misericordia Todi", "federation": "Misericordie",
         "base_lat": 42.7900, "base_lon": 12.4200, "base_district": "Media Valle",
         "n_ambulance": 1, "n_attrezzato": 2, "max_daily_trips": 8, "cost_per_km": 1.25, "reliability": 0.90},
        {"id": "MIS-07", "name": "Misericordia Bastia Umbra", "federation": "Misericordie",
         "base_lat": 43.0700, "base_lon": 12.5500, "base_district": "Assisano",
         "n_ambulance": 1, "n_attrezzato": 2, "max_daily_trips": 7, "cost_per_km": 1.20, "reliability": 0.91},
        {"id": "MIS-08", "name": "Misericordia Marsciano", "federation": "Misericordie",
         "base_lat": 42.9200, "base_lon": 12.3300, "base_district": "Media Valle",
         "n_ambulance": 1, "n_attrezzato": 1, "max_daily_trips": 6, "cost_per_km": 1.25, "reliability": 0.88},
        {"id": "MIS-09", "name": "Misericordia Panicale", "federation": "Misericordie",
         "base_lat": 43.0500, "base_lon": 12.1100, "base_district": "Trasimeno",
         "n_ambulance": 1, "n_attrezzato": 1, "max_daily_trips": 5, "cost_per_km": 1.30, "reliability": 0.87},
        # ANPAS
        {"id": "ANP-01", "name": "ANPAS Città di Castello", "federation": "ANPAS",
         "base_lat": 43.4600, "base_lon": 12.2500, "base_district": "Alto Tevere",
         "n_ambulance": 1, "n_attrezzato": 2, "max_daily_trips": 8, "cost_per_km": 1.15, "reliability": 0.92},
        {"id": "ANP-02", "name": "ANPAS Sansepolcro", "federation": "ANPAS",
         "base_lat": 43.5800, "base_lon": 12.1400, "base_district": "Alto Tevere",
         "n_ambulance": 1, "n_attrezzato": 1, "max_daily_trips": 5, "cost_per_km": 1.30, "reliability": 0.85},
        {"id": "ANP-03", "name": "ANPAS Gubbio", "federation": "ANPAS",
         "base_lat": 43.3400, "base_lon": 12.5600, "base_district": "Alto Chiascio",
         "n_ambulance": 1, "n_attrezzato": 2, "max_daily_trips": 7, "cost_per_km": 1.20, "reliability": 0.90},
        {"id": "ANP-04", "name": "ANPAS Perugia", "federation": "ANPAS",
         "base_lat": 43.0900, "base_lon": 12.3800, "base_district": "Perugino",
         "n_ambulance": 2, "n_attrezzato": 3, "max_daily_trips": 14, "cost_per_km": 1.10, "reliability": 0.94},
        {"id": "ANP-05", "name": "ANPAS Spello", "federation": "ANPAS",
         "base_lat": 43.0000, "base_lon": 12.6700, "base_district": "Assisano",
         "n_ambulance": 1, "n_attrezzato": 1, "max_daily_trips": 5, "cost_per_km": 1.30, "reliability": 0.86},
        {"id": "ANP-06", "name": "ANPAS Todi", "federation": "ANPAS",
         "base_lat": 42.7700, "base_lon": 12.4000, "base_district": "Media Valle",
         "n_ambulance": 1, "n_attrezzato": 1, "max_daily_trips": 5, "cost_per_km": 1.30, "reliability": 0.87},
        {"id": "ANP-07", "name": "ANPAS Castiglione del Lago", "federation": "ANPAS",
         "base_lat": 43.0400, "base_lon": 12.0100, "base_district": "Trasimeno",
         "n_ambulance": 1, "n_attrezzato": 1, "max_daily_trips": 5, "cost_per_km": 1.35, "reliability": 0.85},
        {"id": "ANP-08", "name": "ANPAS Città della Pieve", "federation": "ANPAS",
         "base_lat": 42.9400, "base_lon": 11.9900, "base_district": "Trasimeno",
         "n_ambulance": 1, "n_attrezzato": 1, "max_daily_trips": 4, "cost_per_km": 1.40, "reliability": 0.83},
        {"id": "ANP-09", "name": "ANPAS Deruta", "federation": "ANPAS",
         "base_lat": 42.9900, "base_lon": 12.4300, "base_district": "Perugino",
         "n_ambulance": 1, "n_attrezzato": 1, "max_daily_trips": 5, "cost_per_km": 1.25, "reliability": 0.88},
    ]
    return carriers


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return R * 2 * np.arcsin(np.sqrt(a))


def road_distance_factor():
    return np.random.uniform(1.25, 1.45)


def build_distance_matrix(nodes):
    ids = sorted(nodes.keys())
    n = len(ids)
    dist_km = np.zeros((n, n))
    time_min = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            h = haversine_km(nodes[ids[i]]["lat"], nodes[ids[i]]["lon"],
                             nodes[ids[j]]["lat"], nodes[ids[j]]["lon"])
            road_factor = road_distance_factor()
            dist_km[i][j] = round(h * road_factor, 1)
            time_min[i][j] = round(dist_km[i][j] / 0.6, 0)  # ~36 km/h media
    return ids, dist_km, time_min


def build_zone_demand():
    # Domanda giornaliera stimata per zona e tipo veicolo
    # Basata sui dati annuali divisi per ~260 giorni lavorativi
    return {
        # zona: (ambulance, attrezzato)
        "Z-AT": (4, 3),      # Alto Tevere: 1627/260 ~ 6.3/gg
        "Z-AC": (3, 3),      # Alto Chiascio: 1464/260 ~ 5.6/gg
        "Z-PG": (5, 4),      # Perugino: 2134/260 ~ 8.2/gg
        "Z-TR": (3, 4),      # Trasimeno: 1648/260 ~ 6.3/gg
        "Z-AS": (2, 2),      # Assisano: 795/260 ~ 3.1/gg
        "Z-MV": (3, 3),      # Media Valle: 1256/260 ~ 4.8/gg
        "Z-H-CC": (5, 4),    # PO CC+Umbertide: 3444/260 ~ 13.2/gg (suddiviso tra amb+attr)
        "Z-H-GUB": (4, 3),   # PO Gubbio+GT: 2348/260 ~ 9.0/gg
        "Z-H-POU": (3, 3),   # POU: 2260/260 ~ 8.7/gg
    }


def generate_daily_requests(n_planned=55, n_urgent=12):
    """Genera richieste di trasporto per una giornata tipo."""
    nodes = build_nodes()
    municipalities = [k for k, v in nodes.items() if v["type"] == "municipality"]
    hospitals = [k for k, v in nodes.items() if v["type"] == "hospital"]

    requests = []
    for i in range(n_planned):
        origin_type = np.random.choice(["municipality", "hospital"], p=[0.6, 0.4])
        if origin_type == "municipality":
            origin = np.random.choice(municipalities)
        else:
            origin = np.random.choice(hospitals)

        dest_type = np.random.choice(["hospital", "municipality", "dialysis_center"], p=[0.5, 0.3, 0.2])
        if dest_type == "hospital":
            dest = np.random.choice(hospitals)
        elif dest_type == "dialysis_center":
            dest = np.random.choice(list(DIALYSIS_CENTERS.keys()))
        else:
            dest = np.random.choice(municipalities)
            while dest == origin:
                dest = np.random.choice(municipalities)

        hour = np.random.choice(range(7, 20), p=[
            0.08, 0.10, 0.12, 0.12, 0.10, 0.10, 0.08, 0.08, 0.06, 0.05, 0.04, 0.03, 0.04
        ])
        service = np.random.choice(["ambulance", "attrezzato"], p=[0.35, 0.65])
        req_type = np.random.choice(["dimissione", "trasferimento", "consulenza"], p=[0.4, 0.3, 0.3])

        requests.append({
            "id": f"R-{i+1:04d}",
            "type": req_type,
            "service": service,
            "origin": origin,
            "destination": dest,
            "district": nodes[origin]["district"],
            "time_window_start": f"{hour:02d}:00",
            "time_window_end": f"{min(hour + 3, 21):02d}:00",
            "priority": 2,
            "is_recurring": False,
        })

    for i in range(n_urgent):
        origin = np.random.choice(municipalities)
        dest = np.random.choice(hospitals)
        hour = np.random.choice(range(7, 21))
        service = np.random.choice(["ambulance", "attrezzato"], p=[0.5, 0.5])

        requests.append({
            "id": f"U-{i+1:04d}",
            "type": "urgente",
            "service": service,
            "origin": origin,
            "destination": dest,
            "district": nodes[origin]["district"],
            "time_window_start": f"{hour:02d}:00",
            "time_window_end": f"{min(hour + 1, 21):02d}:00",
            "priority": 1,
            "is_recurring": False,
        })

    return requests


def generate_dialysis_patients(n=45):
    nodes = build_nodes()
    municipalities = [k for k, v in nodes.items() if v["type"] == "municipality"]
    dialysis_centers = list(DIALYSIS_CENTERS.keys())
    patterns = ["MWF", "TTh", "MWF", "TTh", "MWF"]

    patients = []
    # Distribuzione realistica: più pazienti nei distretti più popolosi
    weights_by_district = {
        "Perugino": 15, "Alto Tevere": 8, "Alto Chiascio": 8,
        "Assisano": 5, "Media Valle": 5, "Trasimeno": 4,
    }

    origins = []
    for dist, count in weights_by_district.items():
        dist_mun = [m for m in municipalities if nodes[m]["district"] == dist]
        for _ in range(count):
            origins.append(np.random.choice(dist_mun))

    for i, origin in enumerate(origins):
        # Assegna al centro dialisi più vicino
        best_center = min(dialysis_centers,
                          key=lambda dc: haversine_km(nodes[origin]["lat"], nodes[origin]["lon"],
                                                      nodes[dc]["lat"], nodes[dc]["lon"]))
        patients.append({
            "id": f"DIAL-{i+1:03d}",
            "origin": origin,
            "destination": best_center,
            "district": nodes[origin]["district"],
            "pattern": patterns[i % len(patterns)],
            "sessions_per_week": 3 if patterns[i % len(patterns)] == "MWF" else 2,
            "shift": np.random.choice(["AM", "PM"]),
            "service": "ambulance",
        })

    return patients


def save_all_data():
    os.makedirs(DATA_DIR, exist_ok=True)

    nodes = build_nodes()
    ids, dist_km, time_min = build_distance_matrix(nodes)

    nodes_df = pd.DataFrame([
        {"id": k, "name": v["name"], "type": v["type"],
         "lat": v["lat"], "lon": v["lon"], "district": v["district"],
         "pop": v.get("pop", 0)}
        for k, v in nodes.items()
    ])
    nodes_df.to_csv(os.path.join(DATA_DIR, "nodes.csv"), index=False)

    dist_records = []
    for i, id_i in enumerate(ids):
        for j, id_j in enumerate(ids):
            if i != j:
                dist_records.append({
                    "from": id_i, "to": id_j,
                    "km": dist_km[i][j], "minutes": time_min[i][j]
                })
    pd.DataFrame(dist_records).to_csv(os.path.join(DATA_DIR, "distance_matrix.csv"), index=False)

    carriers = build_carriers()
    pd.DataFrame(carriers).to_csv(os.path.join(DATA_DIR, "carriers.csv"), index=False)

    requests = generate_daily_requests()
    pd.DataFrame(requests).to_csv(os.path.join(DATA_DIR, "daily_requests_sample.csv"), index=False)

    patients = generate_dialysis_patients()
    pd.DataFrame(patients).to_csv(os.path.join(DATA_DIR, "dialysis_patients.csv"), index=False)

    demand = build_zone_demand()
    demand_records = [{"zone": k, "ambulance": v[0], "attrezzato": v[1]} for k, v in demand.items()]
    pd.DataFrame(demand_records).to_csv(os.path.join(DATA_DIR, "zone_demand.csv"), index=False)

    print(f"Salvati {len(nodes)} nodi, {len(dist_records)} distanze, {len(carriers)} vettori")
    print(f"Salvate {len(requests)} richieste giornaliere e {len(patients)} pazienti dialisi")
    return nodes, carriers, requests, patients


if __name__ == "__main__":
    save_all_data()
