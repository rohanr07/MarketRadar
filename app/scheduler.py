import time
from datetime import datetime, timedelta
from dateutil import tz
from app.sources.edgar import EdgarPoller
from app.sources.nsm_uk import NSMUKPoller
from app.sources.rss_generic import RSSPoller
from app.normalize import normalize_event
from app.score import score_and_route
from app.llm import analyze_with_llm
from app.actions import build_action_card

class Scheduler:
    def __init__(self, cfg, store, notifier):
        self.cfg = cfg
        self.store = store
        self.notifier = notifier
        self.tz = tz.gettz(cfg["app"]["timezone"])

        self.edgar = EdgarPoller(cfg, store)
        self.nsm = NSMUKPoller(cfg, store)
        self.rss = RSSPoller(cfg, store)

    def _handle_events(self, events):
        for ev in events:
            evn = normalize_event(ev, self.store)
            if not evn: 
                continue
            if self.store.is_duplicate(evn["uid"]):
                continue

            lane, priority, hints = score_and_route(evn, self.cfg, self.store)
            analysis = analyze_with_llm(evn, hints, self.cfg, self.store)
            card = build_action_card(evn, analysis)

            if lane == "priority":
                self.notifier.send_priority(card)
            elif lane == "watchlist":
                self.notifier.send_watchlist(card)

            self.store.save_event(evn, lane, priority, card)

    def _maybe_digest(self):
        if not self.cfg["app"]["digest"]["enabled"]:
            return
        now = datetime.now(self.tz)
        target_h, target_m = map(int, self.cfg["app"]["digest"]["time"].split(":"))
        key = now.strftime("%Y-%m-%d")
        if now.hour == target_h and now.minute == target_m:
            if self.store.digest_already_sent(key): 
                return
            text = self.store.build_digest_since(now - timedelta(days=1), self.tz)
            if text.strip():
                self.notifier.send_priority(text)
            self.store.mark_digest(key)

    def run_forever(self):
        t0 = int(time.time())
        while True:
            try:
                if (int(time.time()) - t0) % self.cfg["app"]["poll_intervals"]["edgar_sec_seconds"] == 0:
                    self._handle_events(self.edgar.poll())
                if (int(time.time()) - t0) % self.cfg["app"]["poll_intervals"]["nsm_uk_seconds"] == 0:
                    self._handle_events(self.nsm.poll())
                if (int(time.time()) - t0) % self.cfg["app"]["poll_intervals"]["rss_generic_seconds"] == 0:
                    self._handle_events(self.rss.poll())
                self._maybe_digest()
            except Exception as e:
                print(f"[ERR] loop: {e}")
            time.sleep(1)