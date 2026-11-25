"""Calcule l'embedding de chaque article du jeu de données avec TEI (modèle multilingual-e5-small).

Le modèle E5 attend le préfixe « passage: » pour un document et « query: » pour une requête.
Les vecteurs sont normalisés (norme 1) : cosinus et produit scalaire donnent alors le même classement.
Entrée : donnees/wikipedia-fr.jsonl par défaut ; sortie : le même nom suffixé de « -vecteurs » (champ « vecteur »).

Usage : docker compose run --rm outils python outils/vectoriser.py [donnees/<fichier>.jsonl]
"""
import json
import sys

import requests

TEI = "http://tei:80/embed"
ENTREE = sys.argv[1] if len(sys.argv) > 1 else "donnees/wikipedia-fr.jsonl"
SORTIE = ENTREE.removesuffix(".jsonl") + "-vecteurs.jsonl"
LOT = 32


def embeddings(textes):
    r = requests.post(TEI, json={"inputs": textes, "normalize": True, "truncate": True}, timeout=300)
    r.raise_for_status()
    return r.json()


def main():
    with open(ENTREE, encoding="utf-8") as f:
        docs = [json.loads(ligne) for ligne in f]
    with open(SORTIE, "w", encoding="utf-8") as f:
        for i in range(0, len(docs), LOT):
            lot = docs[i:i + LOT]
            vecteurs = embeddings([f"passage: {d['titre']}. {d['texte']}" for d in lot])
            for doc, vecteur in zip(lot, vecteurs):
                f.write(json.dumps({**doc, "vecteur": vecteur}, ensure_ascii=False) + "\n")
            print(f"{min(i + LOT, len(docs))}/{len(docs)}", end="\r", flush=True)
    print(f"\n{len(docs)} vecteurs de {len(vecteurs[0])} dimensions dans {SORTIE}")


if __name__ == "__main__":
    main()
