from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import logging
import os

from config import Config, Text, ExitCode
from util import CookieStorage
from util import get_workday, wait_get_otp, post_clock_in

def xpath_by_text(tag, text) -> str:
    # There should be no text contains quotes.
    # text = text.replace('"', '\\"')
    return f"//{tag}[contains(text(), '{text}')]"

class ClockIn104Bot:
    def __init__(self, aes_key='', username='', password='', firebase_url=''):
        logging.basicConfig(level=logging.INFO)

        self.cookie_str = ''
        self.username = username
        self.password = password
        self.cookie_storage = CookieStorage(aes_key, {
            'firebase_url': firebase_url,
            'cred_path': Config.FB_CRED_PATH
        })
        self.driver = self._init_driver()

    def _init_driver(self):
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--window-size=1024,768')
        options.add_argument('--disable-extensions')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--lang=zh-TW')

        if os.getenv('DEBUG'):
            logging.info('[Init] Open debug port on 9222.')
            options.add_argument('--remote-debugging-port=9222')

        # Note: Ensure you have the ChromeDriver that matches your Chrome version installed and in PATH
        # Or specify the path to ChromeDriver using the `executable_path` parameter in the Service constructor
        service = Service()
        return webdriver.Chrome(service=service, options=options)

    def _login_password(self):
        logging.info('[Login] Start to login 104.')

        # Go to the login page. If the user is already logged in, the webpage will
        # be soon redirected to the clock-in page. Since the login form still
        # shows temporarily in this case, we could not determine if the user is not
        # logged in even if the login form appears.
        urlLogin = 'https://pro.104.com.tw/psc2'
        self.driver.get(urlLogin)

        # Wait for something happens.
        xpath_cookie = '|'.join([
            xpath_by_text('span', Text.CLOCK_IN_EN),
            xpath_by_text('span', Text.CLOCK_IN_TC),
            xpath_by_text('div', Text.CLOCK_IN_EN),
            xpath_by_text('div', Text.CLOCK_IN_TC),
            xpath_by_text('div', Text.LOGIN_PROMPT)
        ])

        WebDriverWait(self.driver, Config.TIMEOUT_OPERATION).until(
            EC.presence_of_element_located((By.XPATH, xpath_cookie))
        )

        curr_url = self.driver.current_url
        logging.info('[Login] Currently at url: ' + curr_url)

        checkin_url = 'https://pro.104.com.tw/psc2'
        if curr_url == checkin_url:
            # The webpage is redirected to the clock-in page and therefore the
            # user must have been logged in.
            logging.info('[Login] Already logged in.')
            return

        # If username or password is not specified, the login fails.
        if not self.username or not self.password:
            logging.error('[Login] Failed to login. Missing username or password.')
            return ExitCode.WRONG_PASSWORD

        # Now try to fill the login form and submit it.
        logging.info('[Login] Try to login by username and password.')

        # Fill username and password inputs.
        inputUsername = self.driver.find_element(By.XPATH, '//*[@id="app"]/div[2]/div/div[2]/div[1]/div[2]/input')
        inputUsername.send_keys(self.username)
        inputPassword = self.driver.find_element(By.XPATH, '//*[@id="app"]/div[2]/div/div[2]/div[2]/div[2]/input')
        inputPassword.send_keys(self.password)

        # Wait until the login button is enabled.
        btnLogin = self.driver.find_element(By.XPATH, xpath_by_text('button', ' 立即登入 '))
        WebDriverWait(self.driver, Config.TIMEOUT_OPERATION).until(
            EC.element_to_be_clickable((By.XPATH, xpath_by_text('button', ' 立即登入 ')))
        )

        # Submit form.
        btnLogin.click()
        logging.info('[Login] Login form submitted. Waiting for redirect.')

        # Wait for something happens.
        xpath = '|'.join([xpath_by_text('div', e) for e in Text.WRONG_PASSWORDS] +
                         [xpath_by_text('span', Text.CLOCK_IN_EN),
                          xpath_by_text('span', Text.CLOCK_IN_TC),
                          xpath_by_text('div', Text.CLOCK_IN_TC),
                          xpath_by_text('div', Text.EMAIL_VERIFY)])

        result = WebDriverWait(self.driver, Config.TIMEOUT_OPERATION).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        text = result.text

        curr_url = self.driver.current_url

        if curr_url == checkin_url:
            # login succeeded
            logging.info('[Login] Login succeeded.')
            return
        if text in Text.WRONG_PASSWORDS:
            # wrong password
            logging.error('[Login] Login failed: wrong password.')
            return ExitCode.WRONG_PASSWORD
        if text == Text.EMAIL_VERIFY:
            # need to authenticate with email OTP
            logging.info('[Login] Login failed: go login with email OTP.')
            return ExitCode.NEED_EMAIL_AUTH

        # unknown error
        logging.debug(f'[Login] Unexpected error occurred. Fetched text by xpath: {text}')
        raise Exception('Unknown error occurred when trying to login.')

    def _login_email_verify(self):
        # Wait until the '身分驗證' text is available.
        WebDriverWait(self.driver, Config.TIMEOUT_OPERATION).until(
            EC.presence_of_element_located((By.XPATH, xpath_by_text('div', Text.EMAIL_VERIFY)))
        )

        logging.info('[OTP] Try get OTP.')
        code = wait_get_otp()
        logging.info(f'[OTP] OTP you have is {code}')

        # Fill username and password inputs.
        inputUsername = self.driver.find_element(By.XPATH, '//*[@id="app"]/div[2]/div[2]/div[2]/div[3]/div[2]/div[1]/input')
        inputUsername.send_keys(code)

        # Submit form.
        btnLoginWithLink = self.driver.find_element(By.XPATH, xpath_by_text('button', ' 驗證 '))
        WebDriverWait(self.driver, Config.TIMEOUT_OPERATION).until(
            EC.element_to_be_clickable((By.XPATH, xpath_by_text('button', ' 驗證 ')))
        )
        btnLoginWithLink.click()
        logging.info('[OTP] OTP sent.')

        # Wait until the page is redirect.
        WebDriverWait(self.driver, Config.TIMEOUT_OPERATION).until(
            EC.url_to_be('https://pro.104.com.tw/psc2')
        )

    def _load_cookies(self):
        logging.info('[Cookie] Start to load cookies.')

        # Connect to dummy page.
        url_home = 'https://marketing.pro.104.com.tw/index.html'
        self.driver.get(url_home)

        # Try to load cookies.
        try:
            json_cookie = self.cookie_storage.get_cookies()
            cookies = json_cookie['cookies']

            # If username or password is not explicitly set, load from credential.
            self.username = json_cookie.get('username', self.username)
            self.password = json_cookie.get('password', self.password)

            for cookie in cookies:
                self.driver.add_cookie(cookie)

            logging.info('[Cookie] Cookies loaded.')
        except Exception as e:
            # Cannot load cookies; ignore. This may be due to invalid cookie string pattern.
            logging.warning('[Cookie] Failed to load cookies: ' + str(e))

    def start_bot(self) -> int:
        r = get_workday()
        if r == False:
            logging.info('[Bot] Holiday, skip check-in')
            return ExitCode.SKIP_CLOCK_IN
        else:
            logging.info('[Bot] Continue to check-in')

        self._load_cookies()

        result = self._login_password()
        if result == ExitCode.NEED_EMAIL_AUTH:
            # Login failed. Email verification required.
            result = self._login_email_verify()

        if result is not None:
            # Failed to login.
            return result

        # Now we are logged in.

        # Save cookies.
        cookies = self.driver.get_cookies()
        cookie_dict = {
            'username': self.username,
            'password': self.password,
            'cookies': cookies
        }
        self.cookie_storage.save_cookies(cookie_dict)  # never raise error

        # Post 104 clock in API with logged in cookies.
        return post_clock_in(cookies)
