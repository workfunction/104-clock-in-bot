import logging
import argparse

from bot import ClockIn104Bot
from teams import TeamsWebhook

def main():
    parser = argparse.ArgumentParser(description="104 Clock-in Bot")
    parser.add_argument("username", type=str, help="Your username for 104 account")
    parser.add_argument("password", type=str, help="Your password for 104 account")
    parser.add_argument("aes_key", type=str, help="AES key for encryption and decryption")
    parser.add_argument("-f", "--firebase_url", type=str, help="Firebase DB URL for saving cookies")
    parser.add_argument("-t", "--teams_hook_url", type=str, help="MS Teams hook URL for sending notification")
    parser.add_argument("-c", "--clear_cookies", action="store_true", help="Clear cookies on firebase")

    args = parser.parse_args()

    username = args.username
    password = args.password
    aes_key = args.aes_key
    firebase_url = args.firebase_url
    teams_hook_url = args.teams_hook_url
    clear_cookies = args.clear_cookies

    bot = ClockIn104Bot(aes_key, username, password, firebase_url)

    if clear_cookies:
        bot.cookie_io.clear_cookies()

    ret = bot.start_bot()

    if teams_hook_url is not None:
        teams_notify = TeamsWebhook(teams_hook_url)
        try:
            teams_notify.send_message(ret)
        except Exception as e:
            logging.warning('[Teams] Failed to send message: ' + str(e))

    exit(ret)

if __name__ == "__main__":
    main()
