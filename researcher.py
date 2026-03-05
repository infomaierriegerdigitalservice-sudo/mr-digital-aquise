"""
researcher.py – Multi-Source Lead-Recherche
MR Digital – Akquise Automatisierung v2

Strategie:
1. Primär: Gelbe Seiten Web-Scraping (kein Playwright nötig)
2. Fallback: Wer-kennt-wen / weitere öffentliche Verzeichnisse
3. Deduplizierung über SQLite
"""

import re
import time
import random
import logging
import requests
import base64
import json
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS_POOL = [
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    },
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Accept-Language": "de-DE,de;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "keep-alive",
    },
]


# ──────────────────────────────────────
# GELBE SEITEN SCRAPER (Primärquelle)
# ──────────────────────────────────────

def _scrape_gelbeseiten(category: str, city: str = "", max_results: int = 10) -> list:
    """Scrapt gelbeseiten.de – funktioniert ohne Playwright."""
    results = []
    try:
        what = category.lower().strip().replace(" ", "-")
        where = city.lower().strip().replace(" ", "-") if city.strip() else "deutschland"

        url = f"https://www.gelbeseiten.de/suche/{what}/{where}"
        headers = random.choice(HEADERS_POOL)

        logger.info(f"[Research] Gelbe Seiten: {url}")
        resp = requests.get(url, headers=headers, timeout=20)

        if resp.status_code != 200:
            logger.warning(f"[Research] Gelbe Seiten HTTP {resp.status_code}")
            return results

        soup = BeautifulSoup(resp.text, "html.parser")

        # Mehrere mögliche Selektoren probieren
        cards = (
            soup.select("article.mod-Treffer") or
            soup.select("[data-wle-treffer]") or
            soup.select(".mod-Treffer") or
            soup.select("article[class*='Treffer']")
        )

        logger.info(f"[Research] Gelbe Seiten: {len(cards)} Karten gefunden")

        for card in cards[:max_results]:
            try:
                # Name
                name_el = (
                    card.select_one("h2.mod-Treffer--name") or
                    card.select_one(".mod-Treffer--name") or
                    card.select_one("h2[class*='name']") or
                    card.select_one("h2")
                )
                if not name_el:
                    continue
                name = name_el.get_text(strip=True)
                if not name or len(name) < 3:
                    continue

                # Telefon
                phone = ""
                phone_el = (
                    card.select_one("[data-phone]") or
                    card.select_one(".mod-MiniKontakt--phone") or
                    card.select_one("[class*='phone']") or
                    card.select_one("a[href^='tel:']")
                )
                if phone_el:
                    phone = phone_el.get("data-phone") or phone_el.get_text(strip=True)

                # Website
                website = ""
                web_el = card.select_one("[data-webseitelink]")
                if web_el:
                    try:
                        b64_url = web_el.get("data-webseitelink", "")
                        if b64_url:
                            href = base64.b64decode(b64_url).decode("utf-8")
                            if href and "gelbeseiten" not in href and href.startswith("http"):
                                website = href
                    except Exception:
                        pass
                
                # Fallback für href
                if not website:
                    web_el_a = card.select_one("a.mod-AdresseKompakt--website, a[class*='website']")
                    if web_el_a:
                        href = web_el_a.get("href", "")
                        if href and "gelbeseiten" not in href and href.startswith("http"):
                            website = href

                # Adresse
                address = ""
                addr_el = card.select_one(".mod-AdresseKompakt--adresse, [class*='adresse']")
                if addr_el:
                    address = addr_el.get_text(strip=True)

                # E-Mail extrahieren oder schätzen
                email = ""
                chat_btn = card.select_one("button[data-parameters]")
                if chat_btn:
                    try:
                        params_str = chat_btn.get("data-parameters", "")
                        if params_str:
                            params = json.loads(params_str)
                            em = params.get("generic", {}).get("email", "")
                            if em:
                                email = em
                    except Exception:
                        pass

                results.append({
                    "name": name,
                    "category": category,
                    "city": city or "Deutschland",
                    "phone": phone,
                    "website": website,
                    "email": email,
                    "address": address,
                    "rating": "",
                    "source": "Gelbe Seiten",
                })
            except Exception as ex:
                logger.debug(f"[Research] Karte überspringen: {ex}")
                continue

        time.sleep(random.uniform(1.0, 2.5))
    except Exception as e:
        logger.warning(f"[Research] Gelbe Seiten Fehler: {e}")

    return results


# ──────────────────────────────────────
# BRANCHENBUCH SCRAPER (Fallback)
# ──────────────────────────────────────

