from flask import Flask, request, jsonify
import json
import elasticsearch as es
from worksites import WorkSiteName, geocode_worksites
from queries import get_match_response, request_elastic, check_if_same_score

app = Flask(__name__, static_url_path='')
ELASTIC_URL = "http://elasticsearch-master:9200"
conn = es.Elasticsearch(ELASTIC_URL)

geo_threshold = 0.7

@app.route('/test')
def dates():
    test = {"hello": "world!"}
    return jsonify(test)


@app.route('/match', methods=['POST'])
def get_match():
    siret = request.json["siret"]
    name = request.json["name"]
    postcode = request.json["postcode"] if "postcode" in request.json else None
    city = request.json["city"] if "city" in request.json else None
    address = request.json["address"]
    
    wks = [WorkSiteName(**{
            "siret":siret,
            "name": name,
            "postcode": postcode,
            "cityname": city, 
            "address": address
        })]
    
    geowk = geocode_worksites(wks)[0]
    
    answer, found, useGeocode, useAddress  = get_match_response(conn, geoworksite=geowk, siret_truth=geowk.siret, geo_threshold=geo_threshold)

    if answer:
        if found:
            return jsonify(
                {
                    "match": True,
                    "with_geocoding": True if useGeocode else False,
                    "with_address": True if useAddress else False,
                    "message": "Found",
                    
                    "original_name": name,
                    "found_name": answer["_source"]["nom_complet"],
                    "original_siret": siret,
                    "found_siret": answer["_source"]["siret"]
                }
            )
        else:
            return jsonify(
                {
                    "match": False,
                    "message": "Not found but results",
                    "original_name": name,
                    "best_found_name": answer["_source"]["nom_complet"],
                    "original_siret": siret,
                    "best_found_siret": answer["_source"]["siret"]
                }
            )
            
    else:
        return jsonify(
            {
                "match": False,
                "message": "Not found and no result at all",
                "original_name": name,
                "original_siret": siret,
            }
        )

    
@app.route('/search', methods=['POST'])
def get_info_siret():
    name = request.json["name"]
    postcode = request.json["postcode"] if "postcode" in request.json else None
    city = request.json["city"] if "city" in request.json else None
    address = request.json["address"] if "address" in request.json else None
    use_geocode = request.json["use_geocode"] if "use_geocode" in request.json else True # Geocode by default
    use_address = request.json["use_address"] if "use_address" in request.json else True # Geocode by default
    
    wks = [WorkSiteName(**{
            "name": name,
            "postcode": postcode,
            "cityname": city, 
            "address": address
        })]
    
    geowk = geocode_worksites(wks)[0]
    
    output, is_use_geocode, is_use_address = request_elastic(conn, geowk, geo_threshold=geo_threshold, use_geo=use_geocode, use_address=use_address)
    output = check_if_same_score(output)
    return jsonify([o["_source"] for o in output] if output else [])

if __name__ == '__main__':
    app.run(host='0.0.0.0')
