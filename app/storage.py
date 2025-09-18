import sqlite3
from datetime import datetime
from dateutil import parser as dtparse

class Storage:
    def __init__(self, db_path):
        self.con = sqlite3.connect(db_path, check_same_thread=False)
        self._init()

    def _init(self):
        c = self.con.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS events(
            uid TEXT PRIMARY KEY,
            published_utc TEXT,
            source TEXT,
            issuer TEXT,
            ticker TEXT,
            form TEXT,
            title TEXT,
            url TEXT,
            lane TEXT,
            priority INTEGER,
            card TEXT
        );""")
        c.execute("""CREATE TABLE IF NOT EXISTS digests(d TEXT PRIMARY KEY);""")
        self.con.commit()

    def is_duplicate(self, uid):
        cur = self.con.execute("SELECT 1 FROM events WHERE uid=?", (uid,))
        return cur.fetchone() is not None

    def save_event(self, evn, lane, priority, card):
        self.con.execute("""INSERT OR IGNORE INTO events
        (uid, published_utc, source, issuer, ticker, form, title, url, lane, priority, card)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (evn["uid"], evn["published_utc"], evn["source"], evn["issuer"], evn["ticker"], evn["form"],
         evn["title"], evn["url"], lane, priority, card))
        self.con.commit()

    def digest_already_sent(self, key): 
        return self.con.execute("SELECT 1 FROM digests WHERE d=?", (key,)).fetchone() is not None

    def mark_digest(self, key):
        self.con.execute("INSERT OR IGNORE INTO digests(d) VALUES(?)", (key,))
        self.con.commit()

    def build_digest_since(self, dt_from, tzinfo):
        rows = self.con.execute("""SELECT published_utc,issuer,ticker,form,title,url,lane,priority
                                   FROM events WHERE published_utc >= ? ORDER BY published_utc ASC""",
                                (dt_from.isoformat(),)).fetchall()
        if not rows: return ""
        lines = ["📰 **Daily Filings Digest (last 24h)**"]
        for (ts, issuer, tkr, form, title, url, lane, pri) in rows:
            ts_short = (ts or "")[:16]
            lines.append(f"- {ts_short} — **{issuer}**{f' ({tkr})' if tkr else ''} — *{form or 'News'}* [{lane} p{pri}]\n  {url}")
            if len("\n".join(lines)) > 3900:
                lines.append("… (truncated)")
                break
        return "\n".join(lines)

    def get_holdings(self):
        import csv, os
        path = "data/portfolio.csv"
        holdings = {}
        if not os.path.exists(path): 
            return holdings
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                tkr = (r.get("ticker") or r.get("Ticker") or r.get("Instrument") or "").strip()
                if not tkr: 
                    continue
                sh = r.get("approx_shares") or r.get("Quantity") or r.get("Shares") or ""
                try: sh = float(str(sh).split()[0])
                except: sh = None
                holdings[tkr.upper()] = {"shares": sh}
        return holdings