# CLAUDE.md - Progetto Trasporti Sanitari AUSL Umbria 1

## Progetto

Sistema di ottimizzazione basato su Linear Programming per i trasporti sanitari secondari (non emergenza) dell'AUSL Umbria 1. Il progetto mira a centralizzare e ottimizzare la gestione di dimissioni, trasferimenti, consulenze e trasporti dialisi tramite un sistema a 3 livelli (strategico, tattico, operativo).

## Contesto Istituzionale

AUSL Umbria 1 opera su un territorio di 4.298 km² con 38 comuni e 6 distretti sanitari. Attualmente la gestione dei trasporti è frammentata tra 24+ associazioni di volontariato (CRI, Misericordie, ANPAS) con convenzioni disomogenee. Obiettivo: attivare la Centrale Unica Trasporti (CUT) con sede presso l'Ospedale della Media Valle del Tevere entro il primo trimestre 2027.

## Struttura del Territorio

### Presidi Ospedalieri (fonti di richieste)
| Presidio | Viaggi 2025 | km 2025 |
|----------|-------------|---------|
| PO Città di Castello e Umbertide | 3.444 | 196.123 |
| PO Gubbio-Gualdo Tadino | 2.348 | 127.991 |
| POU (Assisi/Media Valle/Castiglione del Lago) | 2.260 | 163.877 |

### Distretti Territoriali
| Distretto | Viaggi 2025 | km 2025 |
|-----------|-------------|---------|
| Alto Tevere | 1.627 | 90.237 |
| Alto Chiascio | 1.464 | 130.008 |
| del Perugino | 2.134 | 122.585 |
| Trasimeno | 1.648 | 146.641 |
| Assisano | 795 | 62.595 |
| Media Valle del Tevere | 1.256 | 136.169 |

### Dializzati Barellati
- 362.987 km / 7.007 sedute annue
- Principali distretti: Perugino (210.977 km, 4.752 sedute), Alto Chiascio (81.536 km), Alto Tevere (70.474 km)

## Volumi Complessivi

- Trasporti ordinari: 1.176.226 km (2025) vs 1.282.388 km (2024)
- Trasporti dialisi: 459.608 km (2025) vs 353.239 km (2024)
- Richieste giornaliere: ~70-80 secondarie + ~20 ospedaliere + ~3 logistiche
- 15% trasporti fuori territorio (vettore non locale)
- 2% richieste non evase per indisponibilità vettore

## Architettura del Sistema LP

Il sistema usa 3 livelli di ottimizzazione con orizzonti temporali diversi:

### Livello 1 - Strategico (Trimestrale)
- **Tipo**: Transportation Problem (MIP)
- **Scopo**: Allocare vettori alle 9 zone territoriali (6 distretti + 3 aree ospedaliere)
- **Variabili**: x[c][z][v] = veicoli tipo v assegnati dal vettore c alla zona z; y[c][z] = vettore c serve zona z
- **Obiettivo**: Minimizzare km attesi pesati per costo
- **Vincoli**: copertura domanda, capacità vettore, prossimità geografica, ridondanza (min 2 vettori/zona), bilanciamento federazioni
- **Dimensioni**: ~432 variabili intere + 216 binarie → <1 secondo con CBC

### Livello 2 - Tattico (Giornaliero, risolto la notte prima)
- **Tipo**: Assignment Problem con Time Windows (MIP)
- **Scopo**: Assegnare i ~50-70 trasporti pianificati del giorno seguente
- **Variabili**: a[r][c] = richiesta r assegnata a vettore c; s[r] = orario inizio
- **Obiettivo**: Minimizzare km totali + penalità per richieste non assegnate
- **Vincoli**: tipo veicolo, limite viaggi giornalieri, finestre temporali, sequenziamento (vincoli disgiuntivi)
- **Dimensioni**: ~1.560 binarie + ~2.000 sequenziamento → 10-60 secondi

### Livello 3 - Operativo (Real-time)
- **Tipo**: Euristica greedy + VRP locale
- **Scopo**: Dispatch richieste urgenti/impreviste
- **Algoritmo**: filtrare vettori idonei, calcolare score (-km + 0.3*affidabilita - 0.5*ritardo), assegnare al migliore

