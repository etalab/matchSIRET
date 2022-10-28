from pydantic import BaseModel, Field
from typing import Optional, Union, List
import pandas as pd
import requests
import os


class WorkSiteName(BaseModel):
    name : str = Field(..., description="An official or commercial name of the worksite of the company")
    postcode : Optional[str] = Field(default=None, description="The postcode of the work place")
    cityname : Optional[str] = Field(default=None, description="The names of the work place cities/towns")
    address : Optional[str] = Field(default=None, description="The address of the work place")
    sector : Optional[str] = Field(default=None, description="The sector of the company")
    

class GeoWorkSiteName(BaseModel):
    name : str = Field(..., description="An official or commercial name of the worksite of the company")
    latitude : float = Field(..., description="The latitude of the worksite location")
    longitude : float = Field(..., description="The longitude of the worksite location")
    citycode : Optional[str] = Field(default=None, description="The citycode of the work place")
    cityname : Optional[str] = Field(default=None, description="The names of the work place cities/towns")
    address : Optional[str] = Field(default=None, description="The address of the work place")
    sector : Optional[str] = Field(default=None, description="The sector of the company")
    score : float = Field(default=None, description="the confidence score of geocoding")
    
    
    
def geocode_worksites(
    worksites: List[WorkSiteName]
) -> List[GeoWorkSiteName]:
    names, postcodes, citynames, addresses = list(), list(), list(), list()
    for worksite in worksites:
        names.append(worksite.name)
        postcodes.append(worksite.postcode)
        citynames.append(worksite.cityname)
        addresses.append(worksite.address)
        
    del worksites

    df = pd.DataFrame(data={"names": names, "address": addresses, "postcode": postcodes, "city": citynames})
    df.to_csv("tmp_workplaces.csv", index=False)
    del df, postcodes, citynames
    f = open('tmp_workplaces.csv', 'rb')
    files = {'data': ('tmp_workplaces', f)}
    payload = {'columns': ['address', 'city'], 'postcode': 'postcode',
               "result_columns": ["latitude", "longitude", "result_citycode", "result_city", "result_housenumber", "result_name", "result_score"]}
    r = requests.post('https://api-adresse.data.gouv.fr/search/csv/', files=files, data=payload, stream=True)
    with open('tmp_workplaces_geocoded.csv', 'wb') as fd:
        for chunk in r.iter_content(chunk_size=1024):
            fd.write(chunk)

    geocoded = pd.read_csv("tmp_workplaces_geocoded.csv", dtype=str)
    assert len(geocoded) == len(names)
    geocoded["name"] = names
    geoworksites = list()
    for ind, data in geocoded.iterrows():
        if addresses[ind]: # it is not relevant to add accurate address if there was no adress in input
            if not str(data["result_housenumber"]) == "nan":
                address = str(data["result_housenumber"]) +" " + data["result_name"]
            else:
                address = data["result_name"]
        else:
            address = None
        
        geoworksite = GeoWorkSiteName(**{
            "latitude": float(data["latitude"]),
            "longitude": float(data["longitude"]),
            "name": data["name"],
            "citycode":data["result_citycode"],
            "cityname": data["result_city"],
            "address": address,
            "score": float(data["result_score"])
        })
        geoworksites.append(geoworksite)
    os.remove("tmp_workplaces_geocoded.csv")
    os.remove("tmp_workplaces.csv")
    
    return geoworksites
    