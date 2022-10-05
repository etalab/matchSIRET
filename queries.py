from pydantic import BaseModel, Field
import datetime

class GeoPoint(BaseModel):
    lat: float
    lon: float
    
class Address(BaseModel):
    citycode: 

    
class EQuery(BaseModel):
    sentence: str = Field(
        ...,
        description="""The sentence of the fulltext search,
            ultimately processed using elasticsearch's simple_query_string""",
    )

    filters: EFilter = Field(
        ...,
        description="""Dictionnary of key values pairs
            such that keys are in the list of keys of our demand/letter
            that are LIST OF STRINGS""",
    )

    
class EWorkSite(BaseModel):
    siret: int
    commercial_name: Optional[str]
    point: Optional[GeoPoint]
    citycode: Optional[int]
    address: Optional[str]
    daterange: Optional[Union[datetime.datetime, Tuple[int, int]]] = None

    sorting: Optional[QuerySorting] = None
