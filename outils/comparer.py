"""Lance la même recherche kNN sur les trois moteurs, la compare au vrai résultat (force brute) et mesure le rappel.

Usage : docker compose run --rm outils python outils/comparer.py "fromage à pâte molle" [k] [thème]
Le thème facultatif (gastronomie, vin, peinture, astronomie, patrimoine, musique) est appliqué en préfiltre.

Le vrai top k est calculé en comparant la requête à tous les vecteurs de donnees/wikipedia-fr-vecteurs.jsonl
(score (1 + cos) / 2, comme les moteurs). Le rappel est la part de ce vrai top k que le moteur a retrouvée.
Réglages des moteurs : ceux par défaut (Solr topK = k ; Elasticsearch num_candidates 100, oversample 3 ;
OpenSearch ef_search 100).
"""
import json
import sys

import requests

VECTEURS = "donnees/wikipedia-fr-vecteurs.jsonl"


def vecteur(texte):
    r = requests.post("http://tei:80/embed", json={"inputs": f"query: {texte}", "normalize": True}, timeout=60)
    r.raise_for_status()
    return r.json()[0]


def exact(v, k, theme):
    with open(VECTEURS, encoding="utf-8") as f:
        docs = [json.loads(ligne) for ligne in f]
    scores = [(d["titre"], (1 + sum(a * b for a, b in zip(v, d["vecteur"]))) / 2)
              for d in docs if not theme or d["theme"] == theme]
    return sorted(scores, key=lambda x: -x[1])[:k]


def solr(v, k, theme):
    params = {"q": f"{{!knn f=vecteur topK={k}}}{v}", "fl": "titre,score", "rows": k}
    if theme:
        params["fq"] = f"theme:{theme}"
    r = requests.post("http://solr:8983/solr/wikipedia/select", data=params, timeout=60)
    r.raise_for_status()
    return [(d["titre"], d["score"]) for d in r.json()["response"]["docs"]]


def elasticsearch(v, k, theme):
    knn = {"field": "vecteur", "query_vector": v, "k": k, "num_candidates": 100}
    if theme:
        knn["filter"] = {"term": {"theme": theme}}
    r = requests.post("http://elasticsearch:9200/wikipedia/_search",
                      json={"knn": knn, "size": k, "_source": ["titre"]}, timeout=60)
    r.raise_for_status()
    return [(h["_source"]["titre"], h["_score"]) for h in r.json()["hits"]["hits"]]


def opensearch(v, k, theme):
    knn = {"vector": v, "k": k}
    if theme:
        knn["filter"] = {"term": {"theme": theme}}
    r = requests.post("http://opensearch:9200/wikipedia/_search",
                      json={"query": {"knn": {"vecteur": knn}}, "size": k, "_source": ["titre"]}, timeout=60)
    r.raise_for_status()
    return [(h["_source"]["titre"], h["_score"]) for h in r.json()["hits"]["hits"]]


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    texte, k = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 10
    theme = sys.argv[3] if len(sys.argv) > 3 else None
    v = vecteur(texte)
    vrai = exact(v, k, theme)
    vrais_titres = {titre for titre, _ in vrai}
    print("\n== Exact (force brute)")
    for rang, (titre, score) in enumerate(vrai, 1):
        print(f"{rang:>2}. {score:.4f}  {titre}")
    for nom, f in (("Solr", solr), ("Elasticsearch", elasticsearch), ("OpenSearch", opensearch)):
        resultats = f(v, k, theme)
        trouves = sum(titre in vrais_titres for titre, _ in resultats)
        print(f"\n== {nom} (rappel {trouves}/{len(vrai)})")
        for rang, (titre, score) in enumerate(resultats, 1):
            marque = " " if titre in vrais_titres else "✗"
            print(f"{rang:>2}. {score:.4f} {marque} {titre}")
        manques = [titre for titre, _ in vrai if titre not in {t for t, _ in resultats}]
        if manques:
            print(f"    manqués : {', '.join(manques)}")


if __name__ == "__main__":
    main()
