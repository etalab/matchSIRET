# matchSIRET

Ce dépôt propose un code pour créer et alimenter un index Elasticsearch avec les données [base SIRENE de l'INSEE, après géolocalisation par Etalab](https://files.data.gouv.fr/geo-sirene/), ainsi que pour faire des recherches d'établissements sur cet index Elasticsearch. Le dépôt comprend aussi une liste de quelques sources de données en open data comprenant des libellés d'entreprise

Le code source a été conçu pour être compatible avec l'outil [Onyxia](https://github.com/InseeFrLab/onyxia-web) développé par l'INSEE avec le soutien d'Etalab, mais fonctionne également sans Onyxia.

## Pré-requis

Le service utilise un service Elasticsearch ([à partir de cette image](https://git.lab.sspcloud.fr/hby7ih/matchsiretimage)), Python3.10 et les bibliothèques Python indiquées dans [requirements.txt](requirements.txt). L'utilisation de JupyterLab en plus de Python est facultatif.

## Déployer matchSIRET sur une instance Onyxia

1) Créer un service Elasticsearch [en indiquant le chemin de cette image](https://git.lab.sspcloud.fr/hby7ih/matchsiretimage) (tag:latest)
2) Créer un service JupyterLab [en indiquant le chemin du fichier d'initialisation](https://raw.githubusercontent.com/etalab/matchSIRET/main/init.sh). Des modifications du fichier d'intialisation, et notamment des chemins, peuvent être utiles selon votre version d'Onyxia.
3) Dans JupyterLab, ouvrir le fichier `indexation/indexation.ipynb`, indiquer l'url de votre service Elasticsearch (qui figure dans le "README" de votre service Elastic dans votre compte sur Onyxia) dans la cellule correspondante, et exécuter l'ensemble des cellules (ce processus prend plusieurs heures)

## Déployer sans Onyxia

1) Créer un service Elasticsearch [en indiquant le chemin de cette image](https://git.lab.sspcloud.fr/hby7ih/matchsiretimage) (tag:latest) avec des volumes permanents. Pour télécharger Elasticsearch et déployer une instance locale, vous pouvez suivre [la procédure de la documentation Elastic](https://www.elastic.co/guide/en/elasticsearch/reference/current/setup.html)
2) Clôner ce dépôt matchSIRET, et installer les dépendances Python3.10 dans un environnement virtuel
3) Ouvrir le fichier `indexation/indexation.ipynb`, indiquer l'url de votre service Elasticsearch dans la cellule correspondante, et exécuter l'ensemble des cellules (ce processus prend plusieurs heures)

## Envoyer des requêtes à cette instance Elasticsearch

L'index Elasticsearch créé et rempli précédemment s'appuie sur un stockage permanent (qui ne disparaît pas avec la fermeture du service Elastic). On peut y effectuer des recherches avec les fonctions utilitaires du fichier `queries.py` qui s'appuient sur les structure de données `WorkSite` et `GeoWorkSite` de `worksites.py`

## Coment contribuer

Voir le [guide de contribution](CONTRIBUTING.md)

## Méthodologie 

La méthodologie d'avant-projet est décrite isur le [wiki du programme 10%]((https://github.com/etalab-ia/programme10pourcent/wiki/Ateliers-SIRETisation) 

## Contact

La maintenance est effectué par Etalab, au sein de la Direction interministérielle du numérique

[lab-ia@data.gouv.fr](mailto:lab-ia@data.gouv.fr)

