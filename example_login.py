# -*- coding: utf-8 -*-
# @Time    : 2023/7/20 22:25
# @Author  : Histranger
# @File    : example_login.py
# @Software: PyCharm
import logging
import os
import random
import time
from functools import wraps
from typing import List, Callable, Optional, Dict
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from twocaptcha import TwoCaptcha

from chrome_crawler import ChromeCrawler

env_file = Path(__file__).parent / '.env'
load_dotenv(env_file)

logging.basicConfig(level=logging.INFO)


def timer(f: Callable):
    @wraps(f)
    def _f(*args, **kwargs):
        t0 = time.perf_counter()
        ret = f(*args, **kwargs)
        logging.info(f'[{os.getpid()}] Run [{_f.__name__}], time consumption = {time.perf_counter() - t0:.2f}s')
        return ret

    return _f


@timer
def solve_reCaptcha_v2(site_key: str, url: str) -> Optional[Dict]:
    api_key = os.getenv('APIKEY_2CAPTCHA', 'YOUR_API_KEY')
    solver = TwoCaptcha(api_key)

    try:
        result = solver.recaptcha(sitekey=f'{site_key}', url=f'{url}')
    except Exception as e:
        logging.warning(repr(e))
        return None
    else:
        if isinstance(result, dict):
            return result

        result = eval(result)
        if isinstance(result, dict):
            return result

        logging.warning(f"result's type is not Dict. | {result}")
        return None


class EtherscanCrawler:
    etherscan_login_url: str = "https://etherscan.io/login"
    explicitly_wait_time: int = 10
    username: str = os.getenv("ETHERSCAN_USERNAME", 'foo')
    password: str = os.getenv("ETHERSCAN_PASSWORD", 'bar')

    def __init__(self, *args, **kwargs):
        self.cc = ChromeCrawler(*args, **kwargs)
        self.driver = self.cc.driver

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.cc.close()

    def login_manual(self) -> bool:
        """
        login in etherscan.io bypass reCaptcha by manual.
        """
        ok, msg = self.cc.try_get(self.etherscan_login_url)
        if not ok:
            logging.error(f"login failed. | {msg}")
            return False

        # If the loaded html source code not contains all the keywords, we define it failed.
        login_keywords: List[str] = ['Etherscan', 'LOGIN']
        if any(_ not in self.driver.page_source for _ in login_keywords):
            logging.error('Login failed. | keyword error.')
            return False

        # wait until reCAPTCHA appear
        try:
            WebDriverWait(self.driver, self.explicitly_wait_time).until(
                EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_captchaDiv'))
            )
        except Exception as e:
            logging.error(f'Login failed. | {repr(e)}')
            return False

        # Username
        self.driver.find_element(By.ID, 'ContentPlaceHolder1_txtUserName').send_keys(self.username)

        # Password
        self.driver.find_element(By.ID, 'ContentPlaceHolder1_txtPassword').send_keys(self.password)

        # reCAPTCHA ==> need manual operation
        class RECAPTCHAChecker:
            # https://selenium-python.readthedocs.io/waits.html
            def __init__(self, locator, attr):
                self.locator = locator
                self.attr = attr

            def __call__(self, driver):
                element = driver.find_element(*self.locator)  # Finding the referenced element
                if element.get_attribute(self.attr) == 'true':
                    return element
                else:
                    return False

        # switch to another iframe
        iframe = self.driver.find_element(By.CSS_SELECTOR, '#ContentPlaceHolder1_captchaDiv iframe')
        self.driver.switch_to.frame(iframe)

        # click check box
        self.driver.find_element(By.ID, 'recaptcha-anchor').click()

        try:
            # Attention: We need to wait more time until manual solve captcha
            reCaptcha_element = WebDriverWait(self.driver, self.explicitly_wait_time * 100).until(
                RECAPTCHAChecker(locator=(By.ID, 'recaptcha-anchor'), attr='aria-checked')
            )
        except Exception as e:
            logging.error(f'get reCaptcha element failed | {repr(e)}')
            return False

        # switch to main
        self.driver.switch_to.default_content()

        # LOGIN ==> common click may not work
        # self.driver.find_element(By.ID, 'ContentPlaceHolder1_btnLogin').click()
        login_button = self.driver.find_element(By.ID, 'ContentPlaceHolder1_btnLogin')
        self.driver.execute_script("arguments[0].click();", login_button)
        time.sleep(random.uniform(2, 3))

        # Do Check the Account url after redirect
        if self.driver.current_url != 'https://etherscan.io/myaccount':
            logging.error("login failed. | not myaccount site.")
            return False

        time.sleep(random.uniform(1, 2))
        logging.info("Login succeed.")
        return True

    def login(self) -> bool:
        """
        login in etherscan.io bypass reCaptcha by 2captcha.
        """
        ok, msg = self.cc.try_get(self.etherscan_login_url)
        if not ok:
            logging.error(f"login failed. | {msg}")
            return False

        # If the loaded html source code not contains all the keywords, we define it failed.
        login_keywords: List[str] = ['Etherscan', 'LOGIN']
        if any(_ not in self.driver.page_source for _ in login_keywords):
            logging.error('Login failed. | keyword error.')
            return False

        # wait until reCAPTCHA appear
        try:
            WebDriverWait(self.driver, self.explicitly_wait_time).until(
                EC.presence_of_element_located((By.ID, 'ContentPlaceHolder1_captchaDiv'))
            )
        except Exception as e:
            logging.error(f'Login failed. | {repr(e)}')
            return False

        # Username
        self.driver.find_element(By.ID, 'ContentPlaceHolder1_txtUserName').send_keys(self.username)

        # Password
        self.driver.find_element(By.ID, 'ContentPlaceHolder1_txtPassword').send_keys(self.password)

        # get site-key
        site_key = self.driver.find_element(By.CSS_SELECTOR, 'div.g-recaptcha'). \
            get_attribute('data-sitekey').strip()
        _url = self.driver.current_url
        # if _url.startswith('https'):
        #     _url = 'http' + _url.removeprefix('https')
        logging.info(f"site-key[{site_key}], url[{_url}]")

        if v2_result := solve_reCaptcha_v2(site_key=site_key, url=_url):
            captcha_code = v2_result.get('code', None)
        else:
            logging.error(f"get reCaptcha v2 code failed.")
            return False

        if captcha_code is None:
            logging.error(f"parse v2_result failed. | {v2_result}")
            return False

        textarea_ele = self.driver.find_element(By.CSS_SELECTOR, 'textarea[name="g-recaptcha-response"]')
        # remove style
        self.driver.execute_script("arguments[0].removeAttribute('style')", textarea_ele)
        # send keys
        textarea_ele.send_keys(captcha_code)
        time.sleep(random.uniform(1, 2))

        # LOGIN ==> common click may not work
        self.driver.find_element(By.ID, 'ContentPlaceHolder1_btnLogin').click()
        # login_button = self.driver.find_element(By.ID, 'ContentPlaceHolder1_btnLogin')
        # self.driver.execute_script("arguments[0].click();", login_button)
        time.sleep(random.uniform(2, 3))

        # Do Check the Account url after redirect
        if self.driver.current_url != 'https://etherscan.io/myaccount':
            logging.error("login failed. | not myaccount site.")
            return False

        time.sleep(random.uniform(1, 2))
        logging.info("Login succeed.")
        return True


if __name__ == '__main__':
    # Google Chrome Version 116
    with EtherscanCrawler(headless=False, driver_path='./chromedriver/v116/chromedriver.exe') as ec:
        # ec.login()
        ec.login_manual()
        input("Press Enter to stop.")
