import io
import unicodedata
from collections import Counter
from typing import Any, Dict, List, Optional
import networkx as nx
import pandas as pd

from app.algorithme import shortest_paths as sp
from app.algorithme import traversal as tr
from app.algorithme.helper import load_networkx_graph_from_csv, parse_node_id

CRITERES = {
    "temps_normal": ("temps_normal", "min"),
    "temps_pointe": ("temps_pointe", "min"),
    "distance": ("distance_km", "km"),
}
SOURCE = "__CASERNES__"
STATUTS_OUVERTS = {"", "ouvert", "normal", "actif"}
SENSIBLES_PAR_DEFAUT = ("hopital", "ecole", "mairie", "prefecture", "pharmacie", "centre")


def _norm(text: str) -> str:
    return unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode().lower().strip()

def _sort_key(x):
    return (isinstance(x, str), x)

def _critere(name: str):
    if name not in CRITERES:
        raise ValueError(f"Critère inconnu : {name}")
    return CRITERES[name]

def _reweighted(G: nx.Graph, critere: str) -> nx.Graph:
    attr, _ = _critere(critere)
    H = G.copy()
    for _, _, d in H.edges(data=True):
        if d.get(attr) is not None:
            d["weight"] = float(d[attr])
    return H

def _edges_of(G: nx.Graph):
    edges = [(u, v, float(d.get("weight", 1.0))) for u, v, d in G.edges(data=True)]
    if not G.is_directed():
        edges += [(v, u, w) for u, v, w in edges]
    return edges

def _casernes(G: nx.Graph) -> list:
    return [n for n, d in G.nodes(data=True) if _norm(d.get("type", "")) == "caserne"]

def _parse_pairs(text: Optional[str]) -> list:
    pairs = []
    for chunk in (text or "").split(","):
        chunk = chunk.strip()
        if not chunk: continue
        sep = "->" if "->" in chunk else "-"
        parts = [p.strip() for p in chunk.split(sep)]
        if len(parts) == 2 and all(parts):
            pairs.append((parse_node_id(parts[0]), parse_node_id(parts[1])))
    return pairs

def _signature(G: nx.Graph):
    return G.number_of_edges(), round(sum(float(d.get("weight", 0)) for *_, d in G.edges(data=True)), 6)

def generer_rapport_diagnostic(view: str) -> Dict[str, Any]:
    G = load_networkx_graph_from_csv("routier")
    F = load_networkx_graph_from_csv("fibre")
    adj = tr.adjacency(G)

    casernes = _casernes(G)
    avertissement = "Aucune caserne." if not casernes else None

    accessibles = tr.reachable_from(adj, casernes)
    non_atteignables = sorted(set(G.nodes) - accessibles, key=_sort_key)
    composantes_fibre = tr.connected_components(tr.adjacency(F, directed=False))

    sens_uniques = {u: [v for v in vs if u not in adj.get(v, [])] for u, vs in adj.items()}
    cycle_general = tr.find_directed_cycle(adj)
    cycle_sens_uniques = tr.find_directed_cycle(sens_uniques)
    faibles = tr.connected_components(tr.undirected_view(adj))
    fortes = tr.strongly_connected_components(adj)

    return {
        "casernes_reference": casernes,
        "nb_sites": G.number_of_nodes(),
        "nb_sites_accessibles": len(accessibles),
        "sites_non_atteignables": non_atteignables,
        "nb_composantes_fibre": len(composantes_fibre),
        "composantes_fibre": composantes_fibre,
        "cycle_aller_retour": cycle_general is not None,
        "cycle_sens_uniques": cycle_sens_uniques,
        "nb_arcs_sens_uniques": sum(len(v) for v in sens_uniques.values()),
        "nb_composantes_faibles": len(faibles),
        "nb_composantes_fortes": len(fortes),
        "sites_isoles": sorted([n for n in G.nodes if G.degree(n) == 0], key=_sort_key),
        "sites_isoles_fibre": sorted([n for n in F.nodes if F.degree(n) == 0], key=_sort_key),
        "avertissement": avertissement,
    }

