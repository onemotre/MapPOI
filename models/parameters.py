from dataclasses import dataclass
from typing import Optional

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
    extensions: Optional[str] = 'all'
    output: Optional[str] = 'json'

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
