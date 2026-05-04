from pydantic import BaseModel


class EmailRequest(BaseModel):
    text: str


class BatchEmailRequest(BaseModel):
    emails: list[str]


class SensitivityRequest(BaseModel):
    threshold: float
