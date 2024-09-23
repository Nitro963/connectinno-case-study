from pydantic import BaseModel


class Ping(BaseModel):
    hostname: str
    cpu_usage: float
    cpu_core: int
    memory_usage: float
