def build_action_card(e, analysis_text):
    tkr = f" ({e['ticker']})" if e.get("ticker") else ""
    form = e.get("form") or "News"
    header = f"**{e['issuer']}{tkr} — {form}**\n{e['title']}\n"
    return header + "\n" + analysis_text