import hashlib

def normalize_event(ev, store):
    if not ev or not ev.get("url"):
        return None
    uid = hashlib.sha256(f"{ev['source']}|{ev['url']}".encode("utf-8")).hexdigest()
    evn = {
        "uid": uid,
        "source": ev.get("source"),
        "title": ev.get("title","").strip(),
        "url": ev["url"],
        "published_utc": ev.get("published_utc"),
        "issuer": ev.get("issuer","").strip(),
        "ticker": (ev.get("ticker") or "").upper() or None,
        "form": ev.get("form"),
        "summary": ev.get("summary","").strip(),
    }
    return evn