# -*- coding: utf-8 -*-
# @Time    : 2023/7/21 15:49
# @Author  : Histranger
# @File    : captcha_solver.py
# @Software: PyCharm
import logging
import os
from pathlib import Path
from typing import Optional, Callable, Dict, Protocol, Union, Type

from dotenv import load_dotenv
from twocaptcha import TwoCaptcha

env_file = Path(__file__).parent / '.env'
load_dotenv(env_file)


class CaptchaSolver(Protocol):

    def solve(self, site_key: str, url: str, *args, **kwargs):
        pass


class RecaptchaV2Solver:
    """
    A Google reCaptcha v2 solver based on 2Captcha.
    """

    def __init__(self):
        self.api_key = os.getenv('APIKEY_2CAPTCHA', 'YOUR_API_KEY')
        self.solver = TwoCaptcha(apiKey=self.api_key)

    def __repr__(self):
        return "RecaptchaV2Solver()"

    def solve(self, site_key: str, url: str, *args, **kwargs) -> Optional[str]:
        """
        尝试使用2captcha解决验证码，成功则返回code，失败则返回None
        :param site_key: iframe的sitekey
        :param url: 一般为current_url
        """
        try:
            result = self.solver.recaptcha(sitekey=site_key, url=url, *args, **kwargs)
            result = eval(result)
        except Exception as e:
            logging.warning(f"solve failed. | {repr(e)}")
            return None
        else:
            if isinstance(result, dict):
                code = result.get('code', None)
                if code is None:
                    logging.warning(f"can not get code from result. | {result}")
                return code
            else:
                logging.warning(f"result is not dict. | {result}, {type(result)}")
                return None


class CloudflareSolver:
    """
    A Cloudflare Turnstile solver based on 2Captcha.
    """

    def __init__(self):
        self.api_key = os.getenv('APIKEY_2CAPTCHA', 'YOUR_API_KEY')
        self.solver = TwoCaptcha(apiKey=self.api_key)

    def __repr__(self):
        return "CloudflareSolver()"

    def solve(self, site_key: str, url: str, **kwargs) -> Optional[str]:
        """
        尝试使用2captcha解决验证码，成功则返回code，失败则返回None
        :param site_key: iframe的sitekey
        :param url: 一般为current_url
        """
        try:
            result = self.solver.turnstile(sitekey=site_key, url=url, **kwargs)
            result = eval(result)
        except Exception as e:
            logging.warning(f"solve failed. | {repr(e)}")
            return None
        else:
            if isinstance(result, dict):
                code = result.get('code', None)
                if code is None:
                    logging.warning(f"can not get code from result. | {result}")
                return code
            else:
                logging.warning(f"result is not dict. | {result}, {type(result)}")
                return None


def get_solver(type_: str) -> CaptchaSolver:
    """
    :param type_: solver的类型，现阶段仅支持：reCaptcha v2、Cloudflare
    """

    # Factory
    type2solver: Dict[str, Type[CaptchaSolver]] = {
        "reCaptcha v2": RecaptchaV2Solver,
        "Cloudflare": CloudflareSolver,
    }

    assert type_ in type2solver, f"type_ not in {list(type2solver.keys())}"

    return type2solver[type_]()


def main():
    """
    >>> solver = get_solver("foobar")
    Traceback (most recent call last):
        ...
    AssertionError: type_ not in ['reCaptcha v2', 'Cloudflare']
    >>> solver = get_solver("reCaptcha v2")
    >>> solver
    RecaptchaV2Solver()
    >>> get_solver("Cloudflare")
    CloudflareSolver()
    """


if __name__ == '__main__':
    import doctest

    doctest.testmod()
