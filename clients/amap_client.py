import asyncio, aiohttp
import requests
import pandas as pd
import logging
import datetime
from tqdm import tqdm

from typing import Any, Dict, Iterator
from dataclasses import asdict

from models import *
from config import settings

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
            
    async def fetch_data(self, session: aiohttp.ClientSession, 
                         params : Iterator[AMapKeywordParameters], retries=3) -> list[pd.DataFrame]:
        url = self.BASE_URL
        all_df = []
        for infotype in settings.KEYWORDS:
            fetched_df = pd.DataFrame(
                columns=["index", "name", "lng", "lat", "province", "city", "area", "location",
                         "big_category", "mid_category", "sub_category", "rating", "parking_type"])
            for param in params:
                param.types = infotype
                params_dict = self._clean_params(asdict(param))
                try:
                    async with session.get(url, params=params_dict, timeout=aiohttp.ClientTimeout(total=30)) as response:
                        if response.status != 200:
                            raise HTTPError(response.status)
                        data = await response.json()
                        if data["status"] == "1":
                            if data["count"] == "0":
                                break
                            if self.search_mode == 'keyword':
                                fetched_df = self.parse_keyword_data(fetched_df, data)
                            elif self.search_mode == 'round':
                                fetched_df = self.parse_round_data(fetched_df, data)
                            else:
                                print("don't support this search mode")
                                return all_df
                        else:
                            raise AMapApiError(data["infocode"], data["info"])
                except (HTTPError, aiohttp.ClientConnectorError, aiohttp.ClientOSError) as e:
                    logging.error(f"| http get error | {e}")
                    print(f"{e}")
                    if retries > 0:
                        print(f"Retrying {retries} times...")
                        await asyncio.sleep(3)
                        return await self.fetch_data(session, params, retries - 1)
                    else:
                        return all_df
                except AMapApiError as e:
                    logging.error(f"| api error | {e}")
                    if e.infocode == "10021":
                    # 高德地图API每秒请求次数超限制
                        await asyncio.sleep(1)
                    else:
                        print(f"{e}")
            all_df.append(fetched_df)
        return all_df
            
    def parse_keyword_data(self, df : pd.DataFrame, response : dict):
        for i in range(int(response["count"])):
            poi = response["pois"][i]
            try:
                new_item = pd.DataFrame({
                    "index": [str(df.shape[0] + 1)],
                    "name": [poi["name"]],
                    "lng": [poi["location"].split(",")[0]],
                    "lat": [poi["location"].split(",")[1]],
                    "province": [poi["pname"]],
                    "city": [poi["cityname"]],
                    "area": [poi["adname"]],
                    "location": [poi["location"]],
                    "big_category" : [poi["type"].split(";")[0]],
                    "mid_category" : [poi["type"].split(";")[1]],
                    "sub_category" : [poi["type"].split(";")[2]],
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
                print("occured KeyError error")
                logging.error(f"| item {len(df)} was parsed error | {e}")
        return df
    
    def parse_round_data(self, df: pd.DataFrame, response: dict) -> pd.DataFrame:
        for poi in response["pois"]:
            try:
                new_item = pd.DataFrame({
                    "index": [df.shape[0]],
                    "name": poi["name"],
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
    