# Parcours 1 : la recherche vectorielle avec Solr, Elasticsearch et OpenSearch

Versions : Solr 10.0.0, Elasticsearch et Kibana 9.3.1, OpenSearch et OpenSearch Dashboards 3.5.0, Text Embeddings Inference (TEI) 1.9.2 avec le modèle `intfloat/multilingual-e5-small`.

## Objectif final

Ce parcours a deux buts :

1. **S'initier** à la recherche vectorielle en la pratiquant, de la même façon, sur les trois moteurs.
2. **Produire un article** de blog à partir de ce qu'on a fait, observé et capturé.

### L'article visé

- **Titre** : « Recherche vectorielle avec Solr, Elasticsearch et OpenSearch : les bases ».
- **Publication** : blog d'[Eolya](https://www.eolya.fr/), daté du 17 mars 2026, aux versions des moteurs sorties à cette date (ci-dessus). C'est le premier article d'une série sur la recherche vectorielle, hybride et le RAG.
- **Lecteurs** : architectes, développeurs et administrateurs qui exploitent ou choisissent un moteur de recherche.
- **Promesse** : comprendre ce qu'est la recherche vectorielle et la mettre en œuvre sur Solr, Elasticsearch et OpenSearch, en voyant ce que chacun fait par défaut, ce qui est gratuit, expérimental ou soumis à licence, et les pièges rencontrés.
- **Plan** : celui des étapes du parcours.
  1. Le laboratoire.
  2. Ce qu'est un embedding.
  3. Déclarer un champ vectoriel (tableau des équivalences).
  4. Indexer et mesurer.
  5. Interroger en kNN ; la recherche approchée.
  6. Préfiltre et post-filtre.
  7. Vectoriser dans le moteur (tableau comparatif).
  8. Dimensionnement.
  9. Avis du praticien et tableau de synthèse.
- **Hors périmètre**, réservé aux articles suivants de la série : recherche hybride et RRF, quantification détaillée, reranking, découpage des documents en passages, RAG.
- **Matière de l'article** :
  - les notes prises à chaque étape (`notes/01-recherche-vectorielle.md`) ;
  - les copies d'écran de `captures/` ;
  - les requêtes de ce parcours ;
  - le bilan de l'étape 9.

  Le texte est rédigé ensuite, avec un tableau comparatif et un avis à la première personne. Il renvoie à ce dépôt, au tag `article-01`, pour que le lecteur refasse les manipulations.

## Mode d'emploi

Le parcours se suit dans l'ordre ; compter deux à trois heures. Chaque étape donne :
- **Objectif** : ce qu'on apprend ;
- **À faire** : les commandes (terminal de l'hôte, dans ce dossier) ou les requêtes (interfaces web). L'hôte n'a besoin que de Docker, `make`, `curl`, d'un éditeur de texte et, si on le souhaite, de Postman : les scripts Python tournent dans le conteneur d'outils, via `make` ;
- **À observer** : ce qu'il faut regarder, avec une question à garder en tête ;
- **Pourquoi** : l'explication ;
- 📸 : la copie d'écran à prendre, à enregistrer dans `captures/` sous le nom indiqué. Chaque consigne dit **où** la prendre, **ce qui doit être visible**, le **cadrage**, et **ce qu'elle montre** dans l'article. Règles communes :
  - navigateur : fenêtre de 1440 × 900, zoom 100 %, barre d'adresse visible (elle montre l'URL), un seul onglet ; capturer la fenêtre entière ;
  - console Dev Tools : la requête à gauche, la réponse à droite, sans autre requête dans le panneau de gauche (effacer les précédentes) ; pour que la requête tienne à l'écran, le vecteur de 384 nombres passe par une variable dans Kibana et se replie avec la flèche de la marge dans Dashboards (étape 5) ;
  - terminal : au moins 120 colonnes, police lisible, `clear` avant les commandes ; la commande tapée doit apparaître au-dessus de sa sortie ; cadrer de la première commande à la dernière ligne de sortie.

Note tes observations dans `notes/01-recherche-vectorielle.md` (une section par étape) : l'article sera écrit à partir d'elles. Ce fichier est personnel : le dossier `notes/` est ignoré par Git et ne part pas dans le dépôt public. S'il n'existe pas, `make notes` le crée à partir du modèle `parcours/01-notes-modele.md`.

