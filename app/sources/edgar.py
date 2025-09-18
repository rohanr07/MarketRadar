import os, feedparser, requests, re
from dateutil import parser as dtparse

SEC_FEED = "https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&output=atom"
SEC_TICKERS_JSON = "https://www.sec.gov/files/company_tickers.json"

class EdgarPoller:
    def __init__(self, cfg, store):
        self.cfg = cfg
        self.store = store
        self.ua = {"User-Agent": f"MarketRadar/1.0 ({os.environ.get('SEC_CONTACT_EMAIL','contact@example.com')})"}
        self.cik_map = self._load_cik_map()

    def _load_cik_map(self):
        import json, os, requests
        path = "data/company_tickers.json"
        if not os.path.exists(path):
            r = requests.get(SEC_TICKERS_JSON, headers=self.ua, timeout=30)
            r.raise_for_status()
            with open(path, "w", encoding="utf-8") as f:
                f.write(r.text)
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        m = {str(v["cik_str"]).zfill(10): {"ticker": v.get("ticker"), "title": v.get("title")} for v in raw.values()}
        return m

    def _entry_to_event(self, e):
        title = e.get("title","")
        link = e.get("link") or (e.get("links")[0]["href"] if e.get("links") else "")
        published = e.get("published") or e.get("updated")
        try:
            published_utc = dtparse.parse(published).isoformat()
        except: published_utc = None

        cik = None
        m = re.search(r"\((\d{10})\)", title)
        if m: cik = m.group(1)
        issuer = title.split("(")[0].split("-")[-1].strip()
        ticker = self.cik_map.get(cik,{}).get("ticker") if cik else None
        form = e.get("category","")

        return {
            "source": "SEC/EDGAR",
            "title": title,
            "url": link,
            "published_utc": published_utc,
            "issuer": issuer,
            "ticker": ticker,
            "form": form,
            "summary": e.get("summary","")
        }

    def poll(self):
        d = feedparser.parse(SEC_FEED, request_headers=self.ua)
        if d.bozo:
            print("[WARN] SEC feed parse issue")
            return []
        return [self._entry_to_event(en) for en in d.entries]