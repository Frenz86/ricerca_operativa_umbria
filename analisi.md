# Piano: Creare CLAUDE.md per il progetto Trasporti AUSL Umbria 1

## Azione
Creare il file `CLAUDE.md` nella root del progetto con tutta la documentazione di contesto necessaria per lavorare al sistema di LP.

Il contenuto del CLAUDE.md è definito qui sotto. Una volta approvato, verrà scritto come file nella directory del progetto.

---

# Piano: Sistema di Linear Programming per Trasporti Sanitari AUSL Umbria 1

## Contesto

AUSL Umbria 1 gestisce trasporti sanitari secondari (dimissioni, trasferimenti, consulenze, dialisi) su un territorio di 4.298 km² con 38 comuni e 6 distretti. I dati 2025 mostrano:
- **Trasporti ospedalieri**: 8.052 viaggi, 487.991 km (3 presidi)
- **Trasporti distrettuali**: 8.924 viaggi, 688.235 km (6 distretti)
- **Dializzati barellati**: 362.987 km, 7.007 sedute
- **Totale**: ~1,635 milioni km/anno

Il problema: gestione frammentata tra 24+ associazioni di volontariato con convenzioni disomogenee, il 15% dei trasporti usa vettori fuori territorio (costi extra), il 2% delle richieste non viene evaso.

**Obiettivo**: costruire un sistema LP a 3 livelli per ottimizzare l'assegnazione dei trasporti, dalla fase strategica (allocazione territorio) a quella operativa (dispatch in tempo reale).

---

## Architettura del Sistema LP a 3 Livelli

Non esiste UN singolo modello LP per questo problema. Serve una decomposizione gerarchica:

| Livello | Orizzonte | Tipo Modello | Scopo |
|---------|-----------|-------------|-------|
| **Strategico** | Trimestrale | Transportation Problem (MIP) | Allocare vettori alle zone territoriali |
| **Tattico** | Giornaliero (notte prima) | Assignment Problem (MIP) | Assegnare i trasporti pianificati del giorno seguente |
| **Operativo** | Tempo reale | Euristica greedy + VRP locale | Gestire richieste urgenti/impreviste |

---

## Livello 1: Modello Strategico - Allocazione Territorio (Trimestrale)

### Scopo
Assegnare ogni vettore a una o più zone di servizio per garantire copertura e minimizzare i km attesi.

### Insiemi
- **Z** = 9 zone di servizio (6 distretti + 3 aree ospedaliere)
- **C** = 24+ vettori (associazioni CRI, Misericordie, ANPAS)
- **V** = tipologie veicolo (ambulanza, mezzo attrezzato)

### Variabili Decisionali
```
x[c][z][v] = intero, numero veicoli tipo v che vettore c impegna nella zona z
y[c][z]    = binario, 1 se vettore c serve la zona z
```

### Funzione Obiettivo
```
Minimizzare: SOMMA(c,z,v) di dist[c][z] * costo[c] * x[c][z][v] * 2
```
Il fattore 2 tiene conto dell'andata/ritorno.

### Vincoli
1. **Copertura domanda**: ogni zona deve avere veicoli sufficienti
   `SOMMA(c) x[c][z][v] >= domanda[z][v]` per ogni z, v
2. **Capacità vettore**: nessun vettore supera la propria flotta
   `SOMMA(z) x[c][z][v] <= capacita[c][v]` per ogni c, v
3. **Linking**: si assegnano veicoli solo dove il vettore è attivo
   `x[c][z][v] <= M * y[c][z]` (big-M)
4. **Limite zone**: ogni vettore può coprire al massimo N zone
   `SOMMA(z) y[c][z] <= max_zone[c]`
5. **Prossimità**: vettori troppo lontani non possono servire la zona
   `y[c][z] = 0 se dist[c][z] > raggio_max`
6. **Ridondanza**: almeno 2 vettori per zona
   `SOMMA(c) y[c][z] >= 2`
7. **Bilanciamento federazioni**: evitare monopolio di una federazione per zona

### Dimensioni: ~432 variabili intere + 216 binarie → risolvibile in <1 secondo con CBC (gratuito)

---

## Livello 2: Modello Tattico - Assegnamento Giornaliero (notte prima)

### Scopo
Dati i trasporti pianificati del giorno seguente (~50-70 richieste), assegnare ogni richiesta a un vettore specifico minimizzando i km totali, rispettando le finestre temporali.

