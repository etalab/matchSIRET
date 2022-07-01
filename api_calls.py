import requests
import json
from typing import List

def annuaire_entreprise(
    name: str,
    department:str=None,
    zipcode:str=None,
    activity:str=None,
    sector:str=None
) -> (List, List, List):
    """
    Documentation: https://api.gouv.fr/documentation/api-recherche-entreprises
    """
    url = "https://recherche-entreprises.api.gouv.fr/search"
    params = {"q": name, "page": "1", "per_page": "1"}
    for field_name, field_value in {
        "departement" : department,
        "code_postal": zipcode,
        "activite_principale": activity,
        "section_activite_principale": sector,
    }.items():
        if field_value is not None:
            params[field_name] = field_value
    try:
        results = json.loads(requests.get(url, params=params).content)["results"]
        official_names = [company["nom_raison_sociale"] for company in results]
        full_names = [company["nom_complet"] for company in results]
        sirens = [company["siren"] for company in results]
        return sirens, official_names, full_names
    except Exception as e:
        #return [], [], []
        raise e

