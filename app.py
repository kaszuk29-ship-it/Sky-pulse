import os
import json
import requests
import streamlit as st
from huggingface_hub import InferenceClient

st.set_page_config(
    page_title="SkyPulse AI",
    page_icon="🌈",
    layout="centered"
)

st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg, #dff6ff, #f3e8ff, #fff4d6);
}

/* Main title */
.main-title {
    text-align: center;
    font-size: 48px;
    font-weight: 800;
    background: linear-gradient(90deg, #0077ff, #8e44ad, #ff6b6b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 5px;
}

.subtitle {
    text-align: center;
    color: #555;
    font-size: 18px;
    margin-bottom: 25px;
}

/* Weather card */
.weather-card {
    padding: 28px;
    border-radius: 25px;
    text-align: center;
    color: white;
    background: linear-gradient(135deg, #36d1dc, #5b86e5);
    box-shadow: 0px 10px 25px rgba(0,0,0,0.15);
    margin-top: 20px;
}

.city-name {
    font-size: 25px;
    font-weight: 700;
}

.temperature {
    font-size: 58px;
    font-weight: 800;
    margin: 10px;
}

/* Info cards */
.info-card {
    background: white;
    padding: 18px;
    border-radius: 18px;
    text-align: center;
    box-shadow: 0px 5px 15px rgba(0,0,0,0.08);
}

.info-title {
    font-size: 15px;
    color: #777;
}

.info-value {
    font-size: 23px;
    font-weight: 700;
}

/* AI report */
.ai-card {
    background: linear-gradient(135deg, #fff, #f5efff);
    padding: 20px;
    border-radius: 20px;
    border-left: 6px solid #8e44ad;
    box-shadow: 0px 5px 15px rgba(0,0,0,0.08);
}

/* Footer */
.footer {
    text-align: center;
    color: #777;
    margin-top: 35px;
    font-size: 14px;
}

</style>
""", unsafe_allow_html=True)
st.markdown(
    '<div class="main-title">🌈 SkyPulse AI</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">☁️ Your friendly AI weather assistant</div>',
    unsafe_allow_html=True
)

TOKEN = os.getenv("Access_Token")

if not TOKEN:
    st.error("⚠️ Hugging Face token is missing.")
    st.info(
        "Set your token in the terminal using: "
        "$env:Access_Token='your_token_here'"
    )
    st.stop()

client = InferenceClient(api_key=TOKEN)

MODEL = "openai/gpt-oss-120b:fastest"


def sky_pulse(city):
    location_response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={
            "name": city,
            "count": 1,
            "format": "json"
        },
        timeout=10
    )

    location = location_response.json()

    if "results" not in location:
        return {"error": "City not found. Please check the spelling."}

    place = location["results"][0]
    weather_response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m",
            "timezone": "auto"
        },
        timeout=10
    )

    weather = weather_response.json()["current"]

    return {
        "city": place["name"],
        "country": place.get("country", ""),
        "temperature": weather["temperature_2m"],
        "humidity": weather["relative_humidity_2m"],
        "wind": weather["wind_speed_10m"]
    }

weather_tool = [
    {
        "type": "function",
        "function": {
            "name": "sky_pulse",
            "description": "Get current weather information for a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Name of the city"
                    }
                },
                "required": ["city"]
            }
        }
    }
]
st.markdown("### 🏙️ Where do you want to check the weather?")

city = st.text_input(
    "Enter city name",
    placeholder="Example: Chennai, Madurai, Coimbatore...",
    label_visibility="collapsed"
)

st.write("✨ Quick search")

col1, col2, col3 = st.columns(3)

if col1.button("🌴 Chennai", use_container_width=True):
    city = "Chennai"

if col2.button("🏛️ Madurai", use_container_width=True):
    city = "Madurai"

if col3.button("🌊 Coimbatore", use_container_width=True):
    city = "Coimbatore"

if st.button(
    "🌤️  Check My Weather",
    use_container_width=True
):

    if not city.strip():

        st.warning("👋 Please enter a city first!")

    else:

        messages = [
            {
                "role": "user",
                "content": f"What is the current weather in {city}?"
            }
        ]

        with st.spinner("🔍 SkyPulse is checking the sky..."):

            try:

                # Ask AI to use weather tool
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    tools=weather_tool,
                    tool_choice="auto"
                )

                msg = response.choices[0].message
                if msg.tool_calls:

                    call = msg.tool_calls[0]

                    args = json.loads(
                        call.function.arguments
                    )

                    weather = sky_pulse(args["city"])

                    if "error" in weather:
                        st.error(weather["error"])
                        st.stop()
                    messages.append({
                        "role": "assistant",
                        "content": msg.content,
                        "tool_calls": [
                            {
                                "id": call.id,
                                "type": "function",
                                "function": {
                                    "name": call.function.name,
                                    "arguments": call.function.arguments
                                }
                            }
                        ]
                    })

                    # Add weather result
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(weather)
                    })
                    final = client.chat.completions.create(
                        model=MODEL,
                        messages=messages
                    )
                    st.markdown(f"""
                    <div class="weather-card">

                        <div class="city-name">
                            📍 {weather["city"]}, {weather["country"]}
                        </div>

                        <div class="temperature">
                            🌡️ {weather["temperature"]}°C
                        </div>

                        <div>
                            Current Temperature
                        </div>

                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown("### 📊 Weather Details")

                    c1, c2, c3 = st.columns(3)

                    with c1:
                        st.markdown(f"""
                        <div class="info-card">
                            <div class="info-title">🌡️ Temperature</div>
                            <div class="info-value">
                                {weather["temperature"]}°C
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    with c2:
                        st.markdown(f"""
                        <div class="info-card">
                            <div class="info-title">💧 Humidity</div>
                            <div class="info-value">
                                {weather["humidity"]}%
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    with c3:
                        st.markdown(f"""
                        <div class="info-card">
                            <div class="info-title">💨 Wind</div>
                            <div class="info-value">
                                {weather["wind"]} km/h
                            </div>
                        </div>
                        """, unsafe_allow_html=True)


                

                    st.markdown("### 🤖 SkyPulse AI Says")

                    st.markdown(
                        f"""
                        <div class="ai-card">
                            {final.choices[0].message.content}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )


                else:

                    st.info(msg.content)

            except Exception as e:

                st.error(
                    f"⚠️ Something went wrong:\n\n{e}"
                )

st.markdown("""
<div class="footer">
    🌈 SkyPulse AI • Powered by AI + Open-Meteo
    <br>
    ☁️ Simple • Smart • Friendly
</div>
""", unsafe_allow_html=True)