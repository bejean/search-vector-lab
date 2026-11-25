"""Demande à TEI les vecteurs d'une requête et de passages, puis affiche leur similarité cosinus.

Le premier texte est comparé à chacun des suivants. Les vecteurs sont normalisés : le cosinus est un produit scalaire.
Sans argument, compare « query: fromage à pâte molle » à un passage sur le camembert et à un passage sur Jupiter.

Usage : python outils/similarites.py ["texte 1" "texte 2" …]
"""
import sys

import requests

DEFAUT = ["query: fromage à pâte molle",
          "passage: Le camembert est un fromage à pâte molle et à croûte fleurie.",
          "passage: Jupiter est la plus grande planète du Système solaire."]

textes = sys.argv[1:] or DEFAUT
if len(textes) < 2:
    sys.exit(__doc__)
r = requests.post("http://tei:80/embed", json={"inputs": textes, "normalize": True}, timeout=60)
r.raise_for_status()
v = r.json()
print(f"dimensions : {len(v[0])}")
for texte, vecteur in zip(textes[1:], v[1:]):
    print(f"{sum(x * y for x, y in zip(v[0], vecteur)):.3f}  « {textes[0]} » / « {texte} »")
