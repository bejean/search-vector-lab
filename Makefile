# Makefile du laboratoire de recherche vectorielle
# Lancer `make` ou `make help` pour afficher l'aide générée par sections.

# Couleurs pour l'affichage
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

DOCKER_COMPOSE = docker compose
OUTILS = $(DOCKER_COMPOSE) run --rm outils python
# Machine qui publie les ports (depuis un conteneur : HOTE=host.docker.internal)
HOTE ?= localhost
VOLUMES_MOTEURS = search-vector-lab_solr-data search-vector-lab_es-data search-vector-lab_os-data

.DEFAULT_GOAL := help
.PHONY: help up down restart ps logs status \
	outils wikipedia vectoriser indexer indexer-tous importer-crawl \
	vecteur comparer reset reset-tout

help: ## Affiche cette aide
	@awk 'BEGIN {FS = ":.*?## "; printf "\n$(GREEN)Commandes disponibles:$(NC)\n"} \
		/^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5); next } \
		/^[a-zA-Z_-]+:.*?## / { printf "  $(GREEN)%-18s$(NC) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

##@ 🚀 Stack Docker
up: ## Démarre la stack (Solr, Elasticsearch, Kibana, OpenSearch, Dashboards, TEI)
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✅ Stack démarrée ; Kibana et Dashboards répondent une à deux minutes plus tard (make status)$(NC)"

down: ## Arrête la stack (les données sont gardées)
	$(DOCKER_COMPOSE) down

restart: ## Redémarre la stack, ou un service (ex : make restart SERVICE=opensearch)
	$(DOCKER_COMPOSE) restart $(SERVICE)

ps: ## Liste les services et leur état
	$(DOCKER_COMPOSE) ps

logs: ## Suit les journaux de la stack, ou d'un service (ex : make logs SERVICE=solr)
	$(DOCKER_COMPOSE) logs -f --tail=100 $(SERVICE)

status: ## Vérifie que chaque service répond (codes HTTP)
	@for s in "Solr|http://$(HOTE):8983/solr/admin/info/system" \
		"Elasticsearch|http://$(HOTE):9200" \
		"Kibana|http://$(HOTE):5601/api/status" \
		"OpenSearch|http://$(HOTE):9201" \
		"Dashboards|http://$(HOTE):5602/api/status" \
		"TEI|http://$(HOTE):8088/health"; do \
		nom=$${s%%|*}; url=$${s#*|}; \
		code=$$(curl -s -o /dev/null -w '%{http_code}' "$$url"); \
		if [ "$$code" = 200 ]; then printf "  $(GREEN)%-14s %s$(NC)\n" "$$nom" "$$code"; \
		else printf "  $(RED)%-14s %s$(NC)\n" "$$nom" "$$code"; fi; \
	done

##@ 📚 Données et indexation
outils: ## Construit l'image des outils Python
	$(DOCKER_COMPOSE) --profile outils build outils

wikipedia: ## Reconstruit le jeu de données Wikipédia (plusieurs minutes, débit limité par Wikipédia)
	$(OUTILS) outils/telecharger_wikipedia.py

vectoriser: ## Calcule les embeddings (ex : make vectoriser FICHIER=donnees/crawl-x.jsonl ; défaut : Wikipédia)
	$(OUTILS) outils/vectoriser.py $(FICHIER)

indexer: ## Indexe dans un moteur (ex : make indexer MOTEUR=solr [FICHIER=… INDEX=…])
	@if [ -z "$(MOTEUR)" ]; then \
		echo "$(RED)❌ Usage : make indexer MOTEUR=<solr|elasticsearch|opensearch> [FICHIER=donnees/…-vecteurs.jsonl INDEX=nom]$(NC)"; \
		exit 1; \
	fi
	$(OUTILS) outils/indexer.py $(MOTEUR) $(FICHIER) $(INDEX)

indexer-tous: ## Indexe dans les trois moteurs (défaut : Wikipédia, index wikipedia)
	$(OUTILS) outils/indexer.py solr $(FICHIER) $(INDEX)
	$(OUTILS) outils/indexer.py elasticsearch $(FICHIER) $(INDEX)
	$(OUTILS) outils/indexer.py opensearch $(FICHIER) $(INDEX)

importer-crawl: ## Importe un corpus crawlé, sur l'hôte (ex : make importer-crawl DOSSIER=… THEME=… [MAX=500])
	@if [ -z "$(DOSSIER)" ]; then \
		echo "$(RED)❌ Usage : make importer-crawl DOSSIER=<dossier du crawl> [THEME=nom] [MAX=N]$(NC)"; \
		exit 1; \
	fi
	python3 outils/importer_crawl.py "$(DOSSIER)" $(if $(THEME),--theme "$(THEME)") $(if $(MAX),--max $(MAX))

##@ 🔎 Recherche
vecteur: ## Affiche le vecteur d'une requête (ex : make vecteur Q="fromage à pâte molle" > /tmp/v.json)
	@if [ -z "$(Q)" ]; then echo "$(RED)❌ Usage : make vecteur Q=\"texte\"$(NC)" >&2; exit 1; fi
	@$(OUTILS) outils/vecteur_requete.py "$(Q)"

comparer: ## Même kNN sur les trois moteurs (ex : make comparer Q="fromage" [K=10] [THEME=vin])
	@if [ -z "$(Q)" ]; then echo "$(RED)❌ Usage : make comparer Q=\"texte\" [K=10] [THEME=nom]$(NC)"; exit 1; fi
	@$(OUTILS) outils/comparer.py "$(Q)" $(or $(K),10) $(THEME)

##@ 🧹 Remise à zéro
reset: ## Arrête la stack et supprime les données des moteurs (garde le modèle de TEI)
	@printf "$(RED)⚠️  Supprimer les index, collections, modèles et licences des trois moteurs ? [o/N] $(NC)"; \
	read r; [ "$$r" = o ] || { echo "Abandon."; exit 1; }
	$(DOCKER_COMPOSE) down
	-docker volume rm $(VOLUMES_MOTEURS)
	@echo "$(GREEN)✅ Laboratoire remis à zéro (make up pour repartir)$(NC)"

reset-tout: ## Comme reset, et supprime aussi le modèle téléchargé par TEI
	@printf "$(RED)⚠️  Tout supprimer, y compris le cache du modèle de TEI ? [o/N] $(NC)"; \
	read r; [ "$$r" = o ] || { echo "Abandon."; exit 1; }
	$(DOCKER_COMPOSE) down -v
	@echo "$(GREEN)✅ Tous les volumes supprimés$(NC)"
