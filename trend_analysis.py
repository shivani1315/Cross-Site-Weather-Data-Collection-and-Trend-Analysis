import pandas as pd
import matplotlib.pyplot as plt

# ==== File paths ====
visualcrossing_file = "visualcrossing_haldwani_2025-08-01.csv"
meteostat_file = "haldwani_weather_meteostat.csv"
wunderground_file = "wunderground_hourly_filled_VIPT_20250801.csv"

# ==== Visual Crossing ====
df_vc = pd.read_csv(visualcrossing_file)
df_vc["datetime"] = pd.to_datetime(df_vc["date"] + " " + df_vc["time"])
df_vc = df_vc.rename(columns={
    "temperature_C": "Temperature (°C)",
    "humidity_%": "Humidity (%)",
    "windspeed_kmh": "Wind Speed (km/h)"
})
df_vc = df_vc[["datetime", "Temperature (°C)", "Humidity (%)", "Wind Speed (km/h)"]]
df_vc["Source"] = "Visual Crossing"

# ==== Meteostat ====
df_ms = pd.read_csv(meteostat_file)
df_ms["datetime"] = pd.to_datetime(df_ms["time"])
df_ms = df_ms.rename(columns={
    "Temperature (°C)": "Temperature (°C)",
    "Humidity (%)": "Humidity (%)",
    "Wind Speed (km/h)": "Wind Speed (km/h)"
})
df_ms = df_ms[["datetime", "Temperature (°C)", "Humidity (%)", "Wind Speed (km/h)"]]
df_ms["Source"] = "Meteostat"

# ==== Wunderground ====
df_wu = pd.read_csv(wunderground_file)
df_wu["datetime"] = pd.to_datetime(df_wu["datetime_local"])
df_wu = df_wu.rename(columns={
    "temperature_c": "Temperature (°C)",
    "humidity_pct": "Humidity (%)",
    "wind_speed_kmh": "Wind Speed (km/h)"
})
df_wu = df_wu[["datetime", "Temperature (°C)", "Humidity (%)", "Wind Speed (km/h)"]]
df_wu["Source"] = "Wunderground"

# ==== Combine all ====
df_all = pd.concat([df_vc, df_ms, df_wu], ignore_index=True)

# ==== Plot ====
fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

for ax, param in zip(axes, ["Temperature (°C)", "Humidity (%)", "Wind Speed (km/h)"]):
    for source in df_all["Source"].unique():
        subset = df_all[df_all["Source"] == source]
        ax.plot(subset["datetime"], subset[param], marker="o", label=source)
    ax.set_ylabel(param)
    ax.legend()
    ax.grid(True)

axes[-1].set_xlabel("Datetime")
plt.tight_layout()
plt.show()
