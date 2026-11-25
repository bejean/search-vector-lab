"""Convertit un corpus crawlé par Elastic Open Crawler (format de sortie d'es-labs) au format du laboratoire.

Entrée : un dossier de fichiers JSON, chacun contenant une liste de documents (title, body, url, publication_date…).
Sortie : un fichier JSONL (id, titre, theme, texte, url, date) à passer à vectoriser.py puis indexer.py.

Le texte complet est gardé (recherche lexicale), mais le modèle E5 n'en vectorise que les 512 premiers tokens
(environ 2 000 caractères) : découper les longs documents en passages est le sujet d'un parcours ultérieur.
Ces corpus ne sont pas sous licence libre : le fichier produit reste local (donnees/crawl-*.jsonl, ignoré par Git).

Lancé par le Makefile dans le conteneur d'outils, le dossier du crawl étant monté en lecture seule sur /crawl :
    make importer-crawl DOSSIER=<dossier> [THEME=nom] [MAX=N]
Exemple :
    make importer-crawl DOSSIER=../ElasticStack_ia/labs/data/output-clean/elastic-search-labs-blog-fr THEME=search-labs
"""
import argparse
import glob
import json
import os


def documents(dossier):
    for chemin in sorted(glob.glob(os.path.join(dossier, "*.json"))):
        with open(chemin, encoding="utf-8") as f:
            contenu = json.load(f)
        yield from (contenu if isinstance(contenu, list) else [contenu])


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("dossier", help="dossier de sortie du crawler (fichiers *.json)")
    p.add_argument("--theme", help="valeur du champ theme (par défaut : nom du dossier)")
    p.add_argument("--max", type=int, default=0, help="nombre maximal de documents (0 : tous)")
    p.add_argument("--nom", help="nom du corpus pour le fichier de sortie (par défaut : nom du dossier)")
    args = p.parse_args()

    nom = args.nom or os.path.basename(os.path.normpath(args.dossier))
    theme = args.theme or nom
    sortie = f"donnees/crawl-{nom}.jsonl"
    vus, n = set(), 0
    with open(sortie, "w", encoding="utf-8") as f:
        for d in documents(args.dossier):
            texte = (d.get("body") or "").strip()
            if not d.get("id") or d["id"] in vus or len(texte) < 200:
                continue
            vus.add(d["id"])
            f.write(json.dumps({"id": d["id"], "titre": (d.get("title") or "").strip(), "theme": theme,
                                "texte": texte, "url": d.get("url"), "date": d.get("publication_date")},
                               ensure_ascii=False) + "\n")
            n += 1
            if args.max and n >= args.max:
                break
    print(f"{n} documents dans {sortie}")


if __name__ == "__main__":
    main()
