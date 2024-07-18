import asyncio, aiohttp
import requests
import pandas as pd
import logging
import datetime
from tqdm import tqdm

from typing import Any, Dict
from dataclasses import asdict

from ..models.parameters import *
from ..config import settings

logging.basicConfig(filename=f"{settings.BASE_FILE_PATH.LOG_PATH.value}ClientError.log", level=logging.ERROR,
                    format='%(asctime)s %(levelname)s %(message)s')

class AMapApiError(Exception):
    def __init__(self, infocode : str, info : str) -> None:
        super().__init__(f"AMapKeyword Error: infocode={infocode}, info={info}. More info: https://lbs.amap.com/api/webservice/guide/tools/info/")
        self.infocode = infocode
        self.error_info = info

class HTTPError(Exception):
    def __init__(self, status_code: int) -> None:
        super().__init__(f"HTTP Error: status_code={status_code}")

class AMapApiClient:
    def __init__(self, api_name: str = 'AMAP', search_mode: str = 'keyword'):
        self.search_mode = search_mode
        if search_mode == 'keyword':
            self.BASE_URL = KEYWORD_URL
        else:
            self.BASE_URL = ROUND_URL
        if api_name == 'BAIDU':
            self.api_key = settings.BAIDU_API_KEY
        else:
            self.api_key = settings.AMAP_API_KEY
            
    async def fetch_data(self, session: aiohttp.ClientSession, params) -> pd.DataFrame:
        url = self.BASE_URL
        params_dict = self._clean_params(asdict(params))
        params_dict['key'] = self.api_key
        page = 1
        fetched_df = pd.DataFrame(
            columns=["index", "name", "lng", "lat", "province", "city", "area", "location",
                     "big_category", "mid_category", "sub_category", "rating", "parking_type"])
        name = params_dict.get('city', None) + "|" + params_dict.get('types', None)
        while True:
            try:
                params_dict['page_num'] = page
                async with session.get(url, params=params_dict) as response:
                    if response.status != 200:
                        raise HTTPError(response.status)
                    response = await response.json()
                    if response["status"] == "1":
                        if response["count"] == "0":
                            break
                        page += 1
                        if self.search_mode == 'keyword':
                            fetched_df = self.parse_keyword_data(fetched_df, response)
                        elif self.search_mode == 'round':
                            fetched_df = self.parse_round_data(fetched_df, response)
                        else:
                            return None
                    else:
                        raise AMapApiError(response["infocode"], response["info"])
            except HTTPError as e:
                logging.error(f"| http get error | {e}")
                print(f"{e}")
                return await None
            except AMapApiError as e:
                logging.error(f"| api error | {e}")
                print(f"{e}")
                return await None
        fetched_df.name = name 
        return fetched_df
        
            
    def parse_keyword_data(self, df : pd.DataFrame, response : dict):
        for i in range(int(response["count"])):
            poi = response["pois"][i]
            try:
                new_item = pd.DataFrame({
                    "index": [df.shape[0]],
                    "name": poi["name"],
                    "lng": poi["location"].split(",")[0],
                    "lat": poi["location"].split(",")[1],
                    "province": poi["pname"],
                    "city": poi["cityname"],
                    "area": poi["adname"],
                    "location": poi["location"],
                    "big_category" : poi["type"].split(";")[0],
                    "mid_category" : poi["type"].split(";")[1],
                    "sub_category" : poi["type"].split(";")[2],
                })
                if poi["typecode"] in settings.BASE_CLASS.PARKING_SET.value and "parking_type" in poi["business"]:
                    new_item.loc[0, "parking_type"] = poi["business"]["parking_type"]
                else:
                    new_item.loc[0, "parking_type"] = None
                if "rating" in poi["business"] and poi["business"]["rating"] is not None:
                    new_item.loc[0, "rating"] = poi["business"]["rating"]
                else:
                    new_item.loc[0, "rating"] = "暂无评分数据"
                df = pd.concat([df, new_item], ignore_index=True)

            except KeyError as e:
                logging.error(f"| item {len(df)} was parsed error | {e}")
        
        return df
    
    def parse_round_data(self, df: pd.DataFrame, response: dict) -> pd.DataFrame:
        for poi in response["pois"]:
            try:
                new_item = pd.DataFrame({
                    "index": [df.shape[0]],
                    "name": [poi["name"]],
                    "lng": [poi["location"].split(",")[0]],
                    "lat": [poi["location"].split(",")[1]],
                    "province": [poi["pname"]],
                    "city": [poi["cityname"]],
                    "area": [poi["adname"]],
                    "location": [poi["location"]],
                })
                df = pd.concat([df, new_item], ignore_index=True)
            except KeyError as e:
                logging.error(f"| item {df.shape[0]} was parsed error | {e}")
        return df

    def _clean_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理参数字典，移除值为 None 的键
        """
        return {k: v for k, v in params.items() if v is not None}
    