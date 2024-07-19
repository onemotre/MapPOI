import os
import re
import asyncio, aiohttp
import pandas as pd
import logging

from tqdm import tqdm
from tqdm.asyncio import tqdm as tqdm_asyncio
from typing import List, Iterator

from clients import *
from models import *
from config import settings

logging.basicConfig(filename=f"{settings.BASE_FILE_PATH.LOG_PATH.value}DataCollectorError.log", 
                    level=logging.ERROR, format='%(asctime)s %(levelname)s %(message)s')

class DataCollector:
  def __init__(self, api_mode : str = "AMAP") -> None:
    self.api_mode = api_mode
    self.excel_num = 0
    self.data_frames = []

  def amap_keyword_params_constructor(self) -> List[Iterator[AMapKeywordParameters]]:
    """
    所有城市的关键字参数迭代器组成列表
    """
    city_num = len(settings.SEARCH_AREA)
    param_constructor_list = [ParamConstructor(i, settings.SEARCH_AREA[i]) for i in range(city_num)]
    return [param.amap_keyword_params() for param in param_constructor_list]
  
  async def keyword_worker(self, sem: asyncio.Semaphore, client: AMapApiClient, 
                        session: aiohttp.ClientSession, params: Iterator[AMapKeywordParameters]):
    async with sem:
      try:
        result = await client.fetch_data(session, params, sem)
        await asyncio.sleep(0.3)
        self.save_data(result)
      except Exception as e:
        logging.error(f"| keyword worker error | {e}")

    
  async def KeywordDataCollect(self, param_iters : List[Iterator[AMapKeywordParameters]]):
    client = AMapApiClient(api_name='AMAP', search_mode='keyword')
    sem = asyncio.Semaphore(settings.MAX_REQUESTS_PRE_SECOND)

    print("/****************** Collecting Data... ******************/")
    async with aiohttp.ClientSession() as session:
      tasks = [self.keyword_worker(sem=sem, client=client, 
                              session=session, params=params) for params in param_iters]
      for task in tqdm_asyncio.as_completed(tasks, desc="Data Collecting", ncols=100, ascii=True):
          await task

  def save_data(self, df_list : List[pd.DataFrame]):
    print()
    for df in df_list:
      if df.empty:
        print("Empty DataFrame")
        return
      dirname = ParamConstructor.get_path(df.loc[0, "area"])
      types = df.mid_category[0] + "_" + df.sub_category[0]
      filename = dirname + types + ".xlsx"
      filename = re.sub(r'[|]', '_', filename)
      if not os.path.exists(dirname):
        os.makedirs(dirname)
      try:
        print(f"Saving data to excel {filename}")
        df.to_excel(filename, index=False)
      except Exception as e:
        print(f"Error in saving data to excel {filename}")
        logging.error(f"| save data error | {e}")

  def search_process(self):
    amap_param_iter_list = self.amap_keyword_params_constructor()
    asyncio.run(self.KeywordDataCollect(amap_param_iter_list))


if __name__ == "__main__":
  print("Start Collecting Datas...")
  DataCollector().search_process()