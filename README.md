# matchSIRET

Ce dépôt propose un code pour créer et alimenter un index Elasticsearch avec les données [base SIRENE de l'INSEE, après géolocalisation par Etalab](https://files.data.gouv.fr/geo-sirene/), ainsi que pour faire des recherches d'établissements sur cet index Elasticsearch. Le dépôt comprend aussi une liste de quelques sources de données en open data comprenant des libellés d'entreprise

Le code source a été conçu pour être compatible avec l'outil [Onyxia](https://github.com/InseeFrLab/onyxia-web) développé par l'INSEE avec le soutien d'Etalab, mais fonctionne également sans Onyxia.

## Pré-requis

Le service utilise un service Elasticsearch ([à partir de cette image](https://git.lab.sspcloud.fr/hby7ih/matchsiretimage)), Python3.10 et les bibliothèques Python indiquées dans [requirements.txt](requirements.txt). L'utilisation de JupyterLab en plus de Python est facultatif.
Les données proviennent de SIRENE et sont géolocalisées par ETALAB (https://files.data.gouv.fr/geo-sirene/last/). Elles sont [en libre accès et rafraichies chaque mois par Etalab](https://files.data.gouv.fr/geo-sirene/last/)

## Déployer matchSIRET ***avec*** Onyxia

1) Créer un service Elasticsearch [en indiquant le chemin de cette image](https://git.lab.sspcloud.fr/hby7ih/matchsiretimage) (dans le formulaire: Dépendance ElasticSearch, Image:  `git-registry.lab.sspcloud.fr/hby7ih/matchsiretimage`, ImageTag: `latest`)
2) Créer un service JupyterLab [en indiquant le chemin du fichier d'initialisation](https://raw.githubusercontent.com/etalab/matchSIRET/main/init.sh). Des modifications du fichier d'intialisation, et notamment des chemins, peuvent être utiles selon votre version d'Onyxia.
3) Dans JupyterLab, ouvrir le fichier `indexation/indexation.ipynb`, indiquer l'url de votre service Elasticsearch (qui figure dans le "README" de votre service Elastic dans votre compte sur Onyxia) dans la cellule correspondante, et exécuter l'ensemble des cellules (ce processus prend plusieurs heures)

## Déployer matchSIRET ***sans*** Onyxia

1) Créer un service Elasticsearch [en indiquant le chemin de cette image](https://git.lab.sspcloud.fr/hby7ih/matchsiretimage) (tag:latest) avec des volumes permanents. Pour télécharger Elasticsearch et déployer une instance locale, vous pouvez suivre [la procédure de la documentation Elastic](https://www.elastic.co/guide/en/elasticsearch/reference/current/setup.html)
2) Clôner ce dépôt matchSIRET, et installer les dépendances Python3.10 dans un environnement virtuel
3) Ouvrir le fichier `indexation/indexation.ipynb`, indiquer l'url de votre service Elasticsearch dans la cellule correspondante, et exécuter l'ensemble des cellules (ce processus prend plusieurs heures)

## Envoyer des requêtes à cette instance Elasticsearch

L'index Elasticsearch créé et rempli précédemment s'appuie sur un stockage permanent (qui ne disparaît pas avec la fermeture du service Elastic). On peut y effectuer des recherches avec les fonctions utilitaires du fichier `queries.py` qui s'appuient sur les structure de données `WorkSiteName` et `GeoWorkSiteName` de `worksites.py`

## Coment contribuer

Voir le [guide de contribution](CONTRIBUTING.md)

## Méthodologie 

Le but est de retrouver un établissement d'entreprise à partir d'un libellé potentiellement approximatif (qui peut correspondre au nom du groupe, au nom de l'enseigne, au nom commercial de l'établissmeent, etc.) et  d'une information géographique possiblement approximative (une adresse ou un nom de ville). D'autres champs peuvent venir fiabiliser la recherche, comme le secteur d'activité, etc. Elasticsearch permet une recherche floue ("fuzzy matching") sur les libellés, secteurs et autres champs textuels, et permet de représenter l'information géographique par un couple de coordonnées (latitude, longitude). 

_i) Construction d'un index_

L'ensemble des entrées de la base SIRENE sont géolocalisées par Etalab, puis versées dans l'index par le processus `indexation.ipynb` décrit plus haut (qui doit encore être automatisé pour un rafraichissement mensuel des données, ce qui n'est pas le cas aujourd'hui).

_ii ) Construction d'une recherche_

L'entité recherché se caractérise par un libellé (approximatif) et une adresse plus ou moins précise. Les établissements recherchés doivent être mis sous la forme `WorkSiteName` du fichier `worksites.py` , puis géocodées avec la fonction `geocode_worksites` (ce code écrit un fichier temporaire à l'emplacement d'où il est lancé ; il faut juste s'assurer qu'il a les droits d'écritures adaptés). L'établissement géolocalisé `WorkSiteName` peut ensuite être recherché avec la fonction `request_elastic` de `queries.py`
 
 _iii) Evaluation de la pertinence des résultats_
 
Pour évaluer la pertinence du moteur de recherche, vous avez besoin de données de validation pour lesquels vous disposez déjà d'une association du SIRET, du libellé et de l'adresse. Lors de la conception de ce projet, nous nous sommes appuyés sur des [données en open data](data_sources.txt), notamment une base de restaurants (non exhasutive) utilisée et publiée par la Direction Générale de l'Alimentation (DGAL).

Remarque : il peut arriver que plusoieurs établissements d'entreprise répondent aux critères de recherche (par exemple, si vous avez spécifié une ville et un nom de groupe, et que plusieurs établissements de ce groupe se trouvent dans cette ville). Il faut alors renvoyer l'ensemble de ces résultats exacts (ce cas se pose assez peu dans notre base de données des restaurants).

Si vous êtes un réutilisateur de ce code pour une mission spécifique, il peut être pertinent pour vous d'utiliser vos propres données de validation et de les utiliser pour finetuner vos poids (dans la mesure où l'efficacité opérationnelle dépend de l'équilibrage des poids de recherche)

  _iv) Finetuner le modèle_
 
 En utiliser vos propres données de finetuning comprenant déjà des SIRET, des adresses, des libellés et tous champs très présent pour votre cas d'usage, vous pouvez finetuner les poids de recherche Elasticsearch. Pour celà, il vous suffit de modifier le fichier de poids.

