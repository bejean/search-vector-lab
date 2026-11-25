"""Envoie les articles vectorisés dans un moteur : solr, elasticsearch ou opensearch.

La collection ou l'index doit exister avec son champ vectoriel « vecteur » (étape 3 du parcours).
Par défaut : entrée donnees/wikipedia-fr-vecteurs.jsonl, collection ou index « wikipedia ».

Usage : docker compose run --rm outils python outils/indexer.py <solr|elasticsearch|opensearch> [entrée] [index]
"""
import json
import sys

import requests

ENTREE = sys.argv[2] if len(sys.argv) > 2 else "donnees/wikipedia-fr-vecteurs.jsonl"
INDEX = sys.argv[3] if len(sys.argv) > 3 else "wikipedia"
LOT = 200
URL = {
    "solr": f"http://solr:8983/solr/{INDEX}",
    "elasticsearch": f"http://elasticsearch:9200/{INDEX}",
    "opensearch": f"http://opensearch:9200/{INDEX}",
}


def envoyer_solr(docs):
    r = requests.post(f"{URL['solr']}/update", json=docs, timeout=300)
    r.raise_for_status()


def envoyer_bulk(moteur, docs):
    lignes = []
    for d in docs:
        lignes.append(json.dumps({"index": {"_id": d["id"]}}))
        lignes.append(json.dumps({k: v for k, v in d.items() if k != "id"}, ensure_ascii=False))
    r = requests.post(f"{URL[moteur]}/_bulk", data=("\n".join(lignes) + "\n").encode(),
                      headers={"Content-Type": "application/x-ndjson"}, timeout=300)
    r.raise_for_status()
    if r.json().get("errors"):
        erreur = next(i for i in r.json()["items"] if "error" in i["index"])
        sys.exit(f"Erreur d'indexation : {json.dumps(erreur['index']['error'], ensure_ascii=False)}")


def main():
    moteur = sys.argv[1] if len(sys.argv) > 1 else ""
    if moteur not in URL:
        sys.exit(__doc__)
    with open(ENTREE, encoding="utf-8") as f:
        docs = [json.loads(ligne) for ligne in f]
    for i in range(0, len(docs), LOT):
        lot = docs[i:i + LOT]
        envoyer_solr(lot) if moteur == "solr" else envoyer_bulk(moteur, lot)
        print(f"{min(i + LOT, len(docs))}/{len(docs)}", end="\r", flush=True)
    if moteur == "solr":
        requests.get(f"{URL['solr']}/update", params={"commit": "true"}, timeout=300).raise_for_status()
    else:
        requests.post(f"{URL[moteur]}/_refresh", timeout=300).raise_for_status()
    print(f"\n{len(docs)} documents indexés dans {moteur}")


if __name__ == "__main__":
    main()