def _solve(G: nx.Graph, algo: str, s: Any, t: Any) -> Dict[str, Any]:
    res = sp.solve(algo, list(G.nodes), _edges_of(G), s, t)
    rencontres = []
    path = res.get("path") or []
    for u, v in zip(path, path[1:]):
        statut = str(G[u][v].get("statut", "")).lower()
        if statut not in STATUTS_OUVERTS:
            rencontres.append({"u": u, "v": v, "statut": statut})
    res["fermetures_rencontrees"] = rencontres
    return res

def calculer_intervention_service(start: str, target: str, view: str, algo: str, critere: str,
                                  manual_arcs: Optional[str], scenario_bytes: Optional[bytes]) -> Dict[str, Any]:
    _, unite = _critere(critere)
    G0 = _reweighted(load_networkx_graph_from_csv("routier" if view != "fibre" else "fibre"), critere)
    s, t = parse_node_id(start), parse_node_id(target)

    if s not in G0 or t not in G0:
        return {"accessible": False, "message": "Sommets introuvables."}

    avant = _solve(G0, algo, s, t)

    G1 = G0.copy()
    appliquees, introuvables, modifiees = [], [], []

    def fermer(u, v, origine):
        if G1.has_edge(u, v):
            G1.remove_edge(u, v)
            appliquees.append({"u": u, "v": v, "origine": origine})
        else:
            introuvables.append([u, v])

    if scenario_bytes:
        df = pd.read_csv(io.BytesIO(scenario_bytes))
        for _, row in df.iterrows():
            u, v = parse_node_id(row["u"]), parse_node_id(row["v"])
            action = str(row.get("action", "fermer")).strip().lower()
            if action in ("fermer", "desactiver"):
                fermer(u, v, "scénario")
            elif action == "modifier" and G1.has_edge(u, v):
                new = row.get("nouveau_temps_pointe", row.get("nouveau_poids"))
                if pd.notna(new):
                    G1[u][v]["weight"] = float(new)
                    modifiees.append({"u": u, "v": v, "nouveau_poids": float(new)})

    for u, v in _parse_pairs(manual_arcs):
        fermer(u, v, "saisie manuelle")

    apres = _solve(G1, algo, s, t)

    initial = set(zip(avant.get("path", []), avant.get("path", [])[1:])) if avant.get("path") else set()
    coupant = [a for a in appliquees if (a["u"], a["v"]) in initial]

    degradation = {"statut": None, "retard_absolu": None, "retard_relatif_pct": None}
    if avant.get("accessible") and apres.get("accessible"):
        delta = round(apres["cost"] - avant["cost"], 4)
        degradation.update(
            retard_absolu=delta,
            retard_relatif_pct=round(100 * delta / avant["cost"], 2) if avant["cost"] > 0 else 0.0,
            statut="inchange" if abs(delta) < 1e-9 else "degrade")
    elif avant.get("accessible") and not apres.get("accessible"):
        degradation["statut"] = "devenu_inaccessible"
    elif not avant.get("accessible"):
        degradation["statut"] = "inaccessible_des_le_depart"

    return {
        "start": s, "target": t, "algo": algo, "critere": critere, "unite": unite,
        "arcs_fermes_appliques": [[a["u"], a["v"]] for a in appliquees],
        "fermetures": appliquees,
        "fermetures_sur_trajet_initial": coupant,
        "arcs_introuvables": introuvables,
        "arcs_modifies": modifiees,
        "avant_perturbation": avant,
        "apres_perturbation": apres,
        "degradation": degradation,
    }

