import requests
import itertools
import time

SEEDS = [
    "streaming",
    "netflix",
    "disney plus",
    "prime video",
    "max",
    "apple tv",
    "canal plus",
    "vod",
    "svod",
    "films",
    "film",
    "series",
    "serie",
    "anime",
    "documentaire"
]

CHARS = list("abcdefghijklmnopqrstuvwxyz0123456789")

keywords = set()

for seed in SEEDS:
    for c in CHARS:
        query = f"{seed} {c}"

        url = "https://suggestqueries.google.com/complete/search"

        params = {
            "client": "firefox",
            "hl": "fr",
            "q": query
        }

        try:
            r = requests.get(url, params=params, timeout=10)
            data = r.json()

            for kw in data[1]:
                keywords.add(kw.lower())

            print(query, len(keywords))

            time.sleep(0.2)

        except Exception:
            pass

with open("keywords.txt", "w", encoding="utf-8") as f:
    for kw in sorted(keywords):
        f.write(kw + "\n")

print(f"{len(keywords)} keywords sauvegardés.")
