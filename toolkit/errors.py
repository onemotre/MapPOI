import logging

from typing import Dict, List


class AMapApiError(Exception):
    def __init__(self, data: Dict, logger: logging.Logger):
        self.infocode = data["infocode"]
        self.info = data["info"]
        super().__init__(
            f"AMapKeyword Error: infocode={self.infocode}, info={self.info}. More info: https://lbs.amap.com/api/webservice/guide/tools/info/")
        logger.error(
            f"AMapKeyword Error | infocode={self.infocode}, info={self.info}. ")


class HTTPError(Exception):
    def __init__(self, http_code: int, logger: logging.Logger):
        self.code = http_code
        super().__init__(f"HTTP Error: {self.code}")
        logger.error(f"HTTP Error |  {self.code}")


class ClientSettingError(Exception):
    def __init__(self, logger: logging.Logger):
        super().__init__("Client Settings Error")
        logger.error(f"Client Settings Error")


class ParsingError(KeyError):
    def __init__(self, city: str, types: str, logger: logging.Logger):
        super().__init__()
        logger.error(f"Parsing Error | city={city}, types={types}")


class SaveDataError(Exception):
    def __init__(self, filename: str, logger: logging.Logger):
        super().__init__("Save Data Error")
        logger.error(f"Save Data Error | file {filename}")
