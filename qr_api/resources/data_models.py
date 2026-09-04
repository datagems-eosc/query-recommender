
from typing import Any, Optional
from pydantic import BaseModel

class QueryRequest(BaseModel):
    current_query: str
    context: Optional[Any] = None   # this should probably be a MoMa object, eventually 

class QueryResponse(BaseModel):
    next_queries: list[str]