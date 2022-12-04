import elasticsearch as es
from typing import Dict, List
from math import isnan
from worksites import GeoWorkSiteName


def request_elastic(
    conn: es.Elasticsearch, geowk: GeoWorkSiteName, geo_threshold: float = 0.7, use_geo: bool = True
) -> List[Dict]:
    is_use_geocode = False
    km_tolerance = 5
    q = {
        "bool": {
            "should": [
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
    if use_geo:
        # TODO: the choice of thresholding on geocoding has strong impact. Adapt it to your usecase.
        if geowk.score >= geo_threshold:
            is_use_geocode = True
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
            is_use_geocode = False

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

    for field in list(geowk.__dict__):
        if field in ["score", "citycode", "old_postcode", "old_cityname", "old_address", "address", "latitude", "longitude", "name"]:
            continue
        elif geowk.__getattribute__(field): # example: 'sector'
            q["bool"]["should"].append(
                {"match": {field: geowk.__getattribute__(field)}}
            )
    response = conn.search(index="siret", query=q, size=100)["hits"]["hits"]
    response.sort(reverse=True, key=lambda f: f["_score"])
    return response, is_use_geocode


def check_if_same_score(output):
    if output:
        filter_output = []
        score = output[0]["_score"]
        for out in output:
            if out["_score"] == score:
                filter_output.append(out)
            else:
                return filter_output
    else:
        return []

    
def get_answer(conn, geoworksite, siret_truth:int, geo_threshold: float):
    output, is_use_geocode = request_elastic(conn, geoworksite, geo_threshold=geo_threshold, use_geo=True)
    output = check_if_same_score(output)
    if output:
        for out in output:
            if out["_source"]["siret"] == siret_truth:
                return out
    else:
        output, is_use_geocode = request_elastic(conn, geoworksite, use_geo=False)
        output = check_if_same_score(output)
        if output:
            for out in output:
                if out["_source"]["siret"] == siret_truth:
                    return out
        else:
            return

        
def get_match_response(conn, geoworksite, siret_truth:int, geo_threshold: float):
    output, is_use_geocode = request_elastic(conn, geoworksite, geo_threshold=geo_threshold, use_geo=True)
    output = check_if_same_score(output)
    if output:
        for out in output:
            if out["_source"]["siret"] == siret_truth:
                return out, True, is_use_geocode
        else:
            output, is_use_geocode = request_elastic(conn, geoworksite, use_geo=False)
            output = check_if_same_score(output)
            if output:
                for out in output:
                    if out["_source"]["siret"] == siret_truth:
                        return out, True, is_use_geocode
                return out, False, is_use_geocode
            else:
                return None, False, is_use_geocode 
    else:
        output, is_use_geocode = request_elastic(conn, geoworksite, use_geo=False)
        output = check_if_same_score(output)
        if output:
            for out in output:
                if out["_source"]["siret"] == siret_truth:
                    return out, True, is_use_geocode
            return out, False, is_use_geocode
        else:
            return None, False, is_use_geocode

        
def all_relevant_elastic_answers(conn, geoworksite, geo_threshold:float):
    output, is_use_geocode = request_elastic(conn, geowk, geo_threshold=geo_threshold)

