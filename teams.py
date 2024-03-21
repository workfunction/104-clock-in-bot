import requests
import json
import logging

class TeamsWebhook:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_message(self, c):
        logging.debug("Calling teams hook")

        stat = "Failed"
        color = "ff7675"
        img = "https://imgur.com/13TRvJP.png"

        if c == 0:
            stat = "Finished"
            color = "55efc4"
            img = "https://imgur.com/X0s2W1I.png"

        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color,
            "summary": f"104 Check in {stat}",
            "sections": [{
                "activityTitle": f"104 Check in {stat}: {c}",
                "activitySubtitle": "",
                "activityImage": img,
                "facts": [{
                    "name": "",
                    "value": ""
                }],
                "markdown": True
            }],
            "potentialAction": [{
                "@type": "OpenUri",
                "name": "104",
                "targets": [{
                    "os": "default",
                    "uri": "https://pro.104.com.tw/psc2"
                }]
            }]
        }

        headers = {'Content-Type': 'application/json'}
        response = requests.post(self.webhook_url, data=json.dumps(payload), headers=headers)

        logging.info("[Teams] Teams hook sent.")
