from pydantic import BaseModel


class UrlBase(BaseModel):
    target_url: str


class Url(UrlBase):
    is_active: bool
    clicks: int

    class Config:
        orm_mode = True


class UrlInfo(Url):
    url: str
    admin_url: str
