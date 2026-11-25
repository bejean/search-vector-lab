# search-vector-lab

Laboratoire de recherche vectorielle, hybride et RAG : Apache Solr, Elasticsearch et OpenSearch côte à côte, avec un serveur d'embeddings local ([Text Embeddings Inference](https://github.com/huggingface/text-embeddings-inference)) et un jeu de données en français tiré de Wikipédia.

Il accompagne une série d'articles du blog d'[Eolya](https://www.eolya.fr/). Chaque article a son parcours pas à pas dans `parcours/` et un tag dans ce dépôt, aux versions des moteurs de sa date de publication.

| Parcours | Article | Tag |
|---|---|---|
| [01 : la recherche vectorielle](parcours/01-recherche-vectorielle.md) | Recherche vectorielle avec Solr, Elasticsearch et OpenSearch : le guide pratique | `article-01` |

## Prérequis

- Docker avec Docker Compose.
- Environ 12 Go de mémoire libre.
- `vm.max_map_count` à 262144 au moins (Elasticsearch et OpenSearch), sur l'hôte Docker.

## Démarrage

```bash
make up        # démarre la stack
make status    # vérifie que chaque service répond
make help      # toutes les commandes : stack, indexation, recherche, remise à zéro
```

| Service | Adresse |
|---|---|
| Solr | http://localhost:8983/solr/ |
| Elasticsearch | http://localhost:9200 |
| Kibana | http://localhost:5601 |
| OpenSearch | http://localhost:9201 |
| OpenSearch Dashboards | http://localhost:5602 |
| TEI | http://localhost:8088 |

La sécurité des moteurs est désactivée : ce laboratoire est réservé à un usage local.

## Contenu

- `Makefile` : commandes du laboratoire (`make help`).
- `docker-compose.yml` : les services, aux versions du dernier parcours.
- `outils/` : scripts Python, lancés dans un conteneur (`docker compose run --rm outils python outils/<script>.py`).
  - `telecharger_wikipedia.py` : construit le jeu de données ;
  - `vectoriser.py` : calcule les embeddings avec TEI ;
  - `indexer.py` : envoie les documents dans un moteur ;
  - `vecteur_requete.py` : affiche le vecteur d'une requête ;
  - `comparer.py` : même recherche kNN sur les trois moteurs, côte à côte.
  - `importer_crawl.py` : convertit un corpus crawlé par Elastic Open Crawler au format du laboratoire (voir ci-dessous).
- `donnees/wikipedia-fr.jsonl` : introductions de 909 articles de Wikipédia en français, sur six thèmes ([licence](donnees/LICENCE-DONNEES.md)).
- `parcours/` : les parcours pas à pas.

## Utiliser un autre corpus

`outils/importer_crawl.py` convertit la sortie d'[Elastic Open Crawler](https://github.com/elastic/crawler) (un dossier de fichiers JSON, une liste de documents par fichier) en `donnees/crawl-<dossier>.jsonl`. Il est écrit en Python standard et se lance sur l'hôte, car le dossier du crawl est en dehors du laboratoire :

```bash
make importer-crawl DOSSIER=<dossier du crawl> THEME=<nom> [MAX=N]
make vectoriser FICHIER=donnees/crawl-<dossier>.jsonl
make indexer MOTEUR=elasticsearch FICHIER=donnees/crawl-<dossier>-vecteurs.jsonl INDEX=<index>
```

L'index doit exister, avec les mêmes champs que `wikipedia` (étape 3 du parcours 1) et un champ `date` de type date. Les fichiers `donnees/crawl-*.jsonl` ne sont pas versionnés : un site crawlé n'est généralement pas sous licence libre. Seuls les 512 premiers tokens de chaque document sont vectorisés (limite d'E5) ; découper les documents longs en passages fera l'objet d'un parcours ultérieur.