def comparer_algorithmes_service(start: str, target: str, view: str, critere: str) -> Dict[str, Any]:
    """Dijkstra, Bellman-Ford et Floyd-Warshall sur la même instance (+ BFS comme repère « arcs »)."""
    _, unite = _critere(critere)
    G = _reweighted(load_networkx_graph_from_csv("routier" if view != "fibre" else "fibre"), critere)
    s, t = parse_node_id(start), parse_node_id(target)
    if s not in G or t not in G:
        raise ValueError("Sommet de départ ou d'arrivée introuvable dans le graphe.")

    nodes, edges = list(G.nodes), _edges_of(G)
    resultats = [sp.solve(a, nodes, edges, s, t) for a in ("dijkstra", "bellman_ford", "floyd_warshall")]

    # BFS : minimise le NOMBRE d'arcs, pas le coût (repère pour discuter la différence)
    bfs = tr.bfs_path(tr.adjacency(G), s, t)
    weights = {(u, v): w for u, v, w in edges}
    resultats.append({
        "algo": "bfs_min_arcs", "statut": "ok" if bfs else "inaccessible", "accessible": bool(bfs),
        "cost": round(sum(weights[(a, b)] for a, b in zip(bfs, bfs[1:])), 4) if bfs else None,
        "nb_arcs": len(bfs) - 1 if bfs else 0, "path": bfs or [], "circuit_absorbant": False,
        "temps_ms": None, "remarque": "Minimise le nombre d'arcs, pas le coût : sert de repère.",
    })

    comparables = [r for r in resultats[:3] if r["statut"] in ("ok", "inaccessible")]
    couts = [r["cost"] for r in comparables if r["accessible"]]
    return {
        "start": s, "target": t, "critere": critere, "unite": unite,
        "nb_sommets": len(nodes), "nb_arcs": len(edges),
        "resultats": resultats,
        "algos_compares": len(comparables),
        "memes_acces": len({r["accessible"] for r in comparables}) <= 1,
        "couts_identiques": bool(couts) and max(couts) - min(couts) < 1e-6,
        "chemins_identiques": len({tuple(r["path"]) for r in comparables if r["accessible"]}) <= 1,
    }

def _sensibles(G: nx.Graph, types_param: Optional[str]):
    casernes = set(_casernes(G))
    candidats = [(n, _norm(d.get("type", ""))) for n, d in G.nodes(data=True) if n not in casernes]
    if types_param:
        voulus = {_norm(x) for x in types_param.split(",") if x.strip()}
        retenus = [n for n, t in candidats if t in voulus]
    else:
        retenus = [n for n, t in candidats if any(k in t for k in SENSIBLES_PAR_DEFAUT)]
    note = None
    if not retenus:
        retenus = [n for n, _ in candidats]
        note = "Aucun type de site sensible reconnu : tous les sites hors casernes sont considérés comme sensibles."
    utilises = sorted({G.nodes[n].get("type", "") for n in retenus})
    return sorted(retenus, key=_sort_key), utilises, note

def _distances(G: nx.Graph, casernes: list):
    """Dijkstra multi-casernes : une seule exécution depuis une super-source reliée à chaque caserne."""
    H = G.copy()
    H.add_node(SOURCE)
    for c in casernes:
        H.add_edge(SOURCE, c, weight=0.0)
    dist, paths = nx.single_source_dijkstra(H, SOURCE, weight="weight")
    dist.pop(SOURCE, None)
    return dist, {k: p[1:] for k, p in paths.items() if k != SOURCE}

def _indic_routier(G, casernes, demandes, sensibles, base=None):
    dist, paths = _distances(G, casernes)
    out = {
        "nb_demandes": len(demandes),
        "nb_demandes_accessibles": sum(1 for d in demandes if d in dist),
        "part_sensibles_accessibles_pct": round(100 * sum(1 for s in sensibles if s in dist) / max(len(sensibles), 1), 1),
        "nb_nouvellement_inaccessibles": 0, "nb_deja_inaccessibles": 0,
        "retard_moyen": 0.0, "retard_max": 0.0, "retard_moyen_pct": 0.0,
    }
    if base is not None:
        base_dist = base[0]
        nouveaux, deltas, pcts = 0, [], []
        for d in demandes:
            if d not in base_dist:
                out["nb_deja_inaccessibles"] += 1
            elif d not in dist:
                nouveaux += 1
            else:
                delta = dist[d] - base_dist[d]
                deltas.append(delta)
                pcts.append(100 * delta / base_dist[d] if base_dist[d] > 0 else 0.0)
        out["nb_nouvellement_inaccessibles"] = nouveaux
        if deltas:
            out.update(retard_moyen=round(sum(deltas) / len(deltas), 3), retard_max=round(max(deltas), 3),
                       retard_moyen_pct=round(sum(pcts) / len(pcts), 2))
    return out, (dist, paths)

