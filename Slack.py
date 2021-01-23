import json
import requests

class SlackPost:

    # コンストラクタ
    def __init__(self):
        with open('webhookurl.json','r') as f:
            json_load = json.load(f)
            self.url = json_load["URL"]
    
    def WebhookSlack(self, message):
        requests.post(self.url, data=json.dumps({
            "text": message,
        }))

if __name__ == "__main__":
    slack = SlackPost()
    slack.WebhookSlack("test_test")