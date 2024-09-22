from quickchart import QuickChart
import numpy as np
import requests
from slack_sdk import WebClient
import os
from dotenv import load_dotenv
load_dotenv()
slack_token = os.getenv("SLACK_BOT_TOKEN")
weather_api_key = os.getenv("WEATHER_API_KEY")


def get_weather(api_key, city="Evanston", country="US"):
    # OpenWeatherMap API endpoint for hourly forecast
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat=42.045597&&lon=-87.688568&appid={api_key}"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"Error: {response.status_code}")
        return None


def extract_rain_chance(data):
    rain_probabilities = []
    forecast_list = data.get("list", [])

    # Extract rain probability for the next 12 hours (first 4 entries as each entry is 3-hour interval)
    for i in range(4):
        forecast = forecast_list[i]
        rain = forecast.get("rain", {}).get("3h", 0)
        rain_probabilities.append(rain)

    return rain_probabilities


weather_data = get_weather(weather_api_key)

if weather_data:
    rain_chances = extract_rain_chance(weather_data)
    print("Chance of rain in the next 12 hours (in mm):", rain_chances)

might_rain = False
for chance in rain_chances:
    if chance:
        might_rain = True

if might_rain:
    def get_hour(i):
        if i > 12:
            i -= 12
        return f"{i}:00"

    labels = [f"{get_hour(i)}-{get_hour(i+3)}" for i in range(9, 21, 3)]
    x = np.array(labels)
    y = np.array(rain_chances)

    # plt.bar(x, y)
    # plt.show()

    qc = QuickChart()
    qc.width = 500
    qc.height = 300

    # Config can be set as a string or as a nested dict
    qc.config = {
        "type": 'bar',
        "data": {
            "labels": labels,
            "datasets": [{
                "label": 'Chances of Weather',
                "data": rain_chances
            }]
        }
    }

    # You can get the chart URL...
    print(qc.get_url())

    client = WebClient(token=slack_token)

    client.chat_postMessage(
        channel="weather-updates",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Here is the weather forcast for the next 12 hours."
                }
            },
            {
                "type": "image",
                "image_url": qc.get_url(),
                "alt_text": "Chances of Rain"
            }
        ]
    )
