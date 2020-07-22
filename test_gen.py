from typing import Iterable, Optional
from pydantic import BaseModel, validator
from pydantic.dataclasses import dataclass
import random
import string
import uuid
from datetime import datetime


def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = "".join(random.choice(letters) for i in range(length))
    return result_str


class SiteCode(BaseModel):
    site_code: Optional[str]

    @validator("site_code", always=True)
    def gen_site_code(cls, v):
        if v:
            return v
        return get_random_string(4)


class PointID(BaseModel):
    point_id: Optional[uuid.UUID]

    @validator("point_id", always=True)
    def gen_point_id(cls, v):
        if v:
            return v
        return uuid.uuid4()


class LAQNSiteModel(SiteCode, PointID):

    date_opened: datetime
    date_closed: Optional[datetime]


m = SiteCode()
p = PointID()
l = LAQNSiteModel(date_opened="2020-01-01T00:00:00", point_id=p.point_id).dict()

print(m)
print(p)
print(l)
