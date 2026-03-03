import requests
from bs4 import BeautifulSoup
import sys

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
}
resp = requests.get("https://www.gelbeseiten.de/suche/maler/deutschland", headers=headers)
soup = BeautifulSoup(resp.text, "html.parser")
cards = soup.select("article.mod-Treffer")

for card in cards[:2]:
    print("--- CARD ---")
    print(card.prettify())

