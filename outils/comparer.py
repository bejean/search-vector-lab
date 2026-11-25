"""Lance la même recherche kNN sur les trois moteurs et affiche les résultats côte à côte.

Usage : docker compose run --rm outils python outils/comparer.py "fromage à pâte molle" [k] [thème]
Le thème facultatif (gastronomie, vin, peinture, astronomie, patrimoine, musique) est appliqué en préfiltre.
"""
import sys

import requests


def vecteur(texte):
    r = requests.post("http://tei:80/embed", json={"inputs": f"query: {texte}", "normalize": True}, timeout=60)
    r.raise_for_status()
    return r.json()[0]


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
    for nom, f in (("Solr", solr), ("Elasticsearch", elasticsearch), ("OpenSearch", opensearch)):
        print(f"\n== {nom}")
        for rang, (titre, score) in enumerate(f(v, k, theme), 1):
            print(f"{rang:>2}. {score:.4f}  {titre}")


if __name__ == "__main__":
    main()
