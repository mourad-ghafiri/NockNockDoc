from pydantic import BaseModel


class SimilarQueriesDto(BaseModel):
    query: str
    top_k: int = 5