_(Pour l'historie du projet : la méthodologie d'avant-projet est décrite sur le [wiki du programme 10%](https://github.com/etalab-ia/programme10pourcent/wiki/Ateliers-SIRETisation))_


## API

### Présentation du endpoint `/match` Tester son jeu de donnée

Un endpoint a été créée afin de pouvoir : 

Vérifier que le matching s'effectue bien entre le nom d'un établissement dans sa base et le nom officiel de l'insee. Pour cela, il faudra avoir des siret dans sa base pour vérifier a posteriori de la requête elastic si le résultat trouvé correspond bien à celui cherché. 

Cette API teste une solution avec et sans géocodage de l'adresse : cela permet donc de connaître la qualité des adresses de sa base. Dans certains cas, l'utilisation du géocodage est intéressant (quand les adresses fournies ne sont pas de trop mauvaises qualité). Cela permet d'améliorer le score de confiance des résultats (d'autant plus que la source de l'index est la base SIRENE géocodée via la BAN). Dans d'autres cas, le géocoding n'est pas nécessaire et au contraire amène plus de flous (il s'agit des cas où les adresses ne sont vraiment pas de bonnes qualité).

La réponse de l'API indiquera si le géocodage a été utilisé, ce qui permettra aux utilisateurs de savoir si celui-ci doit être utilisé ou non lors de la tentative de recherche d'établissement.

#### Cas d'utilisation

Je cherche à évaluer ma base établissement et trouver l'établissement suivant : 

```
SIRET : 34326262216640
NOM : LIDL
ADRESSE : 41 AV ETIENNE BILLIERES 31555 TOULOUSE
POSTCODE : 31300
```

##### Cas 1 : Je dispose d'une bonne qualité de données.

Si mes données ressemblent à ça :

```
SIRET : 34326262216640
NOM : LIDL BILIERES # Mauvaise dénomination
ADRESSE : 12 AV ETIENNE BILIER # Mauvaise adresse mais d'une qualité "acceptable"
POSTCODE : 31300 # Bon code postal
```

Je peux requêter l'API de la façon suivante : 

```
curl -X POST http://localhost:5000/match -H 'Content-Type: application/json' -d '{"siret": "34326262216640", "name": "lidl bilieres", "address": "12 av etienne bilier", "postcode": "31300"}
```

Le résultat de l'API retournera :

```
{
   "found_name":"lidl",
   "found_siret":"34326262216640",
   "match":true, # Indication signifiant que le SIRET est trouvé
   "message":"Found", # Message
   "original_name":"lidl bilieres",
   "original_siret":"34326262216640",
   "with_address":true, # L'adresse a été utilisée pour trouver le SIRET
   "with_geocoding":true # L'adresse a été géocodée pour trouver le SIRET
}
```

##### Cas 2 : Je dispose d'une qualité moyenne des données pour l'adresse

Si mes données ressemblent à ça :

```
SIRET : 34326262216640
NOM : LIDL
ADRESSE : ETIENNE BILIERES # adresse de qualité moyenne. Il n'y a pas de code postal dans mes données.
```

Je peux requêter l'API de la façon suivante : 

```
curl -X POST http://localhost:5000/match -H 'Content-Type: application/json' -d '{"siret": "34326262216640", "name": "lidl", "address": "etienne bilieres"}
```

Le résultat de l'API retournera :

```
{
   "found_name":"lidl",
   "found_siret":"34326262216640",
   "match":true, # L'établissement a été trouvé
   "message":"Found", # Message
   "original_name":"lidl",
   "original_siret":"34326262216640",
   "with_address":true, # L'adresse a été utilisée pour trouver l'établissement
   "with_geocoding":false # Le géocodage n'a pas été utilisé pour trouver l'établissement
}
```

NB : Ici, si l'on géocode simplement "etienne bilieres", la BAN nous renvoie une adresse dans une autre ville que Toulouse (l'adresse n'étant suffisamment pas précise). Cette adresse géocodée ne permet pas de retrouver l'établissement, on bascule donc dans un mode sans géocodage mais en gardant l'adresse dans les termes de la requête pour trouver l'établissement. Cela marche pour ce cas. 

##### Cas 3 : Je dispose d'une très mauvaise qualité des données pour l'adresse

Si mes données ressemblent à ça :

```
SIRET : 34326262216640
NOM : LIDL
ADRESSE : TRES MAUVAISE ADRESSE # mauvaise adresse étant peu interprétable
POSTCODE : 31300 # Bon code postal
```

Je peux requêter l'API de la façon suivante : 

```
curl -X POST http://localhost:5000/match -H 'Content-Type: application/json' -d '{"siret": "34326262216640", "name": "lidl bilieres", "address": "très mauvaise adresse", "postcode": "31300"}
```

Le résultat de l'API retournera :

```
{
   "found_name":"lidl",
   "found_siret":"34326262216640",
   "match":true, # Indication signifiant que le SIRET est trouvé
   "message":"Found", # Message
   "original_name":"lidl",
   "original_siret":"34326262216640",
   "with_address":false, # L'adresse n'a pas été utilisée pour trouver le SIRET
   "with_geocoding":false # Le géocodage n'a pas été utilisé pour trouver le SIRET
}
```

NB : Ici, ni l'étape de géocodage, ni la simple réutilisation de l'adresse ne permet de retrouver l'établissement. On lance donc une requête uniquement basé sur le nom fourni et éventuellement le code postal ou la ville fournie. Que l'on spécifie le code postal ou pas, l'établissement sera bien retrouvé. Cependant, en spécifiant le code postal, on limite énormément le nombre d'établissement éligible (A Toulouse vs sur toute la France)

### Présentation du endpoint `/search` pour trouver un établissement

Basé sur les résultats de l'api `/match`, l'utilisateur sait s'il doit utiliser le géocoding ou non. Il peut donc rechercher tous les résultats relatifs à l'établissement recherché en activant ou non le géocoding dans l'API.

#### Cas d'utilisation

Je cherche à trouver ma base établissement et trouver l'établissement suivant : 

```
SIRET : 34326262216640
NOM : LIDL
ADRESSE : 41 AV ETIENNE BILLIERES 31555 TOULOUSE
POSTCODE : 31300
```

Basé sur mes tests sur le endpoint `/match` j'ai pu déterminé quels paramètres pour mon jeu de donnée était le mieux adapté pour trouver un établissement. Je vais donc jouer sur les paramètres `use_geocode` et `use_address` pour rechercher mon établissement.

Exemple : 

```
curl -X POST http://localhost:5000/search -H 'Content-Type: application/json' -d '{"name": "lidl", "address": "etienne bilieres", "use_geocode": "false", "use_address": "true", "postcode": "33300"}
```

Ici, je décide de chercher des résultats sans géocodage mais en gardant les éléments d'adresses. Les valeurs des propriétés `use_geocode` ou `use_address` peuvent prendre les valeurs `true` ou `false`

### Déploiement de l'API

Cet simple API est développée en python, en utilisant le framework Flask.

Le déploiement de celle-ci est réalisée sur Onyxia via le fichier de configuration présent dans ce repo : `deployment.yaml`. Celui-ci récupère une image docker préalablement push sur Docker Hub (geoffreyaldebert/matchsiretapi basé sur le Dockerfile présent dans ce repo) et la déploie sur le cluser Kubernetes Onyxia via la commande : 

```
kubectl apply -f deployment.yaml
```

Les données sont alors requêtable via la commande 

```
curl http://matchsiretapi-service:5000/<MON ENDPOINT> <MES PARAMETRES>
```

## Projets open source liés à ce dépôt

[SocialGouv](https://github.com/SocialGouv/recherche-entreprises) : recherche d'établissements d'entreprises, notamment pour des travaux sur les conventions collectives
[L'Annuaire des entreprises](https://github.com/etalab/annuaire-entreprises-search-infra) : recherche d'entreprises (à l'échelle du SIREN et non du SIRET)

## Contact

La maintenance est effectuée par Etalab, au sein de la Direction interministérielle du numérique (DINUM) française.

[lab-ia@data.gouv.fr](mailto:lab-ia@data.gouv.fr)