def _secours(F0: nx.Graph, mst0: nx.Graph, u, v):
    """Tronçon de raccordement le moins coûteux après retrait de (u, v) de l'ACM initial."""
    T = mst0.copy()
    T.remove_edge(u, v)
    A, B = nx.node_connected_component(T, u), nx.node_connected_component(T, v)
    best = None
    for x, y, d in F0.edges(data=True):
        if (x == u and y == v) or (x == v and y == u):
            continue
        if (x in A and y in B) or (x in B and y in A):
            if best is None or d["cost"] < best["cost"]:
                best = {"u": x, "v": y, "cost": round(float(d["cost"]), 3)}
    return best

def _troncon_critique(F0, mst0):
    """Tronçon de l'ACM dont la panne coûte le plus cher à réparer (ou n'est pas réparable)."""
    pire, pire_score = None, -1.0
    for u, v in sorted(mst0.edges, key=lambda e: (_sort_key(e[0]), _sort_key(e[1]))):
        sec = _secours(F0, mst0, u, v)
        score = float("inf") if sec is None else sec["cost"] - float(mst0[u][v]["cost"])
        if score > pire_score:
            pire, pire_score = (u, v), score
    return pire

def _cout_mst(F):
    mst = nx.minimum_spanning_tree(F, weight="cost")
    return round(sum(float(d["cost"]) for *_, d in mst.edges(data=True)), 3)

def _indic_fibre(F0, mst0, panne=None):
    F = F0.copy()                                    # copie : la fibre de base reste intacte
    out = {"nb_composantes": nx.number_connected_components(F), "cout_total_acm": _cout_mst(F),
           "panne": None, "raccordement_possible": None, "troncon_secours": None,
           "cout_raccordement": None, "surcout": None, "nb_composantes_avant_raccordement": None}
    if panne:
        u, v = panne
        cout_panne = float(mst0[u][v]["cost"])
        sec = _secours(F0, mst0, u, v)
        F.remove_edge(u, v)
        out.update(
            panne={"u": u, "v": v, "cost": round(cout_panne, 3)},
            raccordement_possible=sec is not None, troncon_secours=sec,
            cout_raccordement=sec["cost"] if sec else None,
            surcout=round(sec["cost"] - cout_panne, 3) if sec else None,
            nb_composantes_avant_raccordement=nx.number_connected_components(mst0) + 1,
            nb_composantes=nx.number_connected_components(F),
            cout_total_acm=_cout_mst(F))
    return out