def _scrape_branchenbuch(category: str, city: str = "", max_results: int = 10) -> list:
    """Scrapt branchenbuch.de als zweite Fallback-Quelle (deaktiviert)."""
    logger.warning("[Research] Branchenbuch domain unreachable, skipping.")
    return []
    results = []
    try:
        where = city.strip() if city.strip() else "deutschland"
        query = category.strip()
        url = f"https://www.branchenbuch.de/s/{query.replace(' ', '+')}/{where.replace(' ', '+')}"

        headers = random.choice(HEADERS_POOL)
        logger.info(f"[Research] Branchenbuch: {url}")
        resp = requests.get(url, headers=headers, timeout=20)

        if resp.status_code != 200:
            return results

        soup = BeautifulSoup(resp.text, "html.parser")

        # Firmen-Karten
        cards = soup.select(".company-item, .listing-item, [class*='company'], article")
        logger.info(f"[Research] Branchenbuch: {len(cards)} Karten")

        for card in cards[:max_results]:
            try:
                name_el = card.select_one("h2, h3, .company-name, [class*='name']")
                if not name_el:
                    continue
                name = name_el.get_text(strip=True)
                if not name or len(name) < 3:
                    continue

                phone = ""
                phone_el = card.select_one("a[href^='tel:'], [class*='phone']")
                if phone_el:
                    phone = phone_el.get_text(strip=True).replace("tel:", "").strip()

                website = ""
                web_el = card.select_one("a[href*='http']:not([href*='branchenbuch'])")
                if web_el:
                    website = web_el.get("href", "")

                email = ""  # We only use real emails, never guess

                results.append({
                    "name": name,
                    "category": category,
                    "city": city or "Deutschland",
                    "phone": phone,
                    "website": website,
                    "email": email,
                    "address": "",
                    "rating": "",
                    "source": "Branchenbuch",
                })
            except Exception:
                continue

        time.sleep(random.uniform(1.0, 2.0))
    except Exception as e:
        logger.warning(f"[Research] Branchenbuch Fehler: {e}")

    return results


# ──────────────────────────────────────
# ÖFFENTLICHE API-FUNKTION
# ──────────────────────────────────────

def research_sync(query: str, city: str = "", source: str = "auto",
                  max_results: int = 10) -> list:
    """
    Synchrone Recherche. Gibt Liste von Lead-Dicts zurück.
    source: 'gelbeseiten' | 'branchenbuch' | 'auto'
    city kann leer sein → sucht in ganz Deutschland
    """
    results = []

    if source in ("gelbeseiten", "auto"):
        results = _scrape_gelbeseiten(query, city, max_results)

    if len(results) < 3 and source in ("branchenbuch", "auto"):
        logger.info("[Research] Fallback: Branchenbuch")
        bb = _scrape_branchenbuch(query, city, max_results - len(results))
        results.extend(bb)

    # Deduplizierung
    seen = set()
    unique = []
    for r in results:
        key = r["name"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(r)

    logger.info(f"[Research] '{query}' (Stadt: '{city or 'Deutschland'}') → {len(unique)} Leads")
    return unique


def research_stream(query: str, city: str = "", source: str = "auto",
                    max_results: int = 10):
    """
    Generator für SSE-Streaming. Gibt Leads einzeln zurück.
    """
    city_label = city.strip() if city.strip() else "Deutschland"
    full_query = f"{query} {city}".strip() if city.strip() else query
    seen_names = set()

    yield {"type": "status", "message": f"🔍 Suche: \"{query}\" in {city_label}..."}

    # Gelbe Seiten
    if source in ("gelbeseiten", "auto"):
        yield {"type": "status", "message": "📒 Suche in Gelbe Seiten..."}
        try:
            gs_results = _scrape_gelbeseiten(query, city, max_results)
            for lead in gs_results:
                key = lead["name"].lower().strip()
                if key not in seen_names:
                    seen_names.add(key)
                    yield {"type": "lead", "lead": lead}
        except Exception as e:
            yield {"type": "warning", "message": f"Gelbe Seiten: {str(e)[:100]}"}

    # Fallback Branchenbuch
    if len(seen_names) < 3 and source in ("branchenbuch", "auto"):
        yield {"type": "status", "message": "📖 Suche auch in Branchenbuch..."}
        try:
            bb_results = _scrape_branchenbuch(query, city, max_results - len(seen_names))
            for lead in bb_results:
                key = lead["name"].lower().strip()
                if key not in seen_names:
                    seen_names.add(key)
                    yield {"type": "lead", "lead": lead}
        except Exception as e:
            yield {"type": "warning", "message": f"Branchenbuch: {str(e)[:100]}"}

    count = len(seen_names)
    if count == 0:
        yield {"type": "warning", "message": "⚠️ Keine Ergebnisse gefunden – versuche andere Suchbegriffe"}
    
    yield {
        "type": "complete",
        "message": f"✅ Recherche abgeschlossen – {count} Betriebe gefunden",
        "count": count,
    }



