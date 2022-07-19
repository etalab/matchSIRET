import requests
import json
from typing import List

def annuaire_entreprise(
    name: str,
    department:str=None,
    zipcode:str=None,
    activity:str=None,
    sector:str=None
) -> (List, List, List, List):
    """
    FOR COMPANIES
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
        return sirens, [], official_names, full_names
    except Exception as e:
        #return [], [], []
        raise e

def social_gouv(name:str, address:str=None) -> (List, List, List, List):
    """
    FOR PLANTS (very different from annuaire entreprise)
    If there is several plants matching the given name and address, returns the first one (that may impact the performances)
    """
    url = "https://api.recherche-entreprises.fabrique.social.gouv.fr/api/v1/search"
    params = {"query": name, "limit" : 1, "matchingLimit": "-1", "convention": False, "open": False, "employer": False}
    if address is not None:
        params["address"] = address
    try:
        results = json.loads(requests.get(url, params=params).content)["entreprises"]
        official_names = [company["label"] for company in results]
        full_names = [company["simpleLabel"] for company in results]
        sirens = [company["siren"] for company in results]
        sirets = []
        for company in results:
            if len(company["allMatchingEtablissements"]):
                sirets.append(company["allMatchingEtablissements"][0]["siret"])
            else:
                sirets.append("")
                
        return sirens, sirets, official_names, full_names
    except Exception as e:
        #return [], [], []
        raise e