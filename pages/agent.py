import os
import requests
import streamlit as st

from agno.agent import Agent
from agno.models.openrouter import OpenRouter
from agno.media import Image
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.yfinance import YFinanceTools
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.hackernews import HackerNewsTools
from agno.tools.wikipedia import WikipediaTools


# 🛡️ Setup API key (either from environment or hardcoded here)
API_KEY = os.getenv("OPENROUTER_API_KEY")
api_key = os.getenv("OPENROUTER_API_KEY", "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")

# 🌍 ECCU context and dynamic instruction template
ECCU_COUNTRIES = [
    "Antigua and Barbuda",
    "Dominica",
    "Grenada",
    "Saint Kitts and Nevis",
    "Saint Lucia",
    "Saint Vincent and the Grenadines",
    "Anguilla",
    "Montserrat",
]

ECCU_COUNTRY_CODES = {
    "AG": "Antigua and Barbuda",
    "DM": "Dominica",
    "GD": "Grenada",
    "KN": "Saint Kitts and Nevis",
    "LC": "Saint Lucia",
    "VC": "Saint Vincent and the Grenadines",
    "AI": "Anguilla",
    "MS": "Montserrat",
}

COUNTRY_TONE = {
    "Antigua and Barbuda": {
        "greeting": "Wadadli strong!",
        "example": "Let’s budget your Wadadli Day income after the big fete.",
        "slang": ["Wadadli Day", "carnival money", "boat ride lime", "fete vibes"],
    },
    "Dominica": {
        "greeting": "Wha’ vibes!",
        "example": "What would you do with $50 from selling dasheen at Roseau Market?",
        "slang": ["dasheen", "market money", "Creole fest", "lime spot"],
    },
    "Grenada": {
        "greeting": "Spice up yuh day!",
        "example": "How yuh stretching that Spicemas earnings this month?",
        "slang": ["Spicemas", "oil down", "market day", "shortknee"],
    },
    "Saint Kitts and Nevis": {
        "greeting": "Big up SKN!",
        "example": "What’s your plan for the Culturama profits?",
        "slang": ["Culturama", "Sugar Mas", "federation vibes", "beach lime"],
    },
    "Saint Lucia": {
        "greeting": "Lucian pride!",
        "example": "Let’s plan how to save some Jounen Kwéyòl earnings.",
        "slang": ["Jounen Kwéyòl", "Lucian Lime", "Gros Islet Friday", "carnival flow"],
    },
    "Saint Vincent and the Grenadines": {
        "greeting": "Vincy to de bone!",
        "example": "How yuh putting aside some Vincymas money?",
        "slang": ["Vincymas", "Vincy rum shop", "breadfruit oil down", "whine up"],
    },
    "Anguilla": {
        "greeting": "Straight outta AXA!",
        "example": "Budget that Anguilla Summer Festival hustle money.",
        "slang": ["Summer Festival", "boat race winnings", "island vibes", "beach bash"],
    },
    "Montserrat": {
        "greeting": "Emerald Isle strong!",
        "example": "What’s the plan for your St. Patrick’s Festival profits?",
        "slang": ["St. Patrick’s Festival", "volcano stories", "Irish vibes", "island lime"],
    },
}

INSTRUCTION_TEMPLATE = """
You are a helpful, youth-friendly Financial AI Agent focused on the Eastern Caribbean Currency Union (ECCU) but able to serve anyone globally.

Core capabilities (MUST use tools when applicable):
- Detect and warn about common scams
- Host interactive financial literacy quizzes (one question at a time)
- Recommend personalized side hustles
- Perform currency conversion using tools
- Create custom budget plans using tool-based inputs

Important rules:
- Always use available tools for the above tasks; do not fabricate financial facts.
- Be concise, positive, and practical. Show small, actionable steps.
- If the user is in an ECCU country, adapt tone, slang, and examples accordingly.
- If the user is not in an ECCU country, respond with a friendly, generic global tone.

Location context (from app):
- country: {country}
- region: {region}
- city: {city}
- latitude: {latitude}
- longitude: {longitude}
- is_eccu: {is_eccu}

Persona guidelines:
{persona_guidelines}

Examples to mirror when applicable:
- Dominica: "What would you do with $50 from selling dasheen?"
- Antigua and Barbuda: "Let’s budget your Wadadli Day income."

Quiz style:
- Keep it fun; give feedback after each answer; track score playfully.
- Offer next-step actions after the quiz (budgeting, side hustles, scam tips).
"""


def detect_user_location() -> dict:
    """Detect user location robustly via multiple providers and cache it."""
    if "user_location" in st.session_state:
        return st.session_state.user_location

    location = {
        "country": None,
        "region": None,
        "city": None,
        "latitude": None,
        "longitude": None,
        "is_eccu": False,
    }

    def _normalize_country(country_name: str | None, country_code: str | None) -> str | None:
        if country_name:
            return country_name
        if country_code and country_code in ECCU_COUNTRY_CODES:
            return ECCU_COUNTRY_CODES[country_code]
        return country_name or country_code

    def _finalize(loc: dict) -> dict:
        country_name = loc.get("country")
        if isinstance(country_name, str) and len(country_name) == 2 and country_name.isalpha():
            mapped = ECCU_COUNTRY_CODES.get(country_name.upper())
            if mapped:
                loc["country"] = mapped
        if loc.get("country") in ECCU_COUNTRIES:
            loc["is_eccu"] = True
        st.session_state.user_location = loc
        if os.getenv("DEBUG_LOCATION"):
            print(loc)
        return loc

    headers = {"User-Agent": "Mozilla/5.0 (Streamlit App)"}
    providers = ["ipapi", "ipwhois", "ipapi_alt", "ipinfo"]

    for provider in providers:
        try:
            if provider == "ipapi":
                resp = requests.get("https://ipapi.co/json/", timeout=8, headers=headers)
                if resp.ok:
                    data = resp.json()
                    country_name = _normalize_country(data.get("country_name"), data.get("country"))
                    if country_name or data.get("city"):
                        location["country"] = country_name
                        location["region"] = data.get("region")
                        location["city"] = data.get("city")
                        location["latitude"] = data.get("latitude")
                        location["longitude"] = data.get("longitude")
                        return _finalize(location)

            if provider == "ipwhois":
                resp = requests.get("https://ipwho.is/", timeout=8, headers=headers)
                if resp.ok:
                    data = resp.json()
                    if data.get("success"):
                        location["country"] = _normalize_country(data.get("country"), data.get("country_code"))
                        location["region"] = data.get("region")
                        location["city"] = data.get("city")
                        location["latitude"] = data.get("latitude")
                        location["longitude"] = data.get("longitude")
                        if any([location["country"], location["city"], location["region"]]):
                            return _finalize(location)

            if provider == "ipapi_alt":
                resp = requests.get("https://ip-api.com/json/", timeout=8, headers=headers)
                if resp.ok:
                    data = resp.json()
                    if data.get("status") == "success":
                        location["country"] = _normalize_country(data.get("country"), data.get("countryCode"))
                        location["region"] = data.get("regionName")
                        location["city"] = data.get("city")
                        location["latitude"] = data.get("lat")
                        location["longitude"] = data.get("lon")
                        return _finalize(location)

            if provider == "ipinfo":
                resp = requests.get("https://ipinfo.io/json", timeout=8, headers=headers)
                if resp.ok:
                    data = resp.json()
                    loc_str = data.get("loc")
                    if isinstance(loc_str, str) and "," in loc_str:
                        lat_str, lon_str = loc_str.split(",", 1)
                        try:
                            location["latitude"] = float(lat_str)
                            location["longitude"] = float(lon_str)
                        except Exception:
                            pass
                    location["country"] = _normalize_country(None, data.get("country"))
                    location["region"] = data.get("region")
                    location["city"] = data.get("city")
                    if any([location["country"], location["city"], location["region"]]):
                        return _finalize(location)
                    
        except Exception:
            print(f"Location provider {provider} failed or returned no data.")
            continue
    print(f"Location provider {provider} failed or returned no data.")
    return _finalize(location)


def build_persona_guidelines(location: dict) -> str:
    country = location.get("country") or ""
    if location.get("is_eccu"):
        if country in COUNTRY_TONE:
            tone = COUNTRY_TONE[country]
            return (
                f"- Start with a localized greeting (e.g., '{tone['greeting']}').\n"
                f"- Use culturally relevant examples (e.g., {tone['example']}).\n"
                f"- Light slang allowed: {', '.join(tone['slang'])}. Keep it respectful and clear.\n"
                f"- Use EC$ (XCD) where currency appears; convert with tools if needed."
            )
        else:
            return (
                "- Use a warm ECCU tone with light island slang where natural.\n"
                "- Use examples around carnival gigs, market day sales, tourism tips.\n"
                "- Prefer EC$ (XCD) and show small-step savings and investing."
            )
    return (
        "- Use a neutral global tone.\n"
        "- Avoid local slang.\n"
        "- Use the user's local currency if known, otherwise USD; convert with tools."
    )


def build_instructions(location: dict) -> str:
    persona = build_persona_guidelines(location)
    return INSTRUCTION_TEMPLATE.format(
        country=location.get("country"),
        region=location.get("region"),
        city=location.get("city"),
        latitude=location.get("latitude"),
        longitude=location.get("longitude"),
        is_eccu=location.get("is_eccu"),
        persona_guidelines=persona,
    )


def agent(message, image=None, location=None):
    instructions = build_instructions(location or {})
    _agent = Agent(
        name="💼 Financial AI Agent",
        model=OpenRouter(id="google/gemini-2.5-flash", api_key=api_key, max_tokens=8000),
        tools=[
            DuckDuckGoTools(),
            YFinanceTools(historical_prices=True),
            GoogleSearchTools(),
            HackerNewsTools(),
            WikipediaTools(),
        ],
        tool_choice="auto",
        instructions=instructions,
        add_history_to_messages=True,
    )

    if image:
        image = [Image(filepath=image)]

    return _agent.run(message=message, images=image, stream=True)
