# map code
# call the render_eccu_map to render the map
import os
import pydeck as pdk
import streamlit as st

ECCU_PINS = [
    {"name": "Antigua and Barbuda", "lat": 17.0608, "lon": -61.7964, "note": "Wadadli vibes. Carnival budgets, gig income."},
    {"name": "Dominica", "lat": 15.4150, "lon": -61.3710, "note": "Dasheen money, village market savings."},
    {"name": "Grenada", "lat": 12.1165, "lon": -61.6790, "note": "Spice Mas, cocoa/ nutmeg side hustles."},
    {"name": "Saint Kitts and Nevis", "lat": 17.3578, "lon": -62.7830, "note": "Music gigs, tourism side jobs."},
    {"name": "Saint Lucia", "lat": 13.9094, "lon": -60.9789, "note": "Gros Islet nights, craft sales savings."},
    {"name": "Saint Vincent and the Grenadines", "lat": 13.2500, "lon": -61.2000, "note": "Fisherfolk budgets, market day profits."},
    {"name": "Anguilla", "lat": 18.2206, "lon": -63.0686, "note": "Tourism tips, seasonal saving goals."},
    {"name": "Montserrat", "lat": 16.7425, "lon": -62.1874, "note": "Small island gigs, community investing."},
]

def render_eccu_map(user_country: str | None = None, center: tuple[float, float] | None = None):
    mapbox_token = os.getenv("MAPBOX_API_KEY") or os.getenv("MAPBOX_TOKEN")
    if mapbox_token:
        pdk.settings.mapbox_api_key = mapbox_token

    pins = []
    for pin in ECCU_PINS:
        is_user_pin = user_country and (pin["name"].lower() == user_country.lower())
        pins.append({
            **pin,
            "color": [214, 0, 118, 220] if not is_user_pin else [0, 168, 84, 240],
            "radius": 60000 if is_user_pin else 40000,
        })

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=pins,
        get_position="[lon, lat]",
        get_fill_color="color",
        get_radius="radius",
        pickable=True,
    )

    if center is None:
        center = (15.0, -61.2)

    view_state = pdk.ViewState(
        latitude=center[0],
        longitude=center[1],
        zoom=5,
        pitch=30,
    )

    deck = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/light-v10" if mapbox_token else None,
        tooltip={
            "html": "<b>{name}</b><br/>{note}",
            "style": {"backgroundColor": "#111", "color": "#fff"},
        },
    )

    st.pydeck_chart(deck)
