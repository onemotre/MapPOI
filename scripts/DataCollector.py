import os
import re
import asyncio

from tqdm.asyncio import tqdm as tqdm_asyncio
from typing import List, Iterator, Tuple
from concurrent.futures import ThreadPoolExecutor

import config.settings
from clients import *
from models import *
from toolkit.logger import collector_log as logger
from toolkit.errors import *


def get_file_dir(region: str) -> str:
    dirname = config.settings.BASE_FILE_PATH.DATA_MAIN_PATH.value + region + config.settings.BASE_FILE_PATH.DIV.value
    dirname = re.sub("[|; ]", "_", dirname)
    return dirname


def save_data(typename_df_list):
    region = typename_df_list[0][0]
    dirname = get_file_dir(region)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    for typename_df in typename_df_list:
        filename = dirname + region + "_" + typename_df[1] + '.xlsx'
        filename = re.sub("[|; ]", "_", filename)
        try:
            typename_df[2].to_excel(filename, index=False)
        except Exception as e:
            print(e)
            raise SaveDataError(filename, logger) from e


class DataCollector:
    def __init__(self, api_mode: str = "GAODE"):
        self.api_mode = api_mode
        self.data_save_dir = config.settings.BASE_FILE_PATH.DATA_MAIN_PATH.value
        self.MAX_WORK_CLIENT_PRE_SECONDS = config.settings.SPIDER_CONFIG.MAX_WORK_CLIENTS_PRE_SECONDS.value
        self.MAX_REQUESTS_PRE_SECONDS = config.settings.SPIDER_CONFIG.MAX_REQUESTS_PRE_SECONDS.value
        self.region_list = config.settings.BASE_CONFIG.SEARCH_AREA.value
        self.typename = config.settings.BASE_CONFIG.SEARCH_TYPECODES.value

    async def client_worker(self, parameter_constructor: ParamConstructor):
        clients = AMapAPIClients(api_name="GAODE", search_mode="keyword")
        region_data_list = await clients.keyword_pipline(parameter_constructor, self.typename)
        return region_data_list

    def working_clients(self, parameter_constructors):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            for parameter_constructor in parameter_constructors:
                data = loop.run_until_complete(self.client_worker(parameter_constructor))
                save_data(data)
        finally:
            loop.close()

    def client_pipline(self):
        parameter_constructors = []
        for region in self.region_list:
            parameter_constructors.append(ParamConstructor(region))

        chunk_size = len(parameter_constructors) // self.MAX_WORK_CLIENT_PRE_SECONDS
        chunks = [parameter_constructors[i: i + chunk_size] for i in range(0, len(parameter_constructors), chunk_size)]
        with ThreadPoolExecutor(max_workers=len(parameter_constructors)) as executor:
            futures = [executor.submit(self.working_clients, parameter_constructors) for parameter_constructors in
                       chunks]

            for future in futures:
                future.result()


if __name__ == "__main__":
    DataCollector().client_pipline()
