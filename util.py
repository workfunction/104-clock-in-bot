import datetime
import logging
import requests
import subprocess
import time
import os
import json

from abc import ABC, abstractmethod

from cipher import AesCipher
from config import ExitCode, Config

__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

def get_workday() -> bool:
    try:
        date_str = datetime.datetime.now().strftime('%Y%m%d')
        year = datetime.datetime.now().year

        response = requests.get(f'https://cdn.jsdelivr.net/gh/ruyut/TaiwanCalendar/data/{year}.json')
        response.raise_for_status()  # Raise an exception for HTTP errors

        day_info = next((item for item in response.json() if item['date'] == date_str), None)

        logging.info(f"[Day check] Today {date_str} is {'a holiday' if day_info and day_info.get('isHoliday') else 'a workday'}.")
        return not (day_info and day_info.get('isHoliday', False))

    except Exception as e:
        logging.error(f"[Day check] Error occurred: {e}")
        return False

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
            raise Exception("[OTP] Timeout reached without getting a new OTP.")

        # Execute the command again to get a potentially updated OTP
        result = subprocess.run(["shortcuts", "run", "Get otp"], capture_output=True, text=True, check=True)
        new_otp = result.stdout.strip()

        # If the OTP has changed (or if it's the first time receiving an OTP), return it
        if new_otp and new_otp != old_otp:
            logging.info("[OTP] OTP updated.")
            return new_otp

        # Wait for a second before trying again
        time.sleep(1)

def load_headers() -> dict:
    """
    Load headers from a JSON file.

    Returns:
        dict: The loaded headers.
    """
    try:
        with open(os.path.join(__location__, Config.HEADERS_PATH), 'r') as file:
            return json.load(file)
    except Exception as e:
        logging.error(f"Failed to load headers: {e}")
        return {}

def post_clock_in(cookies) -> int:
    """
    Posts a clock-in request to a specific endpoint with provided cookies.

    Args:
        cookies (list): List of dictionaries representing cookies.

    Returns:
        int: Exit code indicating the result of the operation.
    """
    try:
        headers = load_headers()
        headers['cookie'] = '; '.join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])

        response = requests.post('https://pro.104.com.tw/psc2/api/f0400/newClockin', headers=headers)

        if response.ok:
            return ExitCode.SUCCESS
        else:
            logging.error(f"Clock-in request failed with status code: {response.status_code}")
            return ExitCode.UNKNOWN_ERROR

    except Exception as e:
        logging.error(f"An error occurred during clock-in request: {e}")
        return ExitCode.UNKNOWN_ERROR

class IOBase(ABC):
    """
    Abstract base class to define the IO operations interface.
    """
    @abstractmethod
    def clear(self) -> None:
        pass

    @abstractmethod
    def get(self) -> str:
        pass

    @abstractmethod
    def save(self, data: str) -> None:
        pass

class FireBaseIO(IOBase):
    def __init__(self, dbUrl: str, cred_path: str):
        from firebase_admin import credentials, initialize_app, db
        cred = credentials.Certificate(cred_path)
        firebase_app = initialize_app(cred, {'databaseURL': dbUrl})
        self.ref = db.reference('104/cookie', app=firebase_app)
        logging.info('[Firebase] Initialization done, cookie will be saved to firebase.')

    def clear(self) -> None:
        self._safe_operation(lambda: self.ref.set(''), '[Firebase] Cookie cleared.')

    def get(self) -> str:
        return self._safe_operation(lambda: self.ref.get(), default='')

    def save(self, data: str) -> None:
        self._safe_operation(lambda: self.ref.set(data), '[Firebase] Cookie saved.')

    def _safe_operation(self, func, success_message=None, default=None):
        try:
            result = func()
            if success_message:
                logging.info(success_message)
            return result
        except Exception as e:
            logging.warning(f'[Firebase] Operation failed: {e}')
            return default

class FileIO(IOBase):
    def __init__(self, file_path):
        self.path = os.path.join(__location__, file_path)
        logging.info(f'[Files] Initialization done, cookie will be saved to {file_path}.')

    def clear(self) -> None:
        self._safe_operation(lambda: os.remove(self.path), '[Files] Cookie cleared.')

    def get(self) -> str:
        return self._safe_operation(lambda: open(self.path, 'r', encoding='utf-8').read(), default="")

    def save(self, data: str) -> None:
        self._safe_operation(lambda: open(self.path, 'w', encoding='utf-8').write(data), '[Files] Cookie saved.')

    def _safe_operation(self, func, success_message=None, default=None):
        try:
            result = func()
            if success_message:
                logging.info(success_message)
            return result
        except Exception as e:
            logging.warning(f'[Files] Operation failed: {e}')
            return default

class CookieStorage:
    """
    Manages the storage and retrieval of cookies, with optional AES encryption.
    """
    def __init__(self, aes_key="", firebase_conf={}):
        """
        Initialize the CookieStorage instance.

        :param aes_key: AES key for encryption/decryption.
        :param firebase_conf: Configuration dict for Firebase.
        """
        try:
            self.io = FireBaseIO(firebase_conf['firebase_url'], firebase_conf['cred_path'])
        except Exception as e:
            logging.info('[Firebase] Initialization failed, falling back to file storage: %s', e)
            self.io = FileIO(Config.COOKIE_PATH)

        self.cipher = None if not aes_key else AesCipher(aes_key)

    def clear_cookies(self) -> None:
        """Clears the stored cookies."""
        logging.info('[CookieStorage] Clearing cookies.')
        self.io.clear()

    def save_cookies(self, cookie_dict) -> None:
        """
        Saves cookies after optional encryption.

        :param cookie_dict: Dictionary of cookies to save.
        """
        logging.info('[CookieStorage] Saving cookies.')
        cookie_json = json.dumps(cookie_dict)
        encrypted = self._encrypt_cookie(cookie_json)
        self.io.save(encrypted)

    def get_cookies(self) -> dict:
        """Retrieves and decrypts the cookies, if necessary."""
        encrypted = self.io.get()
        if not encrypted:
            raise ValueError("No cookie in the database.")

        cookie = self._decrypt_cookie(encrypted)
        return json.loads(cookie)

    def _encrypt_cookie(self, cookie_json):
        """Encrypts the cookie if a cipher is available, for internal use."""
        if self.cipher:
            try:
                return self.cipher.encrypt(cookie_json)
            except Exception as e:
                logging.warning('[Cipher] Encryption failed: %s', e)
        logging.warning('[CookieStorage] Saving cookie without encryption')
        return cookie_json

    def _decrypt_cookie(self, encrypted):
        """Decrypts the cookie if a cipher is available, for internal use."""
        if self.cipher:
            try:
                return self.cipher.decrypt(encrypted)
            except Exception as e:
                logging.warning('[Cipher] Decryption failed: %s', e)
        logging.warning('[CookieStorage] Loading cookie without decryption')
        return encrypted