### Variabili Decisionali
```
a[r][c] = binario, 1 se richiesta r è assegnata al vettore c
s[r]    = continuo, orario programmato di inizio per richiesta r
```

### Funzione Obiettivo
```
Minimizzare: SOMMA(r,c) km[r][c] * a[r][c]
             + 1000 * SOMMA(r) slack[r]   (penalità per richieste non assegnate)
```

### Vincoli chiave
- Ogni richiesta assegnata a un solo vettore (o flagged come non assegnata)
- Compatibilità tipo veicolo
- Limite viaggi giornalieri per vettore
- Finestre temporali rispettate
- Sequenziamento: se due richieste sono sullo stesso vettore, devono essere ordinate nel tempo (vincoli disgiuntivi)

### Trattamento dialisi: pre-assegnamento fisso
I pazienti dializzati percorrono la stessa rotta 3 volte/settimana → assegnamento fisso al vettore più vicino. Non vengono ri-ottimizzati ogni giorno.

### Dimensioni: ~1.560 binarie + ~2.000 sequenziamento → risolvibile in 10-60 secondi

---

## Livello 3: Modello Operativo - Dispatch Real-Time

### Approccio: NON un LP completo, ma un'euristica greedy

Quando arriva una richiesta urgente:
1. Filtrare i vettori disponibili (in servizio, tipo veicolo corretto, entro raggio)
2. Per ogni vettore idoneo: stimare tempo di arrivo e impatto sui trasporti già assegnati
3. Assegnare al vettore con score migliore: `score = -km + 0.3*affidabilita - 0.5*ritardo_creato`
4. Ri-ottimizzare localmente la sequenza del vettore (TSP su 5-8 fermate)

---

## Sotto-Problema Dialisi (Quick Win)

La dialisi è il problema più strutturato e dove l'ottimizzazione dà più risparmi:
- 7.007 sedute/anno, 362.987 km
- ~45 pazienti con rotte ricorrenti (es. lun-mer-ven o mar-gio)
- Problema = Periodic VRP (Vehicle Routing Problem periodico)

**Risparmio stimato**: consolidando pazienti vicini sullo stesso veicolo → -15/20% km = **54.000-72.000 km/anno risparmiati**

---

## Dati Necessari (Gap Analysis)

### Dati già disponibili (dall'Excel):
- Viaggi e km totali per presidio/distretto (aggregati annuali)
- Numero sedute dialisi per distretto

### Dati DA RACCGLIERE (critici per l'LP):
1. **Registro Nodi**: ogni ospedale, comune, base vettore, centro dialisi con coordinate GPS (~70 nodi)
2. **Matrice Distanze**: km e tempi di percorrenza stradale tra ogni coppia di nodi (usare OpenRouteService - gratuito)
3. **Registro Vettori**: per ognuno dei 24+ vettori → sede, numero e tipo veicoli, orari operativi, costo/km contrattuale
4. **Storico Richieste**: ogni singola richiesta di trasporto con origine, destinazione, data, vettore assegnato, km effettivi
5. **Struttura Contratti**: tariffa/km per ogni vettore (attualmente 24 contratti diversi)

---

## Stack Tecnologico Proposto

| Componente | Strumento | Motivo |
|-----------|-----------|--------|
| Solver LP/MIP | **PuLP + CBC** (Python, gratuito) | Nessun costo di licenza, dimensioni problema adeguate |
| Matrice distanze | **OpenRouteService API** (gratuito) | Distanze stradali reali in Umbria |
| Database | **PostgreSQL + PostGIS** | Query geografiche, standard sanità |
| Integrazione | **Import CSV dal gestionale SAT** | Il software esistente esporta probabilmente CSV |
| Dashboard KPI | **Streamlit** o **Grafana** | Visualizzazione assegnamenti e metriche |
| Linguaggio | **Python** | Ecosistema ricco per LP, facile da integrare |

---

## Fasi di Implementazione

### Fase 0 (Mesi 1-2): Raccoglimento Dati
- Iniziare a tracciare ogni richiesta di trasporto con: data, origine, destinazione, vettore, km effettivi
- Inventario di tutti i 24 vettori (veicoli, orari, basi)
- Calcolare la matrice delle distanze con OSRM/ORS
- **Nessuna ottimizzazione in questa fase**, solo raccolta dati

### Fase 1 (Mesi 3-4): Modello Strategico
- Risolvere l'allocazione territoriale trimestrale
- Riduce subito il problema del 15% fuori territorio assegnando formalmente vettori alle zone
- Impatto atteso: -60/70% dei viaggi fuori territorio

