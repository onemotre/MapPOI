import asyncio, aiohttp
from asyncio import Future

import pandas as pd

from typing import Any, Dict, Iterator, Tuple, List
from dataclasses import asdict

import config.settings
import models
import toolkit.errors
from models import AMapKeyWordParameters
from toolkit import errors
from toolkit import clients_log as logger


def parse_keyword_request(city: str, types: str, df: pd.DataFrame, data: Dict) -> Tuple[str, str, pd.DataFrame]:
    for i in range(int(data["count"])):
        poi = data["pois"][i]
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
                "big_category": [poi["type"].split(";")[0]],
                "mid_category": [poi["type"].split(";")[1]],
                "sub_category": [poi["type"].split(";")[2]],
            })
            if i == 1:
                city = poi["adname"]
                types = poi["type"].split(";")[1]
            if poi["typecode"] in config.settings.BASE_CLASS.PARKING_SET.value and "parking_type" in poi["business"]:
                new_item.loc[0, "parking_type"] = poi["business"]["parking_type"]
            else:
                new_item.loc[0, "parking_type"] = None
            if "rating" in poi["business"] and poi["business"]["rating"] is not None:
                new_item.loc[0, "rating"] = poi["business"]["rating"]
            else:
                new_item.loc[0, "rating"] = "暂无评分数据"
            df = pd.concat([df, new_item], ignore_index=True)
        except KeyError as e:
            raise errors.AMapApiError(poi, logger)

    return city, types, df


def _clean_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    清理参数字典，移除值为 None 的键
    """
    return {k: v for k, v in params.items() if v is not None}


class AMapAPIClients:
    def __init__(self, api_name: str = "GAODE", search_mode: str = "keyword"):
        self.sem = 1
        self.api_name = api_name
        self.search_mode = search_mode
        if self.search_mode == "keyword":
            self.BASE_URL = config.settings.SPIDER_CONFIG.AMAP_KEYWORD_URL.value
        else:
            raise toolkit.errors.ClientSettingError(logger)
        if self.api_name not in config.settings.BASE_CLASS.SUPPORT_APINAME.value:
            raise toolkit.errors.ClientSettingError(logger)

    async def fetch_data(self, sem: asyncio.Semaphore,
                         session: aiohttp.ClientSession,
                         param_iter: Iterator[AMapKeyWordParameters], retries: int = 5):
        """
        爬取同region, types的多页信息
        :param sem:
        :param session: HTTP请求管理
        :param param_iter: ParamConstructor返回的同region, types的不同页面的参数
        :param retries:重试次数（默认为5）
        :return: [pd.DataFrame] 对应region, types的poi信息
        """
        fetched_df = pd.DataFrame(
            columns=["index", "name", "lng", "lat", "province", "city", "area", "location",
                     "big_category", "mid_category", "sub_category", "rating", "parking_type"])
        for param in param_iter:
            city = param.city
            types = param.types
            params_dict = _clean_params(asdict(param))
            has_next = True
            # send request
            while retries > 0:
                try:
                    async with sem:
                        async with session.get(self.BASE_URL, params=params_dict) as resp:
                            if resp.status != 200:
                                raise errors.HTTPError(resp.status, logger)
                            data = await resp.json()
                            if data["status"] != "1":
                                raise errors.AMapApiError(data, logger)
                            if data["count"] == '0':
                                has_next = False
                                break
                            if self.search_mode == "keyword":
                                city, types, fetched_df = parse_keyword_request(city, types, fetched_df, data)
                                if fetched_df.shape[0] != 0:
                                    break
                                else:
                                    retries -= 1
                                    continue
                except (errors.HTTPError, aiohttp.ClientConnectionError, aiohttp.ClientOSError) as e:
                    print(f"\n Connection Error: {e}")
                    if retries > 0:
                        print(f"Retrying {retries} times")
                        await asyncio.sleep(3)
                        return self.fetch_data(sem, session, param_iter, retries - 1)
                    else:
                        return city, types, fetched_df
                except errors.AMapApiError as e:
                    if data["infocode"] == "10021":
                        await asyncio.sleep(2)
                        retries -= 1
                        continue
            if not has_next:
                break
        return city, types, fetched_df

    async def keyword_pipline(self, param_iter: models.ParamConstructor, types: List[str]):
        request_sem = asyncio.Semaphore(config.settings.SPIDER_CONFIG.MAX_REQUESTS_PRE_SECONDS.value)
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.fetch_data(request_sem, session,
                                (param_iter.amap_keyword_params(item))) for item in types
            ]
            region_data_list = await asyncio.gather(*tasks)
        return region_data_list
