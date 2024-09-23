from pydantic import BaseModel


class PaginatedViewBase(BaseModel):
    total: int
