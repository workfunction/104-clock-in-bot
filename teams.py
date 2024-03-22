import requests
import json
import logging

class TeamsWebhook:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_message(self, return_code):
        logging.debug("Calling Teams webhook")

        status = "Failed"
        color = "ff7675"
        img = "https://imgur.com/13TRvJP.png"

        if return_code == 0:
            status = "Finished"
            color = "55efc4"
            img = "https://imgur.com/X0s2W1I.png"

        payload = self._build_payload(status, return_code, color, img)
        headers = {'Content-Type': 'application/json'}

        try:
            response = requests.post(self.webhook_url, data=json.dumps(payload), headers=headers)
            response.raise_for_status()  # Raise an exception for HTTP errors
            logging.info("[Teams] Teams webhook sent.")
        except requests.RequestException as e:
            logging.error(f"[Teams] Failed to send Teams webhook: {e}")

    def _build_payload(self, status, return_code, color, img):
        return {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color,
            "summary": f"104 Check-in {status}",
            "sections": [{
                "activityTitle": f"104 Check-in {status}: {return_code}",
                "activitySubtitle": "",
                "activityImage": img,
                "facts": [],
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