### Sotto-Problema Dialisi (Quick Win)
- Periodic VRP per ~45 pazienti con rotte ricorrenti (3x/settimana)
- Pre-assegnamento fisso, ri-ottimizzazione solo quando pazienti entrano/escono dal programma
- Risparmio stimato: -15/20% km = 54.000-72.000 km/anno

## File del Progetto

- `Gestione Trasporti.docx` - Documento istituzionale AS-IS/TO-BE, roadmap, SWOT, process flow, KPI
- `Riepilogo Trasp sanitari 2025.xlsx` - Dati aggregati trasporti per presidio/distretto
- `ricerca_operativa/` - Implementazione Python dei modelli LP (da creare)
  - `data/` - nodes.csv, distance_matrix.csv, carriers.csv, requests/
  - `models/` - strategic_allocation.py, tactical_assignment.py, operational_dispatch.py, dialysis_routing.py
  - `utils/` - distance_engine.py, data_loader.py, geo_utils.py
  - `notebooks/` - Esplorazione dati e testing modelli
  - `dashboard/` - Dashboard Streamlit per KPI

## Stack Tecnologico

| Componente | Strumento |
|-----------|-----------|
| Solver LP/MIP | PuLP + CBC (Python, gratuito) |
| Matrice distanze | OpenRouteService API (gratuito) |
| Database | PostgreSQL + PostGIS |
| Integrazione | Import CSV dal gestionale SAT |
| Dashboard | Streamlit o Grafana |
| Linguaggio | Python |

## Vincoli e Considerazioni Pratiche

- **Volontariato**: i vettori sono associazioni di volontariato, non risorse direttamente controllabili. Il modello propone, il vettore conferma. Buffer del 10% nella capacità.
- **Affidabilità > costo**: pesare la funzione obiettivo con `costo_modificato[c] = costo[c] / score_affidabilita[c]`
- **Geografia**: territorio montano con grandi distanze tra centri abitati. Il Trasimeno (~89 km/viaggio) e la Media Valle (~108 km/viaggio) non sono inefficienze ma realtà geografiche.
- **Dialisi prima**: il quick win più importante. Rotte prevedibili, pazienti ricorrenti, alto impatto sull'ottimizzazione.
- **Contratti eterogenei**: attualmente 24 convenzioni diverse. L'armonizzazione è un obiettivo di lungo periodo (Fase 4).

## Fasi di Implementazione

1. **Fase 0** (Mesi 1-2): Raccoglimento dati - tracciare ogni richiesta, inventario vettori, calcolare matrice distanze
2. **Fase 1** (Mesi 3-4): Modello strategico - allocazione territoriale, riduzione viaggi fuori territorio
3. **Fase 2** (Mesi 5-7): Modello tattico - assegnamento giornaliero, partire dalle rotte dialisi
4. **Fase 3** (Mesi 8-10): Dispatch operativo - gestione urgenti, integrazione CUT
5. **Fase 4** (Mesi 11-12): Armonizzazione contratti - tariffa unificata, prezzi ombra LP

## Impatto Stimato

- km risparmiati: ~232.000 km/anno (-15%)
- Viaggi fuori territorio: da 15% a <3%
- Richieste non evase: da 2% a <0.5%
- Risparmio economico: 230.000-350.000 euro/anno

## Processo di Trasporto (7 Fasi)

1. **Richiesta** - Medico richiedente (MMG/Specialista/Reparto) → dati anagrafici, motivazione, tipologia, origine/destinazione
2. **Autorizzazione** - CUT → codice autorizzativo, priorità, criteri normativi
3. **Assegnazione vettore** - CUT → identificativo vettore, mezzo, tempi previsti (QUI agisce il sistema LP)
4. **Presa in carico** - Vettore/Associazione → conferma disponibilità, dati mezzo
5. **Esecuzione prestazione** - Vettore + Paziente → dati viaggio, attestazione medica
6. **Chiusura evento** - Vettore + CUT → km effettivi, tempi, anomalie
7. **Rendicontazione e liquidazione** - CUT + Uffici amministrativi → dati economici, report KPI
