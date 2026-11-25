"""Affiche le vecteur d'une requête (préfixe E5 « query: »), à coller dans une requête kNN.

Usage : docker compose run --rm outils python outils/vecteur_requete.py "fromage à pâte molle" [--lignes]
Avec --lignes, un nombre par ligne : collé dans la console Dev Tools de Dashboards, le tableau
se replie alors avec la flèche de la marge (la console de Kibana ne replie pas : y passer par une variable).
"""
import json
import sys

import requests

args = [a for a in sys.argv[1:] if a != "--lignes"]
if len(args) != 1:
    sys.exit(__doc__)
r = requests.post("http://tei:80/embed", json={"inputs": f"query: {args[0]}", "normalize": True}, timeout=60)
r.raise_for_status()
print(json.dumps([round(x, 6) for x in r.json()[0]], indent=2 if "--lignes" in sys.argv else None))