| Service | Adresse depuis l'hôte |
|---|---|
| Solr (interface d'admin) | http://localhost:8983/solr/ |
| Elasticsearch (API) | http://localhost:9200 |
| Kibana (Dev Tools) | http://localhost:5601/app/dev_tools#/console |
| OpenSearch (API) | http://localhost:9201 |
| OpenSearch Dashboards (Dev Tools) | http://localhost:5602/app/dev_tools#/console |
| TEI (embeddings) | http://localhost:8088 |

---

## Étape 1 : démarrer le laboratoire

**Objectif** : avoir les trois moteurs et le serveur d'embeddings en marche.

**À faire**
```bash
make up        # les commandes du laboratoire : make help
make status    # chaque service doit répondre 200
curl -s localhost:9200 | grep number        # Elasticsearch
curl -s localhost:9201 | grep number        # OpenSearch
curl -s "localhost:8983/solr/admin/info/system?wt=json" | grep -o '"solr-spec-version":"[^"]*"\|"mode":"[^"]*"'
curl -s localhost:8088/info                 # TEI : modèle chargé, longueur maximale
```
Le premier démarrage télécharge les images et le modèle (quelques minutes). Kibana et Dashboards mettent une à deux minutes de plus à répondre.

**À observer**
- Solr démarre en mode `solrcloud` sans rien préciser : c'est le mode par défaut depuis Solr 10, avec un ZooKeeper embarqué.
- `max_input_length` de TEI : 512 tokens. Un texte plus long est tronqué (le reste est ignoré pour le vecteur).

**Pourquoi** : la sécurité est désactivée sur les trois moteurs pour se concentrer sur la recherche ; les ports ne sont ouverts que sur la machine locale.

La console Dev Tools de Kibana et celle de Dashboards gardent leur contenu dans le stockage du navigateur, propre à chaque adresse : si un autre Kibana a déjà servi sur `localhost:5601`, la console affiche ses requêtes, et les effacer les perdrait. Utiliser alors un profil de navigateur dédié au laboratoire. À la première ouverture, la console contient un exemple de requête : le garder pour les captures de cette étape, puis l'effacer.

📸 `01-solr-admin.png`
- **Où** : http://localhost:8983/solr/#/ (*Dashboard*).
- **Visible** : les blocs *Instance*, *Versions* (`solr-spec` 10.0.0, `lucene-spec` 10.3.2) et le début du bloc *JVM* (version de Java).
- **Montre** : les versions du laboratoire.

📸 `01-kibana.png`
- **Où** : la console Dev Tools de Kibana, à sa première ouverture.
- **Visible** : l'exemple d'accueil de la console, tel quel.
- **Montre** : l'outil avec lequel on interroge Elasticsearch dans la suite.

📸 `01-dashboards.png`
- **Où** : la console Dev Tools de Dashboards, à sa première ouverture.
- **Visible** : l'exemple `GET _search`, tel quel.
- **Montre** : l'outil équivalent pour OpenSearch.

**Mes notes** : dans `notes/01-recherche-vectorielle.md`, section « Étape 1 : démarrer le laboratoire ».

---

## Étape 2 : des vecteurs à la main

**Objectif** : comprendre ce qu'est un embedding et ce que mesure la similarité.

**À faire** : regarder d'abord un vecteur brut, tel que TEI le renvoie.
```bash
curl -s localhost:8088/embed -H 'Content-Type: application/json' \
  -d '{"inputs": "query: fromage à pâte molle", "normalize": true}'
```
Puis comparer une requête à deux passages (`outils/similarites.py`, lancé dans le conteneur d'outils, demande les vecteurs à TEI et calcule les cosinus) :
```bash
make similarites
```
Refaire l'essai sans les préfixes `query:` et `passage:`, puis avec une requête sans aucun mot commun avec le passage :
```bash
make similarites T='"fromage à pâte molle" "Le camembert est un fromage à pâte molle et à croûte fleurie." "Jupiter est la plus grande planète du Système solaire."'
make similarites T='"query: spécialité normande au lait cru" "passage: Le camembert est un fromage à pâte molle et à croûte fleurie." "passage: Jupiter est la plus grande planète du Système solaire."'
```

**À observer**
- Un vecteur de 384 nombres, quelle que soit la longueur du texte.
- Le passage sur le camembert est plus proche de la requête que celui sur Jupiter… mais Jupiter obtient tout de même environ 0,77 : avec E5, les scores sont resserrés dans le haut de l'échelle. Seul le classement compte, pas la valeur absolue.
- Sans les préfixes, les écarts changent : E5 a été entraîné avec eux.

**Pourquoi** : le modèle projette un texte dans un espace où des sens proches donnent des vecteurs proches. Les vecteurs sont normalisés (norme 1) : le cosinus se réduit alors à un produit scalaire. La recherche vectorielle consiste à trouver les k vecteurs les plus proches de celui de la requête, sans mot commun nécessaire.

**Pourquoi 384 dimensions ?** Ce n'est pas une propriété des vecteurs en général : c'est la taille de sortie du modèle, fixée par son architecture. Les « petits » modèles (E5 small, MiniLM) produisent 384 dimensions, les modèles « base » 768, les « large » 1 024 ; les modèles d'OpenAI vont de 1 536 à 3 072. Plus de dimensions permettent de capter plus de nuances, mais coûtent plus en mémoire et en calcul. Conséquences pratiques :
- le champ vectoriel est déclaré avec la dimension exacte du modèle (étape 3) ;
- la requête et les documents doivent être vectorisés par le même modèle ;
- changer de modèle impose de tout revectoriser et réindexer.

📸 `02-similarites.png`
- **Où** : le terminal, après `clear`.
- **Visible** : les trois commandes `make similarites` de cette étape (avec préfixes, sans préfixes, sans mot commun) et leurs sorties, soit trois fois deux scores. Les lignes « Container … Creating/Created » peuvent rester.
- **Cadrage** : de la première commande à la dernière ligne de sortie ; aucune ligne coupée.
- **Montre** : le camembert est toujours plus proche que Jupiter, les scores E5 sont resserrés vers le haut, et les préfixes modifient les écarts.

**Mes notes** : dans `notes/01-recherche-vectorielle.md`, section « Étape 2 : des vecteurs à la main ».

---

## Étape 3 : déclarer un champ vectoriel dans chaque moteur

**Objectif** : voir comment chaque moteur décrit un champ vectoriel et quels choix il fait par défaut.

**À faire**

*Solr* (terminal) : créer la collection, puis le type et les champs par l'API Schema.
```bash
curl -s localhost:8983/api/collections -H 'Content-Type: application/json' \
  -d '{"name":"wikipedia","config":"_default","numShards":1,"replicationFactor":1}'

curl -s localhost:8983/solr/wikipedia/schema -H 'Content-Type: application/json' -d '{
  "add-field-type": {"name":"knn_vector_384", "class":"solr.DenseVectorField",
    "vectorDimension":384, "similarityFunction":"cosine",
    "knnAlgorithm":"hnsw", "hnswM":16, "hnswEfConstruction":100},
  "add-field": [
    {"name":"vecteur", "type":"knn_vector_384", "indexed":true, "stored":true},
    {"name":"titre", "type":"text_general", "multiValued":false},
    {"name":"texte", "type":"text_general", "multiValued":false},
    {"name":"theme", "type":"string"},
    {"name":"url", "type":"string", "indexed":false}]}'
```
Attention : l'adresse est `/solr/wikipedia/schema`. La même requête envoyée à l'API v2 `/api/collections/wikipedia/schema` répond sans erreur mais n'ajoute rien (constaté dans Solr 10.0.0).

*Elasticsearch* (console de Kibana) :
```
PUT wikipedia
{
  "mappings": {
    "properties": {
      "titre":   { "type": "text" },
      "texte":   { "type": "text" },
      "theme":   { "type": "keyword" },
      "url":     { "type": "keyword", "index": false },
      "vecteur": { "type": "dense_vector", "dims": 384, "similarity": "cosine" }
    }
  }
}

GET wikipedia/_mapping
```

*OpenSearch* (console de Dashboards) :
```
PUT wikipedia
{
  "settings": { "index.knn": true },
  "mappings": {
    "properties": {
      "titre":   { "type": "text" },
      "texte":   { "type": "text" },
      "theme":   { "type": "keyword" },
      "url":     { "type": "keyword", "index": false },
      "vecteur": { "type": "knn_vector", "dimension": 384, "space_type": "cosinesimil",
                   "method": { "name": "hnsw", "parameters": { "m": 16, "ef_construction": 100 } } }
    }
  }
}

GET wikipedia/_mapping
```

**À observer**
- Elasticsearch a complété le mapping : `index_options` de type `bbq_hnsw` avec `rescore_vector.oversample` à 3. Sans qu'on le demande, les vecteurs sont quantifiés en binaire (1 bit par dimension) et les meilleurs candidats sont recalculés avec les vecteurs complets. C'est le choix par défaut à partir de 384 dimensions ; en dessous, `int8_hnsw`.
- OpenSearch a choisi le moteur `faiss` (bibliothèque native C++), et non Lucene.
- Solr garde les vecteurs en `float` tant qu'on ne choisit pas un type quantifié (`ScalarQuantizedDenseVectorField`, `BinaryQuantizedDenseVectorField`, nouveaux en Solr 10).
- Les trois moteurs ont les mêmes réglages HNSW par défaut : 16 voisins par nœud du graphe (`hnswM`, `m`), 100 candidats à la construction (`hnswEfConstruction`, `ef_construction`).

**Pourquoi** : HNSW (Hierarchical Navigable Small World) est un graphe de voisinage parcouru de proche en proche : la recherche est approchée (elle peut manquer un voisin) mais rapide. Les trois moteurs partagent le principe ; ils diffèrent par le stockage des vecteurs et la quantification.

**La quantification en quelques mots** : stocker chaque nombre du vecteur sur moins de bits. Un `float` occupe 32 bits ; en `int8`, 8 bits (4 fois moins de mémoire) ; en `int4`, 4 bits (8 fois moins) ; en binaire, 1 bit, le seul signe du nombre (32 fois moins). On perd en précision : le score calculé sur les vecteurs quantifiés est approché. Pour compenser, le moteur prend plus de candidats que demandé (*oversample*), puis recalcule leur score avec les vecteurs complets (*rescoring*). BBQ (*Better Binary Quantization*) est la quantification binaire d'Elasticsearch, avec un oversample de 3 par défaut.

| Notion | Solr | Elasticsearch | OpenSearch |
|---|---|---|---|
| Type de champ | `solr.DenseVectorField` | `dense_vector` | `knn_vector` (+ `index.knn: true`) |
| Dimension | `vectorDimension` | `dims` | `dimension` |
| Similarité | `similarityFunction` : `cosine`, `dot_product`, `euclidean` | `similarity` : `cosine`, `dot_product`, `l2_norm`, `max_inner_product` | `space_type` : `cosinesimil`, `innerproduct`, `l2`… |
| HNSW | `hnswM`, `hnswEfConstruction` | `index_options.m`, `ef_construction` | `method.parameters.m`, `ef_construction` |
| Quantification par défaut | aucune | BBQ dès 384 dimensions | aucune (`compression_level` 1x) |
| Bibliothèque | Lucene | Lucene | Faiss (ou Lucene) |

📸 `03-es-mapping.png`
- **Où** : la console de Kibana.
- **Visible** : à gauche, la seule requête `GET wikipedia/_mapping` ; à droite, sa réponse, avec en entier le bloc du champ `vecteur` : `"type": "dense_vector"`, `"dims": 384`, `index_options` avec `"type": "bbq_hnsw"`, `m`, `ef_construction` et `rescore_vector.oversample: 3`.
- **Cadrage** : faire défiler la réponse si besoin pour que tout le bloc `vecteur` soit à l'écran.
- **Montre** : Elasticsearch a choisi seul la quantification BBQ.

📸 `03-os-mapping.png`
- **Où** : la console de Dashboards.
- **Visible** : à gauche, `GET wikipedia/_mapping` ; à droite, le bloc du champ `vecteur` en entier : `"type": "knn_vector"`, `"dimension": 384`, `method` avec `"engine": "faiss"`, `"space_type": "cosinesimil"`, `"name": "hnsw"` et ses paramètres.
- **Montre** : OpenSearch utilise Faiss par défaut.

📸 `03-solr-schema.png`
- **Où** : http://localhost:8983/solr/, menu de gauche : sélectionner la collection `wikipedia`, puis *Schema* ; dans la liste déroulante, choisir le champ `vecteur`.
- **Visible** : le champ `vecteur`, son type `knn_vector_384`, la classe `org.apache.solr.schema.DenseVectorField` et les cases *Indexed* et *Stored*. L'écran n'affiche pas les paramètres du type (dimension, similarité, HNSW) : ils sont dans la capture suivante.
- **Montre** : la déclaration du champ côté Solr.

📸 `03-solr-fieldtype.png`
- **Où** : le terminal, après `clear`.
- **Commande** : `curl -s localhost:8983/solr/wikipedia/schema/fieldtypes/knn_vector_384`
- **Visible** : la commande et la réponse complète : `class`, `vectorDimension` 384, `similarityFunction` cosine, `knnAlgorithm` hnsw, `hnswM` 16, `hnswEfConstruction` 100.
- **Montre** : les paramètres vectoriels de Solr, à comparer avec les deux mappings.

**Mes notes** : dans `notes/01-recherche-vectorielle.md`, section « Étape 3 : déclarer un champ vectoriel dans chaque moteur ».

---

## Étape 4 : indexer les mêmes vecteurs dans les trois moteurs

**Objectif** : indexer des vecteurs calculés hors du moteur, et regarder ce qu'ils coûtent.

**À faire**
```bash
make outils         # image des outils Python
make vectoriser     # 909 articles, environ une minute sur CPU
make indexer-tous   # ou un moteur à la fois : make indexer MOTEUR=solr
```
Le jeu de données (`donnees/wikipedia-fr.jsonl`) est fourni ; `make wikipedia` le reconstruit.

Puis comparer la place occupée :
```bash
curl -s "localhost:9200/_cat/indices/wikipedia?v&h=index,docs.count,store.size"
curl -s "localhost:9201/_cat/indices/wikipedia?v&h=index,docs.count,store.size"
curl -s "localhost:8983/solr/admin/cores?action=STATUS&wt=json" | grep -o '"size":"[^"]*"'
```
Dans Kibana, la vue détaillée par champ : `POST wikipedia/_disk_usage?run_expensive_tasks=true`.

**À observer**
- Combien de temps prend la vectorisation : c'est souvent l'étape la plus lente d'une chaîne d'indexation.
- La taille des index. Chez moi : Elasticsearch 2,2 Mo, OpenSearch 3,5 Mo, Solr 4 Mo, pour les mêmes 909 documents. Elasticsearch exclut les vecteurs de `_source` depuis la 9.2 ; OpenSearch les garde dans `_source` ; Solr les stocke parce que le champ est déclaré `stored`.
- La part du champ `vecteur` dans `_disk_usage` (Elasticsearch).
- Solr 10 n'expose plus ses métriques qu'au format Prometheus ou OpenMetrics (`/solr/admin/metrics`) : pour une taille d'index, l'état des cœurs est plus simple.
- 384 dimensions × 4 octets = 1,5 Ko par vecteur en `float`, avant toute quantification.

**Pourquoi** : la mémoire et le disque nécessaires aux vecteurs sont le premier poste de coût d'une recherche vectorielle ; on y reviendra dans l'article sur la quantification.

📸 `04-tailles.png`
- **Où** : le terminal, après `clear`.
- **Visible** : les trois commandes `curl` de mesure de cette étape et leurs sorties : `docs.count` 909 et `store.size` pour Elasticsearch puis OpenSearch, la taille de l'index pour Solr.
- **Cadrage** : de la première commande à la dernière ligne de sortie.
- **Montre** : la place occupée par les mêmes documents dans chaque moteur.

**Mes notes** : dans `notes/01-recherche-vectorielle.md`, section « Étape 4 : indexer les mêmes vecteurs dans les trois moteurs ».

---

## Étape 5 : interroger en kNN

**Objectif** : écrire une requête kNN dans chaque moteur et comparer les résultats.

**À faire** : obtenir le vecteur d'une requête, puis le coller dans chaque interface.
```bash
make -s vecteur Q="fromage à pâte molle" > /tmp/v.json                    # sur une ligne, pour curl
make -s vecteur Q="fromage à pâte molle" LIGNES=1 > /tmp/v-lignes.json    # un nombre par ligne, pour Dashboards
```
Pour que la requête reste lisible dans les consoles :
- **Kibana** : ouvrir le panneau *Variables* (en bas de la console), créer une variable `vecteur` et lui donner pour valeur le contenu de `/tmp/v.json` (ouvert dans l'éditeur de texte). Dans la requête, `"${vecteur}"` est remplacé par le tableau : les guillemets qui l'entourent sont retirés à l'envoi. Pour changer de requête, il suffit de modifier la variable. L'éditeur de la console de Kibana 9.3 ne permet pas de replier un tableau.
- **Dashboards** : coller le contenu de `/tmp/v-lignes.json` à la place de `[ …coller le vecteur… ]`, puis replier le tableau avec la flèche de la marge, sur la ligne qui l'ouvre. La console de Dashboards n'a pas de variables.

Le paramètre `filter_path` réduit la réponse aux scores et aux titres, pour voir les dix résultats d'un coup.

*Solr* (terminal ; dans l'interface, onglet *Query*, mettre la même chose dans `q`) :
```bash
curl -s localhost:8983/solr/wikipedia/select \
  --data-urlencode 'q={!knn f=vecteur topK=10}'"$(cat /tmp/v.json)" \
  --data-urlencode "fl=titre,theme,score" --data-urlencode "wt=csv"
```
`wt=csv` donne une ligne par document ; sans lui, la réponse est en JSON.

*Elasticsearch* (Kibana) :
```
POST wikipedia/_search?filter_path=hits.hits._score,hits.hits._source
{
  "knn": { "field": "vecteur", "query_vector": "${vecteur}", "k": 10, "num_candidates": 100 },
  "_source": ["titre", "theme"]
}
```

*OpenSearch* (Dashboards) :
```
POST wikipedia/_search?filter_path=hits.hits._score,hits.hits._source
{
  "query": { "knn": { "vecteur": { "vector": [ …coller le vecteur… ], "k": 10 } } },
  "_source": ["titre", "theme"]
}
```

Les trois à la fois, côte à côte :
```bash
make comparer Q="fromage à pâte molle"
make comparer Q="les violons fabriqués à Crémone"
make comparer Q="peintre de paysages norvégien"
```

**À observer**
- Les scores sont identiques d'un moteur à l'autre pour un même document : avec la similarité cosinus, les trois renvoient `(1 + cos) / 2`.
- « les violons fabriqués à Crémone » trouve les articles sur Stradivarius, sans mot commun : c'est l'apport de la recherche sémantique.
- Les trois moteurs ne remontent **pas toujours les mêmes documents** : la recherche est **approchée**. `make comparer` calcule aussi le vrai top k, par force brute (la requête comparée aux 909 vecteurs), et affiche le **rappel** de chaque moteur : la part de ce vrai top k qu'il a retrouvée ; un ✗ marque un document qui n'en fait pas partie, et les documents manqués sont listés. Chez moi, pour « les violons fabriqués à Crémone » :

  | Moteur | Rappel | Manqués | Cause |
  |---|---|---|---|
  | OpenSearch (Faiss, vecteurs `float`) | 10/10 | — | il examine `ef_search` = 100 candidats par défaut |
  | Solr (vecteurs `float`) | 8/10 | Rabâb égyptien, Vihuela | il parcourt le graphe HNSW avec seulement `topK` = 10 candidats |
  | Elasticsearch (BBQ) | 8/10 | Cymbale antique, Zurna | les candidats sont classés sur les vecteurs binaires, puis seuls 3 × 10 sont recalculés avec les vecteurs complets (`oversample` 3) |

  Le graphe HNSW étant construit avec une part de hasard, le résultat peut différer chez toi.
- Corriger chaque moteur, et constater que le bon réglage dépend de la cause (le vecteur de la requête dans `/tmp/v.json`, voir plus haut) :
  - Solr : ajouter `efSearchScaleFactor=2` (deux fois plus de candidats explorés) : 10/10.
    ```bash
    make -s vecteur Q="les violons fabriqués à Crémone" > /tmp/v.json
    curl -s localhost:8983/solr/wikipedia/select \
      --data-urlencode 'q={!knn f=vecteur topK=10 efSearchScaleFactor=2}'"$(cat /tmp/v.json)" \
      --data-urlencode "fl=titre,score" --data-urlencode "wt=csv"
    ```
  - Elasticsearch : passer `num_candidates` de 100 à 500 ne change rien (toujours 8/10), car la perte ne vient pas du parcours du graphe mais de la quantification ; ajouter `"rescore_vector": { "oversample": 10 }` dans le `knn` donne 10/10. Dans Kibana :
    ```
    POST wikipedia/_search?filter_path=hits.hits._score,hits.hits._source
    {
      "knn": { "field": "vecteur", "query_vector": "${vecteur}", "k": 10, "num_candidates": 100,
               "rescore_vector": { "oversample": 10 } },
      "_source": ["titre"]
    }
    ```
  - Une recherche **exacte** reste possible quand le corpus est petit ou très filtré : dans Elasticsearch, une requête `script_score` avec `cosineSimilarity` compare la requête à tous les documents (10/10, mais coût proportionnel au nombre de documents).
- Ce compromis rappel / temps de réponse se règle par moteur : `efSearchScaleFactor` (Solr), `num_candidates` et `oversample` (Elasticsearch), `ef_search` (OpenSearch). Sur 909 documents, l'écart de temps est invisible ; sur des millions de vecteurs, c'est le réglage principal.

📸 `05-solr-knn.png`
- **Où** : http://localhost:8983/solr/, collection `wikipedia`, *Query*.
- **Requête** : dans `q`, `{!knn f=vecteur topK=10}` suivi du vecteur de « fromage à pâte molle » (ouvrir `/tmp/v.json` dans l'éditeur de texte et copier son contenu) ; dans `fl`, `titre,theme,score` ; puis *Execute Query*.
- **Visible** : le formulaire (le champ `q` montre le début du vecteur, c'est normal) et, à droite, le début de la réponse avec les premiers documents (Époisses, Munster, Coulommiers…) et leurs scores.
- **Montre** : une requête kNN dans l'interface de Solr.

📸 `05-es-knn.png`
- **Où** : la console de Kibana.
- **Visible** : à gauche, la requête `POST wikipedia/_search?filter_path=…` avec `knn`, `"query_vector": "${vecteur}"`, `k`, `num_candidates` ; à droite, la réponse réduite par `filter_path` : les dix `_score` et `titre`.
- **Montre** : la même requête dans Elasticsearch.

📸 `05-os-knn.png`
- **Où** : la console de Dashboards.
- **Visible** : la requête `knn` avec `filter_path` et le vecteur replié à gauche (une seule ligne visible), les dix scores et titres à droite.
- **Montre** : la même requête dans OpenSearch.

📸 `05-comparer.png`
- **Où** : le terminal, après `clear`.
- **Visible** : `make comparer Q="les violons fabriqués à Crémone"` et sa sortie complète : le vrai top 10 (force brute), puis les listes de Solr, Elasticsearch et OpenSearch avec leur rappel, les ✗ et les documents manqués. Si la sortie dépasse la hauteur du terminal, faire deux captures : `05-comparer-1.png` (exact et Solr) et `05-comparer-2.png` (Elasticsearch et OpenSearch).
- **Montre** : la recherche trouve des documents sans mot commun avec la requête, et elle est approchée : chaque moteur peut manquer des voisins, pour des raisons différentes.

📸 `05-rappel-corrige.png`
- **Où** : le terminal, après `clear`.
- **Visible** : la commande `curl` Solr avec `efSearchScaleFactor=2` et sa réponse en CSV (dix lignes titre, score), où figurent Rabâb égyptien et Vihuela (ou les documents manqués chez toi).
- **Montre** : un réglage suffit à retrouver les voisins manqués.

**Mes notes** : dans `notes/01-recherche-vectorielle.md`, section « Étape 5 : interroger en kNN ».

---

## Étape 6 : filtrer

**Objectif** : comprendre la différence entre préfiltre et post-filtre, la question la plus fréquente en mission.

**À faire**
```bash
make comparer Q="fromage à pâte molle" THEME=vin
```
Le filtre `theme = vin` est appliqué en préfiltre dans les trois moteurs : `fq` pour Solr, `filter` dans le kNN pour Elasticsearch et OpenSearch.

Puis, dans Kibana, la même recherche avec un **post-filtre** :
```
POST wikipedia/_search?filter_path=hits.total,hits.hits._score,hits.hits._source
{
  "knn": { "field": "vecteur", "query_vector": "${vecteur}", "k": 10, "num_candidates": 100 },
  "post_filter": { "term": { "theme": "vin" } },
  "_source": ["titre", "theme"]
}
```
Et dans Solr, un `fq` exclu du préfiltre :
```bash
curl -s localhost:8983/solr/wikipedia/select \
  --data-urlencode 'q={!knn f=vecteur topK=10 excludeTags=t}'"$(cat /tmp/v.json)" \
  --data-urlencode 'fq={!tag=t}theme:vin' --data-urlencode "fl=titre,theme,score" --data-urlencode "wt=csv"
```

**À observer**
- Avec le préfiltre : dix résultats, tous du thème « vin », les plus proches de « fromage » parmi eux. Elasticsearch peut encore manquer un document à cause de la quantification BBQ (étape 5).
- Les scores restent élevés (autour de 0,90) alors que les cépages n'ont rien à voir avec le fromage : avec E5, les scores sont resserrés dans le haut de l’échelle (étape 2), seul l'ordre compte.
- Avec le post-filtre : on cherche d'abord les dix plus proches dans tout l'index (des fromages), puis on retire ceux qui ne sont pas du thème « vin » : il ne reste aucun résultat, dans Elasticsearch comme dans Solr.

**Pourquoi** : un post-filtre ne fait que retirer des résultats déjà choisis. Le préfiltre restreint le graphe parcouru ; quand le filtre est très sélectif, les moteurs passent à une recherche exacte sur les documents filtrés (Elasticsearch, OpenSearch) ou à une stratégie adaptée (ACORN dans Solr 10, paramètre `filteredSearchThreshold`).

📸 `06-prefiltre.png`
- **Où** : le terminal, après `clear`.
- **Visible** : `make comparer Q="fromage à pâte molle" THEME=vin` et sa sortie complète : la liste exacte puis celles de Solr, d'Elasticsearch et d'OpenSearch, dix cépages chacune.
- **Cadrage** : la sortie fait une soixantaine de lignes ; agrandir le terminal (ou réduire la police) pour que la liste d'OpenSearch soit visible.
- **Montre** : avec un préfiltre, on obtient toujours dix résultats, tous du thème demandé.

📸 `06-postfiltre-es.png`
- **Où** : la console de Kibana.
- **Visible** : à gauche, la requête avec `knn` (`"query_vector": "${vecteur}"`) et `post_filter` ; à droite, la réponse réduite par `filter_path` : `"total": { "value": 0, … }` et aucun document.
- **Montre** : un post-filtre peut ne laisser aucun résultat.

**Mes notes** : dans `notes/01-recherche-vectorielle.md`, section « Étape 6 : filtrer ».

---

## Étape 7 : vectoriser dans le moteur lui-même

**Objectif** : laisser le moteur calculer les vecteurs, et voir ce que chacun permet, gratuitement ou non.

### Elasticsearch : `semantic_text`

```
GET _license
GET _inference/_all

PUT wikipedia-semantique
{
  "mappings": { "properties": {
    "titre": { "type": "text" },
    "contenu": { "type": "semantic_text", "inference_id": ".multilingual-e5-small-elasticsearch" } } }
}

PUT wikipedia-semantique/_doc/1
{ "titre": "Camembert", "contenu": "Le camembert est un fromage à pâte molle et à croûte fleurie." }
```
**À observer** : la licence est `basic` ; l'index se crée, mais l'indexation est refusée (`current license is non-compliant for [inference]`, code 403). Toute l'API Inference, y compris les modèles intégrés au cluster (E5, ELSER), demande une licence Enterprise.

Activer l'essai de 30 jours, puis recommencer :
```
POST _license/start_trial?acknowledge=true

PUT wikipedia-semantique/_doc/1
{ "titre": "Camembert", "contenu": "Le camembert est un fromage à pâte molle et à croûte fleurie." }

PUT wikipedia-semantique/_doc/2
{ "titre": "Jupiter", "contenu": "Jupiter est la plus grande planète du Système solaire." }

GET wikipedia-semantique/_search
{ "query": { "match": { "contenu": "spécialité normande au lait cru" } } }

GET wikipedia-semantique/_mapping
```
**À observer** : le premier document met une vingtaine de secondes (téléchargement et déploiement du modèle dans le cluster). Une simple requête `match` devient sémantique. Le mapping montre les réglages déduits du modèle (384 dimensions, cosinus).

📸 `07-es-licence-refus.png`
- **Où** : la console de Kibana, licence `basic`.
- **Visible** : à gauche, `PUT wikipedia-semantique/_doc/1` et son document ; à droite, la réponse d'erreur avec `"status": 403` et le message `current license is non-compliant for [inference]`.
- **Montre** : `semantic_text` demande une licence payante.
- **Si l'essai est déjà activé** : prendre d'abord `07-es-semantic.png`, puis revenir à la licence gratuite (`POST _license/start_basic?acknowledge=true`) et rejouer `PUT wikipedia-semantique/_doc/1`. L'essai ne s'active qu'une fois par cluster : pour le retrouver, remettre Elasticsearch seul à zéro (`make reset-moteur MOTEUR=elasticsearch`, qui redémarre aussi Kibana), puis reprendre l'étape 7, qui n'utilise que l'index `wikipedia-semantique`. Avant l'étape 8, recréer l'index `wikipedia` (`PUT wikipedia` de l'étape 3) et le remplir (`make indexer MOTEUR=elasticsearch`). Solr, OpenSearch, les variables de la console et les captures déjà prises ne sont pas touchés.

📸 `07-es-semantic.png`
- **Où** : la console de Kibana, après activation de l'essai.
- **Visible** : à gauche, `GET wikipedia-semantique/_search` avec `match` sur « spécialité normande au lait cru » ; à droite, les deux documents, le camembert en premier, avec leurs `_score`.
- **Montre** : une simple requête `match` devient sémantique.

### OpenSearch : modèle préentraîné et champ `semantic`

```
PUT _cluster/settings
{ "persistent": { "plugins.ml_commons.only_run_on_ml_node": "false",
                  "plugins.ml_commons.native_memory_threshold": "99" } }

POST _plugins/_ml/models/_register
{ "name": "huggingface/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
  "version": "1.0.2", "model_format": "TORCH_SCRIPT" }

GET _plugins/_ml/tasks/<task_id>
POST _plugins/_ml/models/<model_id>/_deploy
GET _plugins/_ml/tasks/<task_id du déploiement>

PUT wikipedia-semantique
{ "settings": { "index.knn": true },
  "mappings": { "properties": {
    "titre": { "type": "text" },
    "contenu": { "type": "semantic", "model_id": "<model_id>" } } } }

PUT wikipedia-semantique/_doc/1
{ "titre": "Camembert", "contenu": "Le camembert est un fromage à pâte molle et à croûte fleurie." }

PUT wikipedia-semantique/_doc/2
{ "titre": "Jupiter", "contenu": "Jupiter est la plus grande planète du Système solaire." }

GET wikipedia-semantique/_search
{ "_source": { "excludes": ["contenu_semantic_info"] },
  "query": { "neural": { "contenu": { "query_text": "spécialité normande au lait cru" } } } }

GET wikipedia-semantique/_mapping
```
**À observer** : tout est gratuit. Le modèle est enregistré puis déployé dans le cluster, deux étapes asynchrones suivies par des tâches. Le champ `semantic` crée lui-même un `knn_vector` (`contenu_semantic_info.embedding`). Le modèle multilingue préentraîné n'est pas E5 : la liste d'OpenSearch propose `paraphrase-multilingual-MiniLM-L12-v2`.

Deux pièges rencontrés en montant ce laboratoire :
- avec 1 Go de tas, le déploiement échoue (« Memory Circuit Breaker is open ») : le laboratoire donne 2 Go à OpenSearch ;
- sans la variable `LD_PRELOAD` du `docker-compose.yml`, le nœud s'arrête à la première écriture dans un champ vectoriel une fois le modèle chargé : ml-commons charge le `libstdc++` ancien de PyTorch, puis la bibliothèque Faiss du plugin k-NN n'y trouve pas `GLIBCXX_3.4.20`.

📸 `07-os-modele.png`
- **Où** : la console de Dashboards.
- **Visible** : à gauche, `GET _plugins/_ml/tasks/<task_id du déploiement>` ; à droite, la réponse avec `"task_type": "DEPLOY_MODEL"` et `"state": "COMPLETED"`.
- **Montre** : le modèle tourne dans le cluster OpenSearch.

📸 `07-os-semantic.png`
- **Où** : la console de Dashboards.
- **Visible** : à gauche, la requête `neural` sur « spécialité normande au lait cru » ; à droite, les deux documents, le camembert en premier, avec leurs `_score`.
- **Montre** : la même recherche sémantique, gratuite, dans OpenSearch.

### Solr : le module `language-models`

Le module est activé par `SOLR_MODULES=language-models` dans le `docker-compose.yml`. Il appelle un service d'embeddings par HTTP (via LangChain4j) ; ici, TEI, par son API compatible OpenAI.

```bash
# 1. Déclarer le parseur de requête : c'est lui qui crée le magasin de modèles
curl -s localhost:8983/solr/wikipedia/config -H 'Content-Type: application/json' -d '{
  "add-queryparser": {"name":"knn_text_to_vector",
    "class":"org.apache.solr.languagemodels.textvectorisation.search.TextToVectorQParserPlugin"}}'

# 2. Enregistrer le modèle (TEI vu comme un service OpenAI)
curl -s -X PUT localhost:8983/solr/wikipedia/schema/text-to-vector-model-store -H 'Content-Type: application/json' -d '{
  "class":"dev.langchain4j.model.openai.OpenAiEmbeddingModel", "name":"e5-tei",
  "params":{"baseUrl":"http://tei:80/v1", "apiKey":"inutile", "modelName":"multilingual-e5-small",
            "timeout":60, "maxRetries":2}}'

# 3. Rechercher avec du texte
curl -s localhost:8983/solr/wikipedia/select \
  --data-urlencode 'q={!knn_text_to_vector model=e5-tei f=vecteur topK=10}query: spécialité normande au lait cru' \
  --data-urlencode 'fl=titre,theme,score'
```
**À observer**
- L'ordre compte : si le modèle est envoyé avant la déclaration du parseur, Solr répond par une erreur 500 (`ClassCastException`), car le magasin de modèles n'existe pas encore.
- Le préfixe E5 `query:` se met dans le texte de la requête : Solr transmet le texte tel quel.
- Solr ne fait pas tourner de modèle lui-même : il appelle un service. Le guide de Solr qualifie le module d'expérimental.

📸 `07-solr-texte.png`
- **Où** : http://localhost:8983/solr/, collection `wikipedia`, *Query*.
- **Requête** : dans `q`, `{!knn_text_to_vector model=e5-tei f=vecteur topK=10}query: spécialité normande au lait cru` ; dans `fl`, `titre,theme,score` ; puis *Execute Query*.
- **Visible** : le formulaire, avec la requête en texte lisible, et le début de la réponse : les premiers fromages et leurs scores.
- **Montre** : Solr vectorise lui-même la requête, en appelant TEI.

| | Solr 10.0 | Elasticsearch 9.3 | OpenSearch 3.5 |
|---|---|---|---|
| Où tourne le modèle | service externe (OpenAI, Hugging Face, Mistral, Cohere, ou compatible) | dans le cluster (E5, ELSER) ou service externe | dans le cluster (modèles préentraînés) ou connecteur externe |
| Champ « tout-en-un » | non (processeur d'indexation + parseur) | `semantic_text` | `semantic` |
| Licence | gratuit | Enterprise (ou essai) | gratuit |
| Statut | expérimental | GA | GA |

**Mes notes** : dans `notes/01-recherche-vectorielle.md`, section « Étape 7 : vectoriser dans le moteur lui-même ».

---

## Étape 8 : le dimensionnement en un coup d'œil

**Objectif** : estimer la mémoire nécessaire aux vecteurs.

**À faire**
- Calcul : nombre de vecteurs × dimensions × octets par dimension. En `float` : 1 million × 384 × 4 = 1,5 Go, plus le graphe HNSW (environ 4 × m octets par vecteur selon la documentation d'Elasticsearch, soit 64 Mo pour m = 16).
- Dans Kibana : `POST wikipedia/_disk_usage?run_expensive_tasks=true`, partie `vecteur`.

**À observer** : avec BBQ, Elasticsearch garde en mémoire environ 32 fois moins de données pour la recherche dans le graphe, et relit les vecteurs complets pour recalculer le score des meilleurs candidats (`oversample` 3).

**Pourquoi** : les vecteurs doivent tenir en mémoire (cache du système) pour une recherche rapide. Le détail, et la comparaison avec la quantification de Solr et d'OpenSearch, feront l'objet de l'article sur la quantification.

**Mes notes** : dans `notes/01-recherche-vectorielle.md`, section « Étape 8 : le dimensionnement en un coup d'œil ».

---

## Étape 9 : bilan

Questions pour l'article :
- Quel moteur a été le plus simple à mettre en œuvre, et pourquoi ?
- Qu'est-ce qui est gratuit, expérimental, ou soumis à licence ?
- Quels pièges as-tu rencontrés ?
- Dans quel cas recommanderais-tu chacun des trois ?

**Mes notes** : dans `notes/01-recherche-vectorielle.md`, section « Étape 9 : bilan ».

---

## Remettre le laboratoire à zéro

```bash
make reset
```
La cible demande confirmation, arrête la stack et supprime les volumes des trois moteurs. Le volume `search-vector-lab_tei-cache` garde le modèle de TEI, pour ne pas le télécharger de nouveau (`make reset-tout` le supprime aussi). Pour un seul moteur : `make reset-moteur MOTEUR=<solr|elasticsearch|opensearch>`.
