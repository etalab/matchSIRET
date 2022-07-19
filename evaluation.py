from typing import List
from api_calls import annuaire_entreprise, social_gouv

def score_algorithms(algorithm: str, sirens: List[str], names: List[str], sirets: List[str]=[], zipcodes: List[str]=[]) -> (float, float):
    """
    Evaluate how algorithms as such as annuaire-entreprise and social-gouv are efficient to find a company plant, given the name of one of the etablissement and (optionnally) the zipcode  
    """
    
    algorithm = algorithm.lower()
    known_services = ["annuaire-entreprises", "social-gouv"]
    assert algorithm in known_services, f"The service {algorithm} is unknown. Please choose one of these: {known_services}"
    assert len(sirens) == len(names) and (len(names) == len(zipcodes) or len(zipcodes)==0), "Error in input data: sirens, names and zipcodes must have same lengths (except if zipcodes is empty)."
    siren_score = 0
    siret_score = 0
    for k, name in enumerate(names):
        if algorithm == "annuaire-entreprises":
            if len(zipcodes):
                zipcode = str(zipcodes[k])
            else:
                zipcode = None
            found_sirens, found_sirets, found_names, found_usual_names = annuaire_entreprise(name=name,zipcode=zipcode)
        elif algorithm == "social-gouv":
            if len(zipcodes):
                zipcode = str(zipcodes[k])
            else:
                zipcode = None
            found_sirens, found_sirets, found_names, found_usual_names = social_gouv(name=name, address=zipcode)
        try:
            most_probable_siren = found_sirens[0]
            if algorithm in ["annuaire-entreprises", "social-gouv"] and len(found_sirets) and len(sirets):
                most_probable_siret = found_sirets[0]
                siret_score += (most_probable_siret == sirets[k])

            siren_score += (most_probable_siren == sirens[k])
        except IndexError:
            continue
    return siren_score / max(len(sirens),1), siret_score / max(len(sirets),1)
    