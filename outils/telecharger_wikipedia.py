"""Construit le jeu de données du laboratoire : introductions d'articles de Wikipédia en français.

Chaque thème part de quelques catégories, parcourues avec leurs sous-catégories, jusqu'à MAX_PAR_THEME
articles. Résultat : donnees/wikipedia-fr.jsonl, une ligne par article (id, titre, theme, texte, url).
Textes sous licence CC BY-SA 4.0 (voir donnees/LICENCE-DONNEES.md).

Usage : docker compose run --rm outils python outils/telecharger_wikipedia.py
"""
import json
import time

import requests

API = "https://fr.wikipedia.org/w/api.php"
SESSION = requests.Session()
SESSION.headers["User-Agent"] = "search-vector-lab/0.1 (educational search lab)"
MAX_PAR_THEME = 250
PROFONDEUR = 2
PAUSE = 1.0  # secondes entre deux appels (limite de débit de Wikipédia)
SORTIE = "donnees/wikipedia-fr.jsonl"

THEMES = {
    "gastronomie": ["Fromage français", "Pâtisserie française", "Spécialité culinaire française"],
    "vin": ["Cépage", "Vignoble de France"],
    "peinture": ["Peintre impressionniste", "Peintre français du XIXe siècle"],
    "astronomie": ["Exoplanète", "Planète naine", "Constellation", "Étoile"],
    "patrimoine": ["Château de la Loire", "Cathédrale en France"],
    "musique": ["Instrument de musique"],
}


def appel(params):
    params = {**params, "action": "query", "format": "json", "formatversion": 2}
    for essai in range(8):
        time.sleep(PAUSE)
        r = SESSION.get(API, params=params, timeout=30)
        if r.status_code == 200 and r.text.startswith("{"):
            return r.json()
        time.sleep(int(r.headers.get("Retry-After", 0)) or 5 * (essai + 1))
    r.raise_for_status()
    raise RuntimeError(f"Réponse inattendue de l'API : {r.text[:200]}")


def membres(categorie):
    """Pages (ns 0) et sous-catégories (ns 14) d'une catégorie."""
    params = {"list": "categorymembers", "cmtitle": f"Catégorie:{categorie}",
              "cmnamespace": "0|14", "cmlimit": 500}
    while True:
        rep = appel(params)
        yield from rep["query"]["categorymembers"]
        if "continue" not in rep:
            return
        params.update(rep["continue"])


def pages_du_theme(categories):
    vues, pages = set(), []
    file = [(c, 0) for c in categories]
    while file and len(pages) < MAX_PAR_THEME:
        categorie, prof = file.pop(0)
        if categorie in vues:
            continue
        vues.add(categorie)
        for m in membres(categorie):
            if m["ns"] == 0 and m["pageid"] not in {p for p, _ in pages}:
                pages.append((m["pageid"], m["title"]))
            elif m["ns"] == 14 and prof < PROFONDEUR:
                file.append((m["title"].split(":", 1)[1], prof + 1))
    return pages[:MAX_PAR_THEME]


def introductions(ids):
    """Introductions en texte brut, par lots de 20 (limite de l'API pour exintro)."""
    for i in range(0, len(ids), 20):
        rep = appel({"prop": "extracts|info", "exintro": 1, "explaintext": 1, "inprop": "url",
                     "pageids": "|".join(str(x) for x in ids[i:i + 20])})
        yield from rep["query"]["pages"]


def main():
    deja = set()
    total = 0
    with open(SORTIE, "w", encoding="utf-8") as f:
        for theme, categories in THEMES.items():
            pages = [p for p in pages_du_theme(categories) if p[0] not in deja]
            n = 0
            for page in introductions([p for p, _ in pages]):
                texte = (page.get("extract") or "").strip()
                if len(texte) < 200:
                    continue
                deja.add(page["pageid"])
                f.write(json.dumps({"id": str(page["pageid"]), "titre": page["title"], "theme": theme,
                                    "texte": texte, "url": page["fullurl"]}, ensure_ascii=False) + "\n")
                n += 1
            print(f"{theme} : {n} articles")
            total += n
    print(f"Total : {total} articles dans {SORTIE}")


if __name__ == "__main__":
    main()
