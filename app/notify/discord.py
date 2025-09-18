import requests

class DiscordNotifier:
    def __init__(self, priority_webhook: str, watchlist_webhook: str):
        self.priority = priority_webhook
        self.watchlist = watchlist_webhook

    def _send(self, webhook, text):
        if not webhook: 
            print("[WARN] Discord webhook missing; skipping.")
            return
        try:
            requests.post(webhook, json={"content": text}, timeout=15)
        except Exception as e:
            print(f"[ERR] Discord send: {e}")

    def send_priority(self, text):  self._send(self.priority, text)
    def send_watchlist(self, text): self._send(self.watchlist, text)