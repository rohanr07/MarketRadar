import os, requests

def _ollama_generate(prompt, cfg):
    host = os.environ.get("OLLAMA_HOST","http://127.0.0.1:11434")
    model = cfg["llm"]["model"]
    resp = requests.post(f"{host}/api/generate", json={
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": cfg["llm"]["temperature"]},
    }, timeout=120)
    resp.raise_for_status()
    return resp.json()["response"]

def analyze_with_llm(e, hints, cfg, store):
    holdings = store.get_holdings()
    you_hold = None
    if e.get("ticker") and e["ticker"] in holdings:
        h = holdings[e["ticker"]]
        you_hold = f"You HOLD this ticker: {e['ticker']} (approx_shares={h.get('shares')})."

    prompt = f"""
You are a market event analyst. Use ONLY the provided information.

[EVENT]
source: {e.get('source')}
form_or_type: {e.get('form') or 'News'}
issuer: {e.get('issuer')}
ticker: {e.get('ticker')}
headline: {e.get('title')}
summary: {e.get('summary')}
published_utc: {e.get('published_utc')}
link: {e.get('url')}

[HINTS]
priority_reasons: {hints.get('reasons')}
keyword_boosts: {hints.get('keywords')}
{you_hold or ''}

[TASKS]
1) Briefly summarize the event in <=2 sentences.
2) Classify likely impact (dilution / activist stake / mgmt change / M&A / macro).
3) ONE action: "consider add" | "consider trim" | "consider avoid" | "watch".
4) Confidence 0–100 and 1–2 bullet reasons.
5) Always include the link.

[OUTPUT FORMAT]
Summary:
Impact:
Action:
Confidence:
Reasons:
Link:
"""
    try:
        text = _ollama_generate(prompt, cfg)
    except Exception as ex:
        text = f"LLM error: {ex}"
    return text