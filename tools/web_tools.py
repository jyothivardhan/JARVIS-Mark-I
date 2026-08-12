"""
web_tools.py
Web-based tools — no API keys required.

  search_web(query)   DuckDuckGo Instant Answer API
  get_weather(city)   wttr.in JSON API

Uses only the Python standard library (urllib).
"""
import json
import urllib.error
import urllib.parse
import urllib.request

from core.logger import get_logger

logger = get_logger(__name__)

_TIMEOUT = 8  # seconds per HTTP request


class WebTools:

    # ── Web search ────────────────────────────────────────────────────────────
    def search_web(self, query: str, max_bullets: int = 3) -> str:
        """
        Query DuckDuckGo Instant Answer API and return a concise summary.
        Falls back to listing related-topic snippets if no abstract is found.
        """
        try:
            encoded = urllib.parse.quote_plus(query)
            url     = (
                f"https://api.duckduckgo.com/"
                f"?q={encoded}&format=json&no_html=1&skip_disambig=1"
            )
            with urllib.request.urlopen(url, timeout=_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            # Best case: Instant Answer abstract
            abstract = data.get("AbstractText", "").strip()
            if abstract:
                return abstract

            # Second best: related topics
            topics  = data.get("RelatedTopics", [])
            bullets = []
            for t in topics:
                if isinstance(t, dict) and t.get("Text"):
                    bullets.append(f"• {t['Text']}")
                    if len(bullets) >= max_bullets:
                        break

            if bullets:
                return f"Here's what I found about '{query}':\n" + "\n".join(bullets)

            return (
                f"No instant answer found for '{query}'. "
                "Try rephrasing or ask something more specific."
            )

        except urllib.error.URLError as e:
            logger.error("Web search network error: %s", e)
            return f"Web search failed — network error: {e.reason}"
        except Exception as e:
            logger.error("Web search error: %s", e)
            return f"Web search failed: {e}"

    # ── Weather ───────────────────────────────────────────────────────────────
    def get_weather(self, city: str) -> str:
        """
        Fetch current weather for `city` from wttr.in (JSON format 1).
        """
        try:
            encoded = urllib.parse.quote_plus(city.strip())
            url     = f"https://wttr.in/{encoded}?format=j1"

            with urllib.request.urlopen(url, timeout=_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            current  = data["current_condition"][0]
            temp_c   = current["temp_C"]
            feels_c  = current["FeelsLikeC"]
            desc     = current["weatherDesc"][0]["value"]
            humidity = current["humidity"]
            wind_kmh = current["windspeedKmph"]

            return (
                f"Weather in {city.title()}: {desc}, {temp_c}°C "
                f"(feels like {feels_c}°C). "
                f"Humidity {humidity}%, wind {wind_kmh} km/h."
            )

        except urllib.error.URLError as e:
            logger.error("Weather network error: %s", e)
            return f"Could not fetch weather — network error: {e.reason}"
        except (KeyError, IndexError) as e:
            logger.error("Weather parse error: %s", e)
            return f"Could not parse weather data for '{city}'."
        except Exception as e:
            logger.error("Weather error: %s", e)
            return f"Weather lookup failed: {e}"
