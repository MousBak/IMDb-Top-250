# IMDb Top 250 - Scraping et application Streamlit

> Web Scraping / Data App

## Vue d'ensemble

Projet de scraping IMDb avec application Streamlit. Le code principal est situé dans le sous-dossier imdbSraper/ et permet d'extraire, explorer ou afficher des informations liées au classement IMDb Top 250.

## Objectifs du projet

- Collecter des informations depuis IMDb.
- Structurer les données extraites.
- Présenter les résultats dans une interface Streamlit.
- Préparer un socle de data app pour l’exploration de films.

## Démarche

- Scraping via scripts Python.
- Tests et debug avec fichier HTML local.
- Application Streamlit pour la restitution.
- Organisation des dépendances dans requirements.txt.

## Stack technique

- Python
- Streamlit
- Web Scraping
- BeautifulSoup/Scraping
- HTML

## Structure du dépôt

- `imdbSraper/README.md`
- `imdbSraper/app.py`
- `imdbSraper/app_streamlit.py`
- `imdbSraper/database/mongo.py`
- `imdbSraper/imdb_debug.html`
- `imdbSraper/main.py`
- `imdbSraper/requirements.txt`
- `imdbSraper/scraper/imdb_scraper.py`
- `imdbSraper/templates/index.html`
- `imdb_debug.html`

## Lancer ou consulter le projet

```bash
cd imdbSraper
pip install -r requirements.txt
streamlit run app_streamlit.py
```

## Compétences démontrées

- Extraction web.
- Structuration de données web.
- Création d’interface Streamlit.
- Debug de pages HTML.

## Pistes d'amélioration

- Corriger le nom du dossier imdbSraper en imdbScraper.
- Ajouter une capture de l’application.
- Ajouter un export CSV des résultats.

## Auteur

**Bakayoko Moussa**  
Data Analyst / BI Analyst / Analytics Engineering Jr  
Portfolio : https://mousbak.github.io/  
GitHub : https://github.com/MousBak
