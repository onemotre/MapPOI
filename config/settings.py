import os
from enum import Enum

AMAP_API_KEY = "c1a6e793f86edf6211b1f55d7d38846c"


class BASE_FILE_PATH(Enum):
    CONFIG_PATH = str(os.path.dirname(os.path.abspath(__file__)))
    MAIN_WORD_PATH = str(os.path.dirname(CONFIG_PATH))
    DATA_MAIN_PATH = MAIN_WORD_PATH + "/data/"
    LOG_PATH = MAIN_WORD_PATH + "/log/"
    DIV = "/"


class BASE_CLASS(Enum):
    PARKING_SET = {"150900", "150903", "150904", "150905", "150906", " 150907", " 150908", "150909"}
    SUPPORT_APINAME = {"GAODE"}


class BASE_CONFIG(Enum):
    SEARCH_AREA = [
        '榕江县','花溪区','习水县','织金县','紫云自治县','赫章县','雷山县',
        '镇远县','平塘县','江口县','印江县','荔波县','台江县','从江县','黎平县','大方县'
    ]
    SEARCH_TYPECODES = [
        "风景名胜", "公共厕所", "停车场", "三星级宾馆|四星级宾馆|五星级宾馆|经济型连锁酒店",
        "公交车站", "咖啡厅|休闲餐饮场所", "充电站"
    ]
    # SEARCH_AREA = [
    #     '榕江县'
    # ]
    # SEARCH_TYPECODES = [
    #     "风景名胜"
    # ]


class SPIDER_CONFIG(Enum):
    AMAP_KEYWORD_URL = "https://restapi.amap.com/v5/place/text?"
    MAX_REQUESTS_PRE_SECONDS = 10
    MAX_WORK_CLIENTS_PRE_SECONDS = 4
