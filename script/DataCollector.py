import os
import re
import asyncio, aiohttp
import pandas as pd
import logging

from tqdm import tqdm
from tqdm.asyncio import tqdm as tqdm_asyncio
from typing import List

from ..clients import *
from ..models import *
from ..config import settings

logging.basicConfig(filename=f"{settings.BASE_FILE_PATH.LOG_PATH.value}DataCollectorError.log", 
                    level=logging.ERROR, format='%(asctime)s %(levelname)s %(message)s')

class DataCollector:
  def __init__(self, api_mode : str = "AMAP") -> None:
    self.api_mode = api_mode
    self.excel_num = 0
    self.data_frames = []

  def amap_keyword_param_constructor(self) -> List[AMapKeywordParameters]:
    params = []
    print("/****************** Constructing Parameters... ******************/")
    for city in tqdm(settings.SEARCH_AREA, desc="City Loop", ncols=100, ascii=True):
      for types in tqdm(settings.KEYWORDS, desc="Keyword Loop", ncols=100, ascii=True):
        params.append(
          AMapKeywordParameters(key=settings.AMAP_API_KEY,
                                keywords='*',
                                types=types,
                                city=city,
                                city_limit='true',
                                page_size=25,
                                page_num=1))
    self.excel_num = len(params)
    return params

  async def keyword_worker(self, sem: asyncio.Semaphore, client: AMapApiClient, 
                        session: aiohttp.ClientSession, params: AMapKeywordParameters):
    async with sem:
      return await client.fetch_data(session, params)
    
  async def KeywordDataCollect(self, params_list: List[AMapKeywordParameters]):
    client = AMapApiClient(api_name='AMAP', search_mode='keyword')
    sem = asyncio.Semaphore(settings.MAX_REQUESTS_PRE_SECOND)

    print("/****************** Collecting Data... ******************/")
    async with aiohttp.ClientSession() as session:
      tasks = [self.keyword_worker(sem=sem, client=client, 
                              session=session, params=params) for params in params_list]
      for task in tqdm_asyncio.as_completed(tasks, desc="Data Collecting", ncols=100, ascii=True):
        result = await task
        if result is not None:
          self.data_frames.append(result)

  def save_data(self):
    for i in range(self.excel_num):
      name = self.data_frames[i].name[0]
      file_name = "{}AMAP_{}.xlsx".format(settings.BASE_FILE_PATH.DATA_MAIN_PATH.value, name)
      file_name = re.sub(r'[|]', '_', file_name)
      try:
        print(f"Saving data to excel {file_name}")
        self.data_frames[i].to_excel(file_name, index=False)
      except Exception as e:
        print(f"Error in saving data to excel {file_name}")
        logging.error(f"save data error | {e}")
      

  def search_process(self):
    params_list = self.amap_keyword_param_constructor()
    asyncio.run(self.KeywordDataCollect(params_list))
    self.save_data()


if __name__ == "__main__":
  print("Start Collecting Datas...")
  DataCollector().search_process()