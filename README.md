# CrawlerEngine

A Python3 code template while crawling website by `Selenium` and so on.

## Some usage Hints

### 1. Switch iframe
```python
# import By
from selenium.webdriver.common.by import By
# first, find the iframe element
iframe_ele = driver.find_element(By.CSS_SELECTOR, '#ContentPlaceHolder1_captchaDiv iframe')
# second, switch to it
driver.switch_to.frame(iframe)
# finally, switch to main
driver.switch_to.default_content()
```
### 2. Explicitly wait
```python
# import dependencies 
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
# wait until element appear
try:
    WebDriverWait(driver, explicitly_wait_time).until(
        EC.presence_of_element_located(
            (By.ID, 'ContentPlaceHolder1_captchaDiv'))
    )
except Exception as e:
    print(repr(e))
```
- [More EC.method()](https://www.selenium.dev/selenium/docs/api/py/webdriver_support/selenium.webdriver.support.expected_conditions.html)

上述代码中，Selenium 最多等待 `explicitly_wait_time` 秒，如果在该时间内未找到任何元素，那么触发`TimeoutException`。默认情况下，每`500ms`调用一次检查函数。

自定义检查（Conditions）:
```python
class RECAPTCHAChecker:
    def __init__(self, locator, attr):
        self.locator = locator
        self.attr = attr
        
    def __call__(self, driver):
        element = driver.find_element(*self.locator)  # Finding the referenced element
        if element and element.get_attribute(self.attr) == 'true':
            return element
        else:
            return False
...
try:
    reCAPTCHA_element = WebDriverWait(driver, reCAPTCHA_wait_time).until(
        RECAPTCHAChecker((By.ID, 'recaptcha-anchor'), "aria-checked")  # the first param is Tuple
    )
except Exception as e:
    logger.error(f'Login failed. | {repr(e)}')
```
- [Code Reference](https://selenium-python.readthedocs.io/waits.html)

### 3. Code with 2captcha

```text
pipenv install 2captcha-python
```

```python
from twocaptcha import TwoCaptcha

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
```
- [Code Reference](https://cn.2captcha.com/2captcha-api#solving_recaptchav2_new)

需要寻找 `site-key`，一般在`div.g-recaptcha`下：
```html
<div class="g-recaptcha" data-sitekey="6Le1YycTAAAAAJXqwosyiATvJ6Gs2NLn8VEzTVlS">
```
`url` 一般设置为`driver.current_url`。

**详细的例子见 `example_login.py`**，这个例子综合了`1~4`。

### 4. Click not work
在某些情况下，元素的`click`方法可能不可交互，这时需要执行`JS`脚本：
```python
login_button = driver.find_element(By.ID, 'ContentPlaceHolder1_btnLogin')
driver.execute_script("arguments[0].click();", login_button)
```
