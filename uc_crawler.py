# -*- coding: utf-8 -*-
# @Time    : 2023/7/20 14:12
# @Author  : Histranger
# @File    : uc_crawler.py
# @Software: PyCharm
import copy
import logging
import time
from typing import Dict, Optional
from dataclasses import dataclass

import undetected_chromedriver as uc
from selenium.common import WebDriverException, TimeoutException

logging.basicConfig(level=logging.INFO)


@dataclass
class UCCrawlerConfig:
    implicitly_wait: int = 3
    explicitly_wait: int = 5


class UCCrawler:
    """
    An undetected chromedriver base on undetected-chromedriver.
    自动下载的driver缓存，在win下一般在：~/appdata/roaming/undetected_chromedriver.
    具体的位置可见源码：https://github.com/ultrafunkamsterdam/undetected-chromedriver/blob/d29b3e300fe75aa878e0313bce37a1816d6bd4c0/undetected_chromedriver/patcher.py#L43C12-L43C12
    当出现driver问题时，可以手动清除缓存。
    """

    def __init__(self, headless: bool = True, proxy: Optional[Dict] = None,
                 driver_path: Optional[str] = None, *args, **kwargs):
        """
        :param headless: 是否使用无头模式
        :param proxy: 是否开启代理，proxy必须是一个字典，且键必须包含ip和port
        :param driver_path: 是否指定chromedriver，一般当你的chrome版本过新时，需要手动下载，可以到这里看看：https://googlechromelabs.github.io/chrome-for-testing/#stable
        """
        self.headless = headless
        self.proxy = copy.deepcopy(proxy)
        self.driver_path = driver_path

        self.opts = uc.ChromeOptions()

        if self.headless:
            self.opts.add_argument('--no-sandbox')
            self.opts.add_argument('--disable-dev-shm-usage')
            self.opts.add_argument('--headless')  # open headless mode
            self.opts.add_argument("--disable-gpu")  # disable gpu

        self.opts.add_argument("--incognito")
        self.opts.add_argument("--start-maximized")
        self.opts.add_argument("--disable-extensions")

        if self.proxy:
            assert 'ip' in self.proxy and 'port' in self.proxy, "proxy must be a dict with key ip and port."
            self.opts.add_argument(f"--proxy-server={proxy['ip']}:{proxy['port']}")

        if self.driver_path:
            logging.info(f"Use ChromeDriver[{self.driver_path}].")
            self.driver = uc.Chrome(headless=self.headless, options=self.opts,
                                    executable_path=self.driver_path,
                                    use_subprocess=True, *args, **kwargs)
        else:
            self.driver = uc.Chrome(headless=self.headless, options=self.opts,
                                    use_subprocess=True, *args, **kwargs)
        self.driver.implicitly_wait(UCCrawlerConfig.implicitly_wait)

        logging.info("UCCrawler Started.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __repr__(self):
        return f"UCCrawler(headless={self.headless}, proxy={self.proxy})"

    def close(self):
        self.driver.close()
        logging.info("UCCrawler Closed.")

    def try_get(self, url: str, interval: float = 0.2, retries: int = 3,
                key_msg: str = None, err_msg: str = 'ERR_') -> (bool, str):
        """
        尝试访问url
        :param url: 网址
        :param interval: 尝试间隔
        :param retries: 尝试次数
        :param key_msg: 关键词
        :param err_msg: 错误信息
        :return: 是否成功访问url，详细信息
        """
        ok: bool = True
        msg: str = ""

        index = 0
        while index < retries:
            if index:
                time.sleep(interval)
            index += 1

            try:
                self.driver.get(url)
            except (WebDriverException, TimeoutException) as e:
                ok, msg = False, repr(e)
                continue
            else:
                # 如果页面中存在key_msg，那么访问成功
                if key_msg:
                    if key_msg in self.driver.page_source:
                        ok, msg = True, f"key_msg[{key_msg}] in page source."
                        break
                    else:
                        ok, msg = False, f"key_msg[{key_msg}] NOT in page source."
                        continue
                # 如果错误信息err_msg在页面中
                if err_msg in self.driver.page_source:
                    ok, msg = False, f"err_msg[{err_msg}] in page source."
                    continue
                else:
                    ok, msg = True, f"get url[{url}] OK."
                    break
        return ok, msg


if __name__ == '__main__':
    with UCCrawler(headless=False, driver_path='./chromedriver/v116/chromedriver.exe') as uc:
        uc.driver.get('https://etherscan.io/address/0x1f9090aae28b8a3dceadf281b0f12828e676c326')
        input()
