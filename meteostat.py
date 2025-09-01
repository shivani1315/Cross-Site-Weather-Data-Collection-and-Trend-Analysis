pip install meteostat pandas matplotlib seaborn
from meteostat import Point, Hourly
from datetime import datetime
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ========== Location: Haldwani (Updated Coordinates) ==========
haldwani = Point(29.16762015565497, 79.52007657468288, 424)  # 424m elevation (approx)

# ========== Time Range ==========
start = datetime(2025, 8, 1)
end = datetime(2025, 8, 1, 23, 59)

# ========== Fetch Data ==========
data = Hourly(haldwani, start, end)
df = data.fetch()[['temp', 'rhum', 'wspd']]
df.columns = ['Temperature (°C)', 'Humidity (%)', 'Wind Speed (km/h)']
df.reset_index(inplace=True)

# ========== Save to CSV ==========
csv_path = "haldwani_weather_meteostat.csv"
df.to_csv(csv_path, index=False)
print(f" Weather data saved to: {csv_path}")


#Visualization

from meteostat import Point, Hourly
from datetime import datetime
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# ========== Location: Haldwani ==========
haldwani = Point(29.16762015565497, 79.52007657468288, 424)

# ========== Time Range ==========
start = datetime(2025, 8, 1)
end = datetime(2025, 8, 1, 23, 59)

# ========== Fetch Data ==========
data = Hourly(haldwani, start, end)
df = data.fetch()[['temp', 'rhum', 'wspd']]
df.columns = ['Temperature (°C)', 'Humidity (%)', 'Wind Speed (km/h)']
df.reset_index(inplace=True)

# ========== Prepare Data for Heatmap ==========
df['Hour'] = df['time'].dt.hour
heatmap_data = df[['Hour', 'Temperature (°C)', 'Humidity (%)', 'Wind Speed (km/h)']].set_index('Hour').T
heatmap_data = heatmap_data.astype(float)

# ========== Plot and Save Heatmap ==========
plt.figure(figsize=(14, 4))
sns.heatmap(heatmap_data, annot=True, fmt=".1f", cmap="viridis", cbar_kws={'label': 'Value'})

plt.title("Weather Parameters Heatmap - Haldwani (1 Aug 2025)")

plt.xlabel("Hour")
plt.ylabel("Parameter")
plt.tight_layout()

# Save as PNG
plt.savefig("haldwani_heatmap.png", dpi=300, bbox_inches='tight')
plt.show()
