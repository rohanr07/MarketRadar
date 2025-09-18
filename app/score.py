import re

def score_and_route(e, cfg, store):
    form = (e.get("form") or "").upper()
    title = (e.get("title") or "") + " " + (e.get("summary") or "")
    priority = 0
    lane = None
    hints = {"keywords": [], "reasons": []}

    for pf in cfg["routing"]["priority_forms"]:
        if pf in form or (pf == "Form 4 (purchase)" and ("FORM 4" in form and re.search(r"\bP\b", title))):
            priority = max(priority, 3)
            lane = "priority"
            hints["reasons"].append(f"priority_form:{pf}")

    for kw in cfg["routing"]["priority_keywords"]:
        if re.search(rf"\b{re.escape(kw)}\b", title, flags=re.I):
            priority = max(priority, 2)
            hints["keywords"].append(kw)
            if lane != "priority":
                lane = "priority"

    holdings = store.get_holdings()
    if e.get("ticker") and e["ticker"].upper() in holdings:
        if lane is None:
            lane = "watchlist"
            priority = max(priority, 1)
        hints["reasons"].append("user_holds")

    if lane is None:
        return ("watchlist", 1, hints) if e.get("ticker") else ("watchlist", 0, hints)

    return (lane, priority, hints)