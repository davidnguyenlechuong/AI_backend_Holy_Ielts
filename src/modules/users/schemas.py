from pydantic import BaseModel


class UserMeResponse(BaseModel):
    id: str
    name: str
    email: str
