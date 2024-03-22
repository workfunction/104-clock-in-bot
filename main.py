import logging
import argparse

from bot import ClockIn104Bot
from teams import TeamsWebhook

def main():
    setup_logging()
    args = parse_arguments()
    bot = initialize_bot(args)

    if args.clear_cookies:
        bot.cookie_storage.clear_cookies()

    return_code = bot.start_bot()

    if args.teams_hook_url:
        notify_teams(args.teams_hook_url, return_code)

    exit(return_code)

def setup_logging():
    logging.basicConfig(level=logging.INFO)

def parse_arguments():
    parser = argparse.ArgumentParser(description="104 Clock-in Bot")
    parser.add_argument("username", type=str, help="Your email address for 104 account")
    parser.add_argument("password", type=str, help="Your password for 104 account")
    parser.add_argument("-k", "--aes_key", type=str, help="AES key for encryption and decryption")
    parser.add_argument("-f", "--firebase_url", type=str, help="Firebase DB URL for saving cookies")
    parser.add_argument("-t", "--teams_hook_url", type=str, help="MS Teams hook URL for sending notification")
    parser.add_argument("-c", "--clear_cookies", action="store_true", help="Clear cookies on firebase")
    return parser.parse_args()

def initialize_bot(args):
    return ClockIn104Bot(args.aes_key, args.username, args.password, args.firebase_url)

def notify_teams(teams_hook_url, return_code):
    teams_notify = TeamsWebhook(teams_hook_url)
    try:
        teams_notify.send_message(return_code)
    except Exception as e:
        logging.warning('[Teams] Failed to send message: ' + str(e))

if __name__ == "__main__":
    main()
