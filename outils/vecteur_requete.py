"""Affiche le vecteur d'une requête (préfixe E5 « query: »), à coller dans une requête kNN.

Usage : docker compose run --rm outils python outils/vecteur_requete.py "fromage à pâte molle"
"""
import json
import sys

import requests

if len(sys.argv) != 2:
    sys.exit(__doc__)
r = requests.post("http://tei:80/embed", json={"inputs": f"query: {sys.argv[1]}", "normalize": True}, timeout=60)
r.raise_for_status()
print(json.dumps([round(x, 6) for x in r.json()[0]]))
