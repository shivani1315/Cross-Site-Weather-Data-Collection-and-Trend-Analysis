import requests
import pandas as pd

# ---- CONFIGURATION ----
api_key = "XYHMZG8QTX97QNQ7Q6SV9WCJU"  # get free key from https://www.visualcrossing.com
city_name = "Haldwani, India"
target_date = "2025-08-01"  # YYYY-MM-DD

# ---- STEP 1: Build API URL ----
url = (
    f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/"
    f"{city_name}/{target_date}/{target_date}"
    f"?unitGroup=metric&include=hours&key={api_key}&contentType=json"
)

# Send Request
response = requests.get(url)
response.raise_for_status()
data = response.json()

#Parse Hourly Data
records = []
for hour in data["days"][0]["hours"]:
    records.append({
        "date": data["days"][0]["datetime"],
        "time": hour["datetime"],
        "temperature_C": hour["temp"],
        "humidity_%": hour.get("humidity"),
        "windspeed_kmh": hour.get("windspeed"),
        "conditions": hour.get("conditions")
    })

#Save to CSV
df = pd.DataFrame(records)
csv_filename = f"visualcrossing_haldwani_{target_date}.csv"
df.to_csv(csv_filename, index=False)
print(f"Data saved to {csv_filename}")
print(df.head())
