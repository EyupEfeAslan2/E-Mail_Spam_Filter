from pydantic import BaseModel


class EmailRequest(BaseModel):
    text: str

class SensitivityRequest(BaseModel):
    threshold: float
