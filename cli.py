import argparse
import sys
import json
from app.algorithme.resilience_service import (
    generer_rapport_diagnostic,
    calculer_intervention_service,
    acm_couts_egaux_service
)
from app.algorithme import shortest_paths as sp


def main():
    parser = argparse.ArgumentParser(description="Novapolis Résilience - CLI de gestion et d'analyse des graphes.")
    subparsers = parser.add_subparsers(dest="command", help="Commande à exécuter")

    # 1. Commande de diagnostic (Module 1)
    parser_diag = subparsers.add_parser("diagnostic", help="Exécute le diagnostic global du réseau.")
    parser_diag.add_argument("--view", default="routier", choices=["routier", "fibre"], help="Vue du réseau.")

    # 2. Commande d'intervention / plus court chemin (Module 2)
    parser_inter = subparsers.add_parser("intervention", help="Calcule un itinéraire de secours.")
    parser_inter.add_argument("--start", required=True, help="Sommet de départ.")
    parser_inter.add_argument("--target", required=True, help="Sommet d'arrivée.")
    parser_inter.add_argument("--view", default="routier", choices=["routier", "fibre"], help="Vue du réseau.")
    parser_inter.add_argument("--algo", default="dijkstra", choices=["dijkstra", "bellman_ford", "floyd_warshall"],
                              help="Algorithme.")
    parser_inter.add_argument("--critere", default="temps_normal", choices=["temps_normal", "temps_pointe", "distance"],
                              help="Critère de poids.")
    parser_inter.add_argument("--arcs", default=None, help="Arcs manuels à fermer (ex: 3->16,16->3).")
    parser_inter.add_argument("--scenario", default=None, help="Chemin vers un fichier CSV de scénario.")

    # 3. Commande ACM / Coûts égaux (Module 4.4)
    subparsers.add_parser("fibre-ties", help="Analyse les arbres couvrants minimaux multiples (coûts égaux).")

    # 4. Tests des circuits absorbants (Module 3)
    subparsers.add_parser("test-cycles", help="Exécute les tests unitaires pour les circuits absorbants.")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "diagnostic":
            result = generer_rapport_diagnostic(args.view)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "intervention":
            scenario_bytes = None
            if args.scenario:
                with open(args.scenario, "rb") as f:
                    scenario_bytes = f.read()

            result = calculer_intervention_service(
                start=args.start,
                target=args.target,
                view=args.view,
                algo=args.algo,
                critere=args.critere,
                manual_arcs=args.arcs,
                scenario_bytes=scenario_bytes
            )
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "fibre-ties":
            result = acm_couts_egaux_service()
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.command == "test-cycles":
            tests = sp.run_all_tests()
            result = {"tests": tests, "tous_reussis": all(t["reussi"] for t in tests)}
            print(json.dumps(result, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"Erreur lors de l'exécution : {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()