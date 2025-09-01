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

# Visualization
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

# ===== Example API Data =====
# Yahan apna actual API response ka data daal do
hours = data["days"][0]["hours"]

# Create DataFrame
df = pd.DataFrame(hours)

# ---- Date Handling ----
# Agar datetime me sirf time ho, to date attach karo
date_str = data["days"][0]["datetime"]  # e.g. "2025-08-01"
if len(df["datetime"].iloc[0]) <= 8:  # sirf time hai
    df["datetime"] = pd.to_datetime(date_str + " " + df["datetime"])
else:  # already date + time hai
    df["datetime"] = pd.to_datetime(df["datetime"])

# Sort by datetime
df = df.sort_values(by="datetime")

# ==== Parameters to Plot ====
params = {
    "temp": "Temperature (°C)",
    "humidity": "Humidity (%)",
    "windspeed": "Wind Speed (km/h)",
    "precip": "Precipitation (mm)",
    "cloudcover": "Cloud Cover (%)"
}

# ==== Plot Each Parameter ====
for col, label in params.items():
    plt.figure(figsize=(8, 4))
    plt.plot(df["datetime"], df[col], marker="o")
    plt.title(f"{label} vs Time")
    plt.xlabel("Time")
    plt.ylabel(label)
    plt.grid(True)

    # Format X-axis for date + time
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%m-%d %H:%M"))
    plt.xticks(rotation=45)

    plt.tight_layout()
    plt.show()

