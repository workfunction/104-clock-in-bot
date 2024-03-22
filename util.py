import datetime
import logging
import requests
import subprocess
import time
import os
import json

from firebase_admin import credentials, initialize_app, db

from cipher import AesCipher
from config import ExitCode, Config

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

def get_workday() -> bool:
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

def wait_get_otp(timeout=60) -> str:
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
            return ""

        # Execute the command again to get a potentially updated OTP
        result = subprocess.run(["shortcuts", "run", "Get otp"], capture_output=True, text=True, check=True)
        new_otp = result.stdout.strip()

        # If the OTP has changed (or if it's the first time receiving an OTP), return it
        if new_otp and new_otp != old_otp:
            logging.info("[OTP] OTP updated.")
            return new_otp

        # Wait for a second before trying again
        time.sleep(1)

def post_clock_in(cookies) -> int:
    # Make cookies in header format
    cookie_str = '; '.join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])

    # Open json file and load the JSON data
    with open(os.path.join(__location__, Config.HEADERS_PATH), 'r') as file:
        headers = json.load(file)

    headers['cookie'] = cookie_str
    response = requests.post('https://pro.104.com.tw/psc2/api/f0400/newClockin', headers=headers)

    if not response.ok:
        return ExitCode.UNKNOWN_ERROR
    return ExitCode.SUCCESS

class FireBaseIO:
    def __init__(self, dbUrl: str, cred_path: str):
        cred = credentials.Certificate(os.path.join(__location__, cred_path))
        firebase_app = initialize_app(cred, {'databaseURL': dbUrl})
        self.ref = db.reference('104/cookie', app=firebase_app)

    def clear(self) -> None:
        try:
            self.ref.set('')
            logging.info('[Firebase] Cookie cleared.')
        except Exception as e:
            logging.warning('[Firebase] Failed to clear cookie: ' + str(e))

    def get(self) -> str:
        try:
            return self.ref.get()
        except Exception as e:
            logging.warning('[Firebase] Failed to get cookie: ' + str(e))
            return ''

    def save(self, data: str) -> None:
        try:
            self.ref.set(data)
            logging.info('[Firebase] Cookie saved.')
        except Exception as e:
            logging.warning('[Firebase] Failed to save cookie: ' + str(e))

class FileIO:
    def __init__(self, file_path=Config.COOKIE_PATH):
        self.path = os.path.join(__location__, file_path)

    def clear(self) -> None:
        if os.path.exists(self.path):
            os.remove(self.path)
            logging.info('[Files] Cookie cleared.')

    def get(self) -> str:
        try:
            with open(self.path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logging.warning('[Files] Failed to load cookie: ' + str(e))
            return ""

    def save(self, data: str) -> None:
        try:
            with open(self.path, 'w', encoding='utf-8') as file:
                file.write(data)
            logging.info('[Files] Cookie saved.')
        except Exception as e:
            logging.warning('[Files] Failed to save cookie: ' + str(e))

class CookieIO:
    def __init__(self, aes_key="", firebase_conf={}):
        try:
            self.io = FireBaseIO(firebase_conf['firebase_url'], firebase_conf['cred_path'])
        except Exception as e:
            logging.info('[Firebase] Failed to start firabase: ' + str(e))
            self.io = FileIO()

        self.cipher = None if not aes_key else AesCipher(aes_key)

    def clear_cookies(self) -> None:
        logging.info('[Cookie] Start to clear cookie.')
        self.io.clear()

    def save_cookies(self, cookie_dict) -> None:
        logging.info('[Cookie] Start to save cookie.')
        cookie_json = json.dumps(cookie_dict)
        encrypted = cookie_json

        if self.cipher:
            try:
                encrypted = self.cipher.encrypt(cookie_json)
            except Exception as e:
                logging.warning('[Cipher] Failed to encrypt cookie: ' + str(e))
                logging.warning('[Cookie] Save cookie without encryption')
        else:
            logging.warning('[Cookie] Save cookie without encryption')

        self.io.save(encrypted)

    def get_cookies(self) -> dict:
        encrypted = self.io.get()
        if not encrypted:
            raise Exception("No cookie on the database.")

        cookie = encrypted
        if self.cipher:
            try:
                cookie = self.cipher.decrypt(encrypted)
            except Exception as e:
                logging.warning('[Cipher] Failed to decrypt cookie: ' + str(e))
                logging.warning('[Cookie] Try load cookie without encryption')
        else:
            logging.warning('[Cookie] Try load cookie without encryption')

        return json.loads(cookie)
