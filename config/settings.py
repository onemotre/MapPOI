"""
全局配置文件
"""
import os
from enum import Enum
from typing import Set

class BASE_FILE_PATH(Enum):
  CONFIG_PATH = os.path.dirname(os.path.abspath(__file__))
  MAIN_WORD_PATH = os.path.dirname(CONFIG_PATH)
  DATA_MAIN_PATH = MAIN_WORD_PATH + "\\data\\"
  LOG_PATH = MAIN_WORD_PATH + "\\log\\"

class BASE_CLASS(Enum):
  PARKING_SET = {"150900", "150903", "150904", "150905", "150906"," 150907"," 150908", "150909"}

BAIDU_API_KEY = os.getenv('BAIDU_API_KEY', 'None')

########### 高德地图 API 配置 ###############
# 所有需要查询的城市
AMAP_API_KEY = os.getenv('AMAP_API_KEY', 'c1a6e793f86edf6211b1f55d7d38846c')
SEARCH_AREA = [
  '榕江县'
]
# 所有需要查询的关键字
KEYWORDS = [
    "公共厕所", "停车场", "充电站", 
    "公交车站", "咖啡厅|休闲餐饮场所", "风景名胜"
]

########## 其他设置 ############
MAX_REQUESTS_PRE_SECOND = os.getenv('MAX_REQUESTS_PRE_SECOND', 25)

