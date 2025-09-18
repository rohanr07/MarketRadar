import os, yaml

def load_dotenv(path=".env"):
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            k, v = s.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

from app.scheduler import Scheduler
from app.storage import Storage
from app.notify.discord import DiscordNotifier

CONFIG_PATH = "config.yaml"

def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    load_dotenv()  # NEW: read .env into os.environ
    cfg = load_config()

    store = Storage(db_path="storage/radar.db")

    notifier = DiscordNotifier(
        priority_webhook=os.environ.get(cfg["notifiers"]["discord"]["priority_webhook_env"], ""),
        watchlist_webhook=os.environ.get(cfg["notifiers"]["discord"]["watchlist_webhook_env"], "")
    )

    sched = Scheduler(cfg, store, notifier)
    print("[OK] Market Radar started.")
    sched.run_forever()

if __name__ == "__main__":
    main()