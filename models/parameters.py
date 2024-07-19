import pandas as pd
import re

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Iterator

import config.settings


@dataclass
class AMapKeyWordParameters:
    city: str
    page_num: int
    types: str
    key: Optional[str] = config.settings.AMAP_API_KEY
    keyword: Optional[str] = "*"
    city_limit: Optional[str] = "true"
    page_size: Optional[int] = 25  # 不超过25
    output: Optional[str] = 'json'
    show_fields: Optional[str] = 'business'


class ParamConstructor:
    def __init__(self, city: str):
        self.city = city

    def amap_keyword_params(self, types: str) -> Iterator[AMapKeyWordParameters]:
        for page in range(1, 100):
            yield AMapKeyWordParameters(
                city=self.city,
                page_num=page,
                types=types
            )
