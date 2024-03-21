from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from firebase_admin import credentials, initialize_app, db
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from typing import Optional
import logging
import os
import subprocess
import time
import sys
import json
import datetime
import base64
import requests
import base64

from cipher import AES_cipher
from config import *
from teams import TeamsWebhook

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

class ClockIn104Bot:
    def __init__(self, username: Optional[str], password: Optional[str], aes_key: str):
        self.cookie_str = ''
        self.username = username
        self.password = password
        self.cipher = AES_cipher(aes_key)

        cred = credentials.Certificate(os.path.join(__location__, './firebase-cred.json'))
        self.firebase_app = initialize_app(cred, {
            'databaseURL': 'https://bot-104-default-rtdb.firebaseio.com'
        })

        logging.basicConfig(level=logging.INFO)

        self.driver = self.init_driver()

    def get_workday(self) -> bool:
        current_date = datetime.datetime.now()
        date_str = current_date.strftime('%Y%m%d')
        year = current_date.year
        response = requests.get(f'https://cdn.jsdelivr.net/gh/ruyut/TaiwanCalendar/data/{year}.json')
        data = response.json()
        day_info = next((item for item in data if item['date'] == date_str), None)
        if day_info and day_info['isHoliday']:
            logging.info(f"[Day check] Today {date_str} is a holiday.")
            return False
        else:
            logging.info(f"[Day check] Today {date_str} is a workday.")
            return True

    def init_driver(self):
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

    def wait_get_otp(self, timeout=60):
        logging.info('[OTP] Try get OTP from mail.')

        # Initial call to get the OTP
        result = subprocess.run(["shortcuts", "run", "Get otp"], capture_output=True, text=True, check=True)
        old_otp = result.stdout.strip()

        # Start time for timeout
        start_time = time.time()

        # Loop until the OTP changes or timeout
        while True:
            # Check for timeout to prevent infinite loop
            if (time.time() - start_time) > timeout:
                logging.error("[OTP] Timeout reached without getting a new OTP.")
                return None

            # Execute the command again to get a potentially updated OTP
            result = subprocess.run(["shortcuts", "run", "Get otp"], capture_output=True, text=True, check=True)
            new_otp = result.stdout.strip()

            # If the OTP has changed (or if it's the first time receiving an OTP), return it
            if new_otp and new_otp != old_otp:
                logging.info("[OTP] OTP updated.")
                return new_otp

            # Wait for a second before trying again
            time.sleep(1)

    def xpath_by_text(self, tag, text):
        # There should be no text contains quotes.
        # text = text.replace('"', '\\"')
        return f"//{tag}[contains(text(), '{text}')]"

    def login_password(self):
        logging.info('[Login] Start to login 104.')

        # Go to the login page. If the user is already logged in, the webpage will
        # be soon redirected to the clock-in page. Since the login form still
        # shows temporarily in this case, we could not determine if the user is not
        # logged in even if the login form appears.
        urlLogin = 'https://pro.104.com.tw/psc2'
        self.driver.get(urlLogin)

        # Wait for something happens.
        xpath_cookie = '|'.join([
            self.xpath_by_text('span', Text.CLOCK_IN_EN),
            self.xpath_by_text('span', Text.CLOCK_IN_TC),
            self.xpath_by_text('div', Text.CLOCK_IN_EN),
            self.xpath_by_text('div', Text.CLOCK_IN_TC),
            self.xpath_by_text('div', Text.LOGIN_PROMPT)
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
        btnLogin = self.driver.find_element(By.XPATH, self.xpath_by_text('button', ' 立即登入 '))
        WebDriverWait(self.driver, Config.TIMEOUT_OPERATION).until(
            EC.element_to_be_clickable((By.XPATH, self.xpath_by_text('button', ' 立即登入 ')))
        )

        # Submit form.
        btnLogin.click()
        logging.info('[Login] Login form submitted. Waiting for redirect.')

        # Wait for something happens.
        xpath = '|'.join([self.xpath_by_text('div', e) for e in Text.WRONG_PASSWORDS] +
                         [self.xpath_by_text('span', Text.CLOCK_IN_EN),
                          self.xpath_by_text('span', Text.CLOCK_IN_TC),
                          self.xpath_by_text('div', Text.CLOCK_IN_TC),
                          self.xpath_by_text('div', Text.EMAIL_VERIFY)])

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

    def login_email_verify(self):
        # Wait until the '身分驗證' text is available.
        WebDriverWait(self.driver, Config.TIMEOUT_OPERATION).until(
            EC.presence_of_element_located((By.XPATH, self.xpath_by_text('div', Text.EMAIL_VERIFY)))
        )

        logging.info('[OTP] Try get OTP.')
        code = self.wait_get_otp()
        logging.info(f'[OTP] OTP you have is {code}')

        # Fill username and password inputs.
        inputUsername = self.driver.find_element(By.XPATH, '//*[@id="app"]/div[2]/div[2]/div[2]/div[3]/div[2]/div[1]/input')
        inputUsername.send_keys(code)

        # Submit form.
        btnLoginWithLink = self.driver.find_element(By.XPATH, self.xpath_by_text('button', ' 驗證 '))
        WebDriverWait(self.driver, Config.TIMEOUT_OPERATION).until(
            EC.element_to_be_clickable((By.XPATH, self.xpath_by_text('button', ' 驗證 ')))
        )
        btnLoginWithLink.click()
        logging.info('[OTP] OTP sent.')

        # Wait until the page is redirect.
        WebDriverWait(self.driver, Config.TIMEOUT_OPERATION).until(
            EC.url_to_be('https://pro.104.com.tw/psc2')
        )

    def clear_cookies(self):
        logging.info('[Cookie] Start to clear cookie.')

        try:
            ref = db.reference('104/cookie', app=self.firebase_app)
            ref.set("")
            logging.info('[Cookie] Cookie cleared.')
        except Exception as e:
            # Suppress error.
            logging.warning('[Cookie] Failed to clear cookie: ' + str(e))

    def save_cookies(self):
        logging.info('[Cookie] Start to save cookie.')

        try:
            cookies = self.driver.get_cookies()
            json_data = {
                'username': self.username,
                'password': self.password,
                'cookies': cookies
            }

            encrypted = self.cipher.encrypt(json.dumps(json_data))
            ref = db.reference('104/cookie', app=self.firebase_app)
            ref.set(encrypted)
            logging.info('[Cookie] Cookie saved.')
        except Exception as e:
            # Suppress error.
            logging.warning('[Cookie] Failed to save cookie: ' + str(e))

    def get_cookies(self) -> dict:
        ref = db.reference('104/cookie', app=self.firebase_app)
        cookie = ref.get()
        if cookie:
            return json.loads(self.cipher.decrypt(cookie))
        else:
            raise Exception("No cookie on the database.")

    def load_cookies(self):
        logging.info('[Cookie] Start to load cookies.')

        # Connect to dummy page.
        url_home = 'https://marketing.pro.104.com.tw/index.html'
        self.driver.get(url_home)

        # Try to load cookies.
        try:
            json_cookie = self.get_cookies()
            cookies = json_cookie['cookies']

            # If username or password is not explicitly set, load from credential.
            self.username = json_cookie.get('username', self.username)
            self.password = json_cookie.get('password', self.password)

            for cookie in cookies:
                self.driver.add_cookie(cookie)

            cookie_str = '; '.join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
            self.cookie_str = cookie_str

            logging.info('[Cookie] Cookies loaded.')
        except Exception as e:
            # Cannot load cookies; ignore. This may be due to invalid cookie string pattern.
            logging.warning('[Cookie] Failed to load cookies: ' + str(e))

    def send_clock_in(self):
        headers = {
            'authority': 'pro.104.com.tw',
            'accept': 'application/json',
            'accept-language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'content-length': '0',
            'content-type': 'application/json',
            'cookie': self.cookie_str,
            'dnt': '1',
            'origin': 'https://pro.104.com.tw',
            'referer': 'https://pro.104.com.tw/psc2',
            'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'x-request': 'JSON',
            'x-requested-with': 'XMLHttpRequest'
        }

        response = requests.post('https://pro.104.com.tw/psc2/api/f0400/newClockin', headers=headers)

        if not response.ok:
            return ExitCode.UNKNOWN_ERROR
        return ExitCode.SUCCESS

    def start_bot(self) -> int:
        r = self.get_workday()
        if r == False:
            logging.info('[Bot] Holiday, skip check-in')
            return ExitCode.SKIP_CLOCK_IN
        else:
            logging.info('[Bot] Continue to check-in')

        self.load_cookies()

        result = self.login_password()
        if result == ExitCode.NEED_EMAIL_AUTH:
            # Login failed. Email verification required.
            result = self.login_email_verify()

        if result is not None:
            # Failed to login.
            return result

        # Now we are logged in.

        # Save cookies.
        self.save_cookies()  # never raise error

        logging.info('[Bot] Cookie saved.')

        # Receive coins.
        return self.send_clock_in()

if __name__ == "__main__":
    if len(sys.argv) == 5:
        teams_hook_url = sys.argv[4]
    elif len(sys.argv) == 4:
        teams_hook_url = None
    else:
        print("Usage: python main.py <Username> <Password> <AES_key> [Teams_hook_url]")
        sys.exit(ExitCode.INVALID_OPTIONS)

    username = sys.argv[1]
    password = sys.argv[2]
    aes_key = sys.argv[3]

    b = ClockIn104Bot(username, password, aes_key)
    ret = b.start_bot()

    if teams_hook_url is not None:
        teams_notify = TeamsWebhook(teams_hook_url)
        try:
            teams_notify.send_message(ret)
        except Exception as e:
            # Suppress error.
            logging.warning('[Teams] Failed to send message: ' + str(e))

    sys.exit(ret)
