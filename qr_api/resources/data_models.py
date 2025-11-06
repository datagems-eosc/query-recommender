
from typing import Any, Optional, List
from pydantic import BaseModel

class Location(BaseModel):
    city: str
    country: str

class UserProfile(BaseModel):
    name: str
    surname: str
    age: int
    email: str
    affiliation: str
    location: Location
    previous_queries: List[str]

class QueryRequest(BaseModel):
    current_query: str
    context: Optional[Any] = None   # this should probably be a MoMa object, eventually 

class QueryResponse(BaseModel):
    next_queries: list[str]