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
VOLUME_solr = solr-data
VOLUME_elasticsearch = es-data
VOLUME_opensearch = os-data
INTERFACE_elasticsearch = kibana
INTERFACE_opensearch = opensearch-dashboards

.DEFAULT_GOAL := help
.PHONY: help up down restart ps logs status \
	outils wikipedia vectoriser indexer indexer-tous importer-crawl \
	similarites vecteur comparer reset reset-moteur reset-tout notes

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

importer-crawl: ## Importe un corpus crawlé (ex : make importer-crawl DOSSIER=… THEME=… [MAX=500])
	@if [ -z "$(DOSSIER)" ]; then \
		echo "$(RED)❌ Usage : make importer-crawl DOSSIER=<dossier du crawl> [THEME=nom] [MAX=N]$(NC)"; \
		exit 1; \
	fi
	$(DOCKER_COMPOSE) run --rm -v "$(abspath $(DOSSIER)):/crawl:ro" outils python outils/importer_crawl.py /crawl \
		--nom "$(notdir $(patsubst %/,%,$(DOSSIER)))" $(if $(THEME),--theme "$(THEME)") $(if $(MAX),--max $(MAX))

##@ 🔎 Recherche
similarites: ## Similarité cosinus entre textes via TEI (ex : make similarites T='"query: …" "passage: …"')
	@$(OUTILS) outils/similarites.py $(T)

vecteur: ## Vecteur d'une requête (ex : make -s vecteur Q="fromage" > /tmp/v.json ; LIGNES=1 : un nombre par ligne)
	@if [ -z "$(Q)" ]; then echo "$(RED)❌ Usage : make vecteur Q=\"texte\" [LIGNES=1]$(NC)" >&2; exit 1; fi
	@$(OUTILS) outils/vecteur_requete.py "$(Q)" $(if $(LIGNES),--lignes)

comparer: ## Même kNN sur les trois moteurs (ex : make comparer Q="fromage" [K=10] [THEME=vin])
	@if [ -z "$(Q)" ]; then echo "$(RED)❌ Usage : make comparer Q=\"texte\" [K=10] [THEME=nom]$(NC)"; exit 1; fi
	@$(OUTILS) outils/comparer.py "$(Q)" $(or $(K),10) $(THEME)

##@ 📝 Notes
notes: ## Crée le fichier de notes personnelles du parcours 1, s'il n'existe pas (notes/, ignoré par Git)
	@mkdir -p notes
	@if [ -e notes/01-recherche-vectorielle.md ]; then echo "notes/01-recherche-vectorielle.md existe déjà"; \
	else cp parcours/01-notes-modele.md notes/01-recherche-vectorielle.md && echo "$(GREEN)✅ notes/01-recherche-vectorielle.md créé$(NC)"; fi

##@ 🧹 Remise à zéro
reset: ## Arrête la stack et supprime les données des moteurs (garde le modèle de TEI)
	@printf "$(RED)⚠️  Supprimer les index, collections, modèles et licences des trois moteurs ? [o/N] $(NC)"; \
	read r; [ "$$r" = o ] || { echo "Abandon."; exit 1; }
	$(DOCKER_COMPOSE) down
	-docker volume rm $(VOLUMES_MOTEURS)
	@echo "$(GREEN)✅ Laboratoire remis à zéro (make up pour repartir)$(NC)"

reset-moteur: ## Supprime les données d'un seul moteur et le redémarre (ex : make reset-moteur MOTEUR=elasticsearch)
	@case "$(MOTEUR)" in solr|elasticsearch|opensearch) ;; \
		*) echo "$(RED)❌ Usage : make reset-moteur MOTEUR=<solr|elasticsearch|opensearch>$(NC)"; exit 1;; esac
	@printf "$(RED)⚠️  Supprimer les données de $(MOTEUR) (index, modèles, licence) ? [o/N] $(NC)"; \
	read r; [ "$$r" = o ] || { echo "Abandon."; exit 1; }
	$(DOCKER_COMPOSE) rm -sf $(MOTEUR)
	docker volume rm search-vector-lab_$(VOLUME_$(MOTEUR))
	$(DOCKER_COMPOSE) up -d $(MOTEUR)
	$(if $(INTERFACE_$(MOTEUR)),$(DOCKER_COMPOSE) restart $(INTERFACE_$(MOTEUR)))
	@echo "$(GREEN)✅ $(MOTEUR) remis à zéro ; recréer l'index (étape 3 du parcours), puis make indexer MOTEUR=$(MOTEUR)$(NC)"

reset-tout: ## Comme reset, et supprime aussi le modèle téléchargé par TEI
	@printf "$(RED)⚠️  Tout supprimer, y compris le cache du modèle de TEI ? [o/N] $(NC)"; \
	read r; [ "$$r" = o ] || { echo "Abandon."; exit 1; }
	$(DOCKER_COMPOSE) down -v
	@echo "$(GREEN)✅ Tous les volumes supprimés$(NC)"
