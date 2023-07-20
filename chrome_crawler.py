# -*- coding: utf-8 -*-
# @Time    : 2023/7/20 14:59
# @Author  : Histranger
# @File    : chrome_crawler.py
# @Software: PyCharm
import copy
import logging
import time
from typing import *
from dataclasses import dataclass

from selenium import webdriver
from selenium.common import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


@dataclass
class ChromeCrawlerConfig:
    implicitly_wait: int = 3
    explicitly_wait: int = 5


class ChromeCrawler:

    def __init__(self, headless: bool = True, debug: bool = False, proxy: Optional[Dict] = None, driver_path: Optional[str] = None):
        """
        :param headless: 是否使用无头模式
        :param debug: 是否开启调试模式
        :param proxy: 是否开启代理，proxy必须是一个字典，且键必须包含ip和port
        :param driver_path: 是否使用自定义chromedriver_path
        """
        self.driver_path = driver_path
        self.headless = headless
        self.debug = debug
        self.proxy = copy.deepcopy(proxy)

        self.chrome_options = Options()

        if self.debug:
            self.chrome_options.add_argument('--remote-debugging-port=9222')
            logging.info("Debug Mode, remote debugging port is 9222.")

        if self.headless:
            self.chrome_options.add_argument('--no-sandbox')
            self.chrome_options.add_argument('--disable-dev-shm-usage')
            self.chrome_options.add_argument('--headless')  # open headless mode
            self.chrome_options.add_argument("--disable-gpu")  # disable gpu

        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
        self.chrome_options.add_argument("--incognito")
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        self.chrome_options.add_argument("--disable-blink-features=AutomationControlled")

        if self.proxy:
            assert 'ip' in self.proxy and 'port' in self.proxy, "proxy must be a dict with key ip and port."
            self.chrome_options.add_argument(f"--proxy-server={proxy['ip']}:{proxy['port']}")

        if self.driver_path:
            logging.info(f"Use ChromeDriver[{self.driver_path}].")
        else:
            self.chromedriver_manager = ChromeDriverManager()
            self.driver_path = self.chromedriver_manager.install()

        self.service = Service(self.driver_path)
        self.driver = webdriver.Chrome(service=self.service, options=self.chrome_options)
        self.driver.implicitly_wait(ChromeCrawlerConfig.implicitly_wait)

        logging.info("ChromeCrawler Started.")

    def close(self):
        self.driver.quit()
        logging.info("ChromeCrawler Closed.")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __repr__(self):
        return f"ChromeCrawler(headless={self.headless}, debug={self.debug}, proxy={self.proxy})"

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
    with ChromeCrawler(headless=False, driver_path=r".\chromedriver\v116\chromedriver.exe") as cc:
        ret = cc.try_get('https://etherscan.io/address/0xdafea492d9c6733ae3d56b7ed1adb60692c98bc5')
        print(ret)
        input()
