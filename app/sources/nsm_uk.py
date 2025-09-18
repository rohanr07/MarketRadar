import feedparser
from dateutil import parser as dtparse

NSM_FEEDS = [
    {"name": "FCA News", "url": "https://www.fca.org.uk/news/rss.xml"}
]

class NSMUKPoller:
    def __init__(self, cfg, store):
        self.cfg = cfg
        self.store = store

    def poll(self):
        items = []
        for f in NSM_FEEDS:
            d = feedparser.parse(f["url"])
            if getattr(d, "bozo", False):
                continue
            for e in d.entries:
                link = e.get("link") or (e.get("links")[0]["href"] if e.get("links") else "")
                pub = e.get("published") or e.get("updated")
                try: published_utc = dtparse.parse(pub).isoformat()
                except: published_utc = None
                items.append({
                    "source": f"NSM/RSS:{f['name']}",
                    "title": e.get("title",""),
                    "url": link,
                    "published_utc": published_utc,
                    "issuer": e.get("author","") or f["name"],
                    "ticker": None,
                    "form": None,
                    "summary": e.get("summary","")
                })
        return items