# Comment contribuer

Différents types de contribution sont utiles à ce dépôt, selon vos compétences et envies. Ci-dessous quelques suggestions de contribution, mais tout autre contribution est également bienvenue.

Nous sommes ouverts aux pull requests.

## Contribuer comme développeur

**Piste possible**: vous pouvez proposer une API REST prête au déploiement, ou des interface utilisateurs (front-end) de recherche, ou encore ajouter d'autres sources de données (open data) en plus de SIRENE
**Mode de contribution** : github issue et pull request

## Contribuer comme data engineer / data scientist

La création de l'index Elasticsearch et de la base de données tampon SQLite s'appuie sur le code de l'[annuaire des entreprises](https://github.com/etalab/annuaire-entreprises-search-infra). /Les fichiers sont dans le dossier [indexation/](indexation/)

**Piste possible** : vous pouvez travailler sur l'analyzer Elasticsearch, ou proposer des poids finetunés sur un jeu de données (dans ce cas, indiquer le jeu de données utilisé dans le [ficher des données](data_sources.txt)), ou encore ajouter d'autres sources de données (open data) en plus de SIRENE
**Mode de contribution** : github issue et pull request

## Contribuer comme utilisateur métier

**Piste possible** : faire des retours d'utilisation, sur la prise en main de l'outil, ses résultats, les fonctionnalités manquantes, suggérer d'autres sources de données open data supplémentaires, etc.
**Mode de contribution **: ouvrir une github issue décrivant précisément vos difficultés, bugs ou propositions de fonctionnalités

# Maintenance du dépôt

La maintenance du projet est assuré par
- Geoffrey ALDEBERT : notamment sur l'indexation des données SIRENE géolocalisées
- Pierre-Etienne DEVINEAU : notamment sur la recherche d'établissements

Le code source s'appuie également sur les développements pour l'annuaire entreprise de Hajar AIT EL KADI.
