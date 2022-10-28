import elasticsearch as es
from typing import Dict, List
from math import cos, pi, isnan
from worksites import GeoWorkSiteName


def request_elastic(
    conn: es.Elasticsearch, geowk: GeoWorkSiteName, geo_threshold: float = 0.7
) -> List[Dict]:
    km_tolerance = 5
    lat_tolerance = 5 / 111  # approximation 1°lat = 111 km
    lon_tolerance = (
        5 / 111 * cos(pi / 180 * 48)
    )  # approximation 1°lon = 111*cos(lon) km, with Paris lon=48

    q = {
        "bool": {
            "should": [
                {"match": {"commune": geowk.__getattribute__("citycode")}},
                {
                    "multi_match": {
                        "query": geowk.__getattribute__("name"),
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

    # TODO: this thresholding on geocoding quality is arbitrary and realy important
    if geowk.score >= geo_threshold:
        q["bool"]["must"] = [
            {
                "range": {
                    "latitude": {
                        "gte": geowk.latitude - lat_tolerance,
                        "lte": geowk.latitude + lat_tolerance,
                    }
                }
            },
            {
                "range": {
                    "longitude": {
                        "gte": geowk.longitude - lon_tolerance,
                        "lte": geowk.longitude + lon_tolerance,
                    }
                }
            },
        ]
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

    if geowk.__getattribute__("sector"):
        q["bool"]["should"].append(
            {"match": {"section_activite_principale": geowk.__getattribute__("sector")}}
        )

    for field in list(geowk.__dict__):
        if field in ["score", "citycode", "address", "latitude", "longitude", "name"]:
            continue
        elif geowk.__getattribute__(field):
            q["bool"]["should"].append(
                {"match": {field: geowk.__getattribute__(field)}}
            )
    response = conn.search(index="siret", query=q)["hits"]["hits"]
    response.sort(reverse=True, key=lambda f: f["_score"])
    return response