### Fase 2 (Mesi 5-7): Modello Tattico
- Implementare il solver giornaliero una volta raccolti 2-3 mesi di dati a livello di singola richiesta
- Partire dalle rotte dialisi (maggiore impatto, più strutturato)
- Poi estendere a tutti i trasporti pianificati
- Impatto atteso: -10/15% km per trasporti pianificati

### Fase 3 (Mesi 8-10): Dispatch Operativo
- Costruire il modulo di dispatch real-time
- Integrare con la CUT (Centrale Unica Trasporti)
- Impatto atteso: richieste non evase dal 2% a <0.5%

### Fase 4 (Mesi 11-12): Armonizzazione Contratti
- Usare i dati dell'assegnamento per negoziare contratti standardizzati
- Sostituire 24 contratti eterogenei con una tariffa unificata
- Usare i prezzi ombra dell'LP per capire il costo marginale di ogni trasporto

---

## Impatto Quantificato

| Metrica | Attuale | Dopo Ottimizzazione | Risparmio |
|---------|---------|---------------------|-----------|
| km annui totali | ~1.539.000 | ~1.307.000 | ~232.000 km (15%) |
| Viaggi fuori territorio | 2.546/anno (15%) | <500/anno (3%) | 2.000+ viaggi |
| Richieste non evase | 340/anno (2%) | <85/anno (0.5%) | 255+ pazienti |
| km dialisi | 362.987 | ~300.000 | ~63.000 km (17%) |
| Tipi contratto | 24 diversi | 3 (uno per federazione) | Semplificazione amministrativa |
| **Risparmio economico stimato** | | | **230.000-350.000 euro/anno** |

---

## Struttura Cartella Progetto

```
ricerca_operativa/
├── data/
│   ├── nodes.csv              # Registro nodi (ospedali, comuni, basi vettori)
│   ├── distance_matrix.csv    # Matrice distanze stradali
│   ├── carriers.csv           # Registro vettori
│   └── requests/              # Storico richieste giornaliere
├── models/
│   ├── strategic_allocation.py    # Modello Livello 1
│   ├── tactical_assignment.py     # Modello Livello 2
│   ├── operational_dispatch.py    # Modello Livello 3 (euristica)
│   └── dialysis_routing.py        # Sotto-problema dialisi
├── utils/
│   ├── distance_engine.py     # Calcolo matrice distanze via OSRM
│   ├── data_loader.py         # Import da Excel/SAT
│   └── geo_utils.py           # Utility geografiche
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_strategic_model.ipynb
│   └── 03_tactical_model.ipynb
└── dashboard/
    └── app.py                 # Dashboard Streamlit per KPI
```

---

## Considerazioni Pratiche Importanti

1. **Volontariato ≠ risorse controllabili**: Il modello propone, il vettore conferma. Includere un buffer del 10% nei vincoli di capacità per no-show.

2. **Affidabilità > costo**: Aggiungere un peso di affidabilità nella funzione obiettivo:
   `costo_modificato[c] = costo[c] / score_affidabilita[c]`

3. **Territorio montano**: Il Distretto Trasimeno ha ~89 km/viaggio e Media Valle ~108 km/viaggio. Non sono "inefficienze" ma realtà geografiche. Il modello non deve penalizzare i vettori che servono queste aree.

4. **Dialisi = quick win**: Iniziare da lì. Stessi 45 pazienti, stesse rotte ogni settimana. Consolidare 2 pazienti vicini su un veicolo dimezza i km di quella rotta.

---

## File Critici da Modificare/Crerare

- **[Riepilogo Trasp sanitari 2025.xlsx](Riepilogo%20Trasp%20sanitari%202025.xlsx)** → da parsare per popolare i dati iniziali del modello
- **[Gestione Trasporti.docx](Gestione%20Trasporti.docx)** → riferimento istituzionale per vincoli e contesto organizzativo
- **Nuovi file Python** in `ricerca_operativa/` → implementazione dei 3 modelli LP

## Verifica

1. Eseguire il modello strategico con dati sintetici basati sull'Excel → verificare che produce assegnamenti sensati (vettori vicini alle zone)
2. Validare la matrice delle distanze confrontando con Google Maps per 10 tratte campione
3. Simulare una giornata tipo con 65 richieste e verificare che il solver tattico trova una soluzione in <60 secondi
4. Confrontare i km ottimizzati con i km effettivi storici per stimare il risparmio reale
