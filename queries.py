import elasticsearch as es
from typing import Dict, List
from math import isnan
from worksites import GeoWorkSiteName


def request_elastic(
    conn: es.Elasticsearch, geowk: GeoWorkSiteName, geo_threshold: float = 0.7
) -> List[Dict]:
    km_tolerance = 20
    q = {
        "bool": {
            "should": [
                {
                    "multi_match": {
                        "query": geowk.__getattribute__("name"),
                        "fuzziness" : "AUTO",
                        "fields": [
                            "nom_raison_sociale",
                            "nom_commercial",
                            "nom_complet",
                            "sigle",
                        ],
                    }
                },
            ]
        }
    }

    # TODO: the choice of thresholding on geocoding has strong impact. Adapt it to your usecase.
    if geowk.score >= geo_threshold:
        
        q["bool"]["filter"] = {
            "geo_distance": {
                "distance": km_tolerance,
                "coordonnees": {
                    "lat": geowk.latitude,
                    "lon": geowk.longitude
                }
            }
        }
        
        if geowk.__getattribute__("address"):
            q["bool"]["should"].append(
                {
                    "multi_match": {
                        "query": geowk.__getattribute__("address"),
                        "fields": [
                            "addresse_etablissement",
                            "libelle_voie",
                            "numero_voie",
                        ],
                    }
                }
            )
        if geowk.__getattribute__("citycode"):
            q["bool"]["should"].append(
                {
                    "match": {"commune": geowk.__getattribute__("citycode")}
                }
            )
        if geowk.__getattribute__("cityname"):
            q["bool"]["should"].append(
                {
                    "match": {"libelle_commune": geowk.__getattribute__("cityname")}
                }
            )

    
    else:
        if geowk.__getattribute__("old_postcode"):
            q["bool"]["should"].append(
                {
                    "match": {"code_postal": geowk.__getattribute__("old_postcode")}
                }
            )
        if geowk.__getattribute__("old_cityname"):
            q["bool"]["should"].append(
                {
                    "match": {"libelle_commune": geowk.__getattribute__("old_cityname")}
                }
            )

        if geowk.__getattribute__("old_address"):
            q["bool"]["should"].append(
                {
                    "multi_match": {
                        "query": geowk.__getattribute__("old_address"),
                        "fields": [
                            "addresse_etablissement",
                            "libelle_voie",
                            "numero_voie",
                        ],
                    }
                }
            )


    for field in list(geowk.__dict__):
        if field in ["score", "citycode", "old_postcode", "old_cityname", "old_address", "address", "latitude", "longitude", "name"]:
            continue
        elif geowk.__getattribute__(field): # example: 'sector'
            q["bool"]["should"].append(
                {"match": {field: geowk.__getattribute__(field)}}
            )
    response = conn.search(index="siret", query=q, size=100)["hits"]["hits"]
    response.sort(reverse=True, key=lambda f: f["_score"])
    return response