def evaluer_scenarios_service(nb_demandes: int, critere: str, axe: Optional[str],
                              troncon: Optional[str], types_sensibles: Optional[str]) -> Dict[str, Any]:
    """
    Trois scénarios comparés sur les mêmes demandes d'intervention :
      1. situation normale (référence) ; 2. fermeture d'un axe routier ; 3. panne d'un tronçon de fibre.
    """
    _, unite = _critere(critere)
    G0 = _reweighted(load_networkx_graph_from_csv("routier"), critere)
    F0 = load_networkx_graph_from_csv("fibre")
    sig_G, sig_F = _signature(G0), _signature(F0)

    casernes = _casernes(G0)
    if not casernes:
        raise ValueError("Aucune caserne (type « caserne ») dans sites.csv.")
    sensibles, types_utilises, note_types = _sensibles(G0, types_sensibles)
    pas = len(sensibles) / min(nb_demandes, len(sensibles)) if sensibles else 1
    demandes = [sensibles[int(i * pas)] for i in range(min(nb_demandes, len(sensibles)))]

    # --- référence
    indic_base, base = _indic_routier(G0.copy(), casernes, demandes, sensibles)
    mst0 = nx.minimum_spanning_tree(F0, weight="cost")

    # --- scénario 2 : axe routier le plus emprunté (ou axe choisi)
    if axe:
        arcs = _parse_pairs(axe)
        if not arcs:
            raise ValueError("Axe invalide (format attendu : u->v, séparés par des virgules).")
        inconnus = [f"{u}->{v}" for u, v in arcs if not G0.has_edge(u, v)]
        if inconnus:
            raise ValueError(f"Arcs inexistants dans le graphe routier : {', '.join(inconnus)}")
        origine_axe = "choisi"
    else:
        usage = Counter()
        for d in demandes:
            p = base[1].get(d, [])
            usage.update(zip(p, p[1:]))
        arcs, origine_axe = [], "le plus emprunté par les plus courts chemins de référence"
        if usage:
            u, v = max(sorted(usage, key=lambda e: (_sort_key(e[0]), _sort_key(e[1]))), key=lambda e: usage[e])
            arcs = [(u, v)] + ([(v, u)] if G0.has_edge(v, u) else [])
    G2 = G0.copy()
    for u, v in arcs:
        G2.remove_edge(u, v)
    indic_axe, _ = _indic_routier(G2, casernes, demandes, sensibles, base)

    # --- scénario 3 : panne de fibre
    if troncon:
        pairs = _parse_pairs(troncon)
        if len(pairs) != 1 or not mst0.has_edge(*pairs[0]):
            raise ValueError("Le tronçon doit être UN tronçon de l'arbre couvrant minimal (ex : 4-9).")
        panne, origine_panne = pairs[0], "choisi"
    else:
        panne, origine_panne = _troncon_critique(F0, mst0), "tronçon de l'ACM le plus coûteux à raccorder"

    scenarios = [
        {"id": "normal", "titre": "Situation normale", "description": "Référence : réseaux de base, aucune perturbation.",
         "perturbation": {"arcs_routiers_fermes": [], "troncon_fibre": None},
         "routier": indic_base, "fibre": _indic_fibre(F0, mst0)},
        {"id": "axe_ferme", "titre": "Fermeture d'un axe routier",
         "description": f"Arcs fermés ({origine_axe}) : " + (", ".join(f"{u}→{v}" for u, v in arcs) or "aucun"),
         "perturbation": {"arcs_routiers_fermes": [[u, v] for u, v in arcs], "troncon_fibre": None},
         "routier": indic_axe, "fibre": _indic_fibre(F0, mst0)},
        {"id": "panne_fibre", "titre": "Panne d'un tronçon de fibre",
         "description": f"Tronçon en panne ({origine_panne}) : " + (f"{panne[0]}–{panne[1]}" if panne else "aucun"),
         "perturbation": {"arcs_routiers_fermes": [], "troncon_fibre": {"u": panne[0], "v": panne[1]} if panne else None},
         "routier": indic_base, "fibre": _indic_fibre(F0, mst0, panne)},
    ]

    return {
        "parametres": {"critere": critere, "unite": unite, "nb_demandes": len(demandes), "casernes": casernes,
                       "nb_sites_sensibles": len(sensibles), "types_sensibles_utilises": types_utilises,
                       "note_types_sensibles": note_types},
        "reference_inchangee": _signature(G0) == sig_G and _signature(F0) == sig_F,
        "scenarios": scenarios,
    }

def acm_couts_egaux_service() -> Dict[str, Any]:
    """
    Plusieurs ACM existent dès qu'une arête hors arbre a le même coût que la plus chère des arêtes
    du chemin qui la relie dans l'arbre : on peut échanger les deux sans changer le coût total.
    """
    F = load_networkx_graph_from_csv("fibre")
    T = nx.minimum_spanning_tree(F, weight="cost", algorithm="kruskal")
    P = nx.minimum_spanning_tree(F, weight="cost", algorithm="prim")

    alternatives = []
    for x, y, d in F.edges(data=True):
        if T.has_edge(x, y) or not nx.has_path(T, x, y):
            continue
        chemin = nx.shortest_path(T, x, y)
        pire = max(zip(chemin, chemin[1:]), key=lambda e: T[e[0]][e[1]]["cost"])
        if abs(float(d["cost"]) - float(T[pire[0]][pire[1]]["cost"])) < 1e-9:
            alternatives.append({"arete_hors_arbre": {"u": x, "v": y, "cost": float(d["cost"])},
                                 "remplace": {"u": pire[0], "v": pire[1], "cost": float(T[pire[0]][pire[1]]["cost"])}})

    occurrences = Counter(round(float(d["cost"]), 6) for *_, d in F.edges(data=True))
    norm = lambda G: {frozenset(e) for e in G.edges}
    return {
        "nb_aretes": F.number_of_edges(),
        "nb_couts_dupliques": sum(1 for c in occurrences.values() if c > 1),
        "plusieurs_acm_possibles": bool(alternatives),
        "nb_echanges_possibles": len(alternatives),
        "exemples": alternatives[:8],
        "kruskal_prim_memes_aretes": norm(T) == norm(P),
        "cout_kruskal": _cout_mst(F),
    }