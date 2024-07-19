from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Iterator
import pandas as pd
import re

from config import settings
        
KEYWORD_URL = "https://restapi.amap.com/v5/place/text?"
ROUND_URL = "https://restapi.amap.com/v3/place/around?"

@dataclass
class AMapKeywordParameters:
    key: str
    keywords: Optional[str] = "*" #查询关键字
    types: Optional[str] = "*"  #分类代码 或 汉字（若用汉字，请严格按照附件之中的汉字填写）规则： 多个关键字用“|”分割
    city: Optional[str] = "北京市"
    city_limit: Optional[str] = "true"
    page_size: Optional[int] = 25  # 不超过25
    page_num: Optional[int] = 1
    output: Optional[str] = 'json'
    show_fields: Optional[str] = 'business'

@dataclass
class AMapRoundParameters:
    key: str
    location: str # 查询经纬度坐标
    keyword: Optional[str] # 查询关键字，仅支持单个关键字
    types: Optional[str] # 查询POI类型
    city: Optional[str]
    radius: Optional[int] = 1000  # 查询半径m
    sortrule: Optional[str] = 'distance'  # 排序规则
    offset: Optional[int] = 20
    page: Optional[int] = 1
    extensions: Optional[str] = 'all'
    output: Optional[str] = 'json'

class ParamConstructor:
    def __init__(self, id : int, city : str, 
                 param : Dict[str, Any] = 
                     {"keyword": "*",
                     "city_limit": "true",
                     "page_size": 25}
                 ) -> None:
        self.id = id
        self.city = city
        self.base_param = param
        self.types_idx = 0

    def amap_keyword_params(self) -> Iterator[AMapKeywordParameters]:
        for page in range(1, 100):
            yield AMapKeywordParameters(
                key=settings.AMAP_API_KEY,
                keywords=self.base_param["keyword"],
                city=self.city,
                city_limit=self.base_param["city_limit"],
                page_size=self.base_param["page_size"],
                page_num=page
            )

    def get_path(city : str) -> str:
        city_path = settings.BASE_FILE_PATH.DATA_MAIN_PATH.value + city + "\\" 
        return city_path
    
    def get_size(self) -> int:
        return self.types_idx
