from pydantic import BaseModel


class ApiMeta(BaseModel):
    name: str
    version: str
    api_version: str = "v1"
