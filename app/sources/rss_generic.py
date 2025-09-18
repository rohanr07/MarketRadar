import feedparser
from dateutil import parser as dtparse

class RSSPoller:
    def __init__(self, cfg, store):
        self.cfg = cfg
        self.store = store

    def _one(self, name, url, region):
        out = []
        d = feedparser.parse(url)
        if getattr(d, "bozo", False):
            return out
        for e in d.entries:
            link = e.get("link") or (e.get("links")[0]["href"] if e.get("links") else "")
            pub = e.get("published") or e.get("updated")
            try: published_utc = dtparse.parse(pub).isoformat()
            except: published_utc = None
            out.append({
                "source": f"RSS:{name}",
                "title": e.get("title",""),
                "url": link,
                "published_utc": published_utc,
                "issuer": e.get("author","").strip() or name,
                "ticker": None,
                "form": None,
                "summary": e.get("summary","")
            })
        return out

    def poll(self):
        events = []
        for f in self.cfg.get("rss",{}).get("feeds",[]):
            events += self._one(f["name"], f["url"], f.get("region"))
        for f in self.cfg.get("rss",{}).get("company_feeds",[]):
            events += self._one(f["name"], f["url"], f.get("region"))
        return events