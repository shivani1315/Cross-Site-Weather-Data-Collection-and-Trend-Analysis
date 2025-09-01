# Filename: wunderground_hourly_pantnagar.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import re
import os
import time

# ============ USER INPUT ============
city_code = "pantnagar"
icao_code = "VIPT"
date_input = "2000-08-01"  # YYYY-MM-DD
url = f"https://www.wunderground.com/history/daily/in/{city_code}/{icao_code}/date/{date_input}"

# ============ SELENIUM SETUP ============
options = Options()
options.add_argument('--headless=new')  # more stable headless
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--window-size=1400,1000')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36" # Changed user agent
)
options.binary_location = "/opt/chrome/chrome"
chromedriver_path = "/usr/bin/chromedriver"

def debug_dump(driver, tag=""):
    os.makedirs("debug", exist_ok=True)
    png = f"debug/wu_{icao_code}_{date_input}_{tag}.png"
    html = f"debug/wu_{icao_code}_{date_input}_{tag}.html"
    try: driver.save_screenshot(png)
    except: pass
    try:
        with open(html, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
    except: pass
    print(f" Debug saved: {png} , {html}")

try:
    driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)
except Exception as e:
    print(" WebDriver error:", e)
    raise SystemExit(1)

wait = WebDriverWait(driver, 20) # Reduced wait time

print(" Loading page:", url)
driver.get(url)

# --- Accept cookie/consent if present ---
try:
    consent = WebDriverWait(driver, 6).until(
        EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
    )
    consent.click()
    time.sleep(0.5)
    print(" Accepted cookies.")
except TimeoutException:
    pass
except Exception:
    pass

# --- Locate a table and ensure rows exist ---
table = None
for sel in [
    'table[aria-label*="Weather history"]',
    'table[aria-label*="Daily Weather History"]',
    'table'
]:
    try:
        table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
        break
    except TimeoutException:
        continue

if not table:
    debug_dump(driver, "no_table")
    print(" No table found.")
    driver.quit()
    raise SystemExit(1)

# Scroll to trigger lazy rendering
driver.execute_script("arguments[0].scrollIntoView({block:'center'});", table)
time.sleep(1.0)

# Wait for data rows
try:
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tbody tr")))
except TimeoutException:
    debug_dump(driver, "no_rows")
    print(" No rows rendered.")
    driver.quit()
    raise SystemExit(1)

# Ensure some cell yields text/attributes
def any_cell_has_value(drv):
    """Check if any cell in the first 100 has non-empty text or relevant attributes."""
    cells = drv.find_elements(By.CSS_SELECTOR, "tbody tr td")
    for td in cells[:100]: # Check up to the first 100 cells
        if (td.text or "").strip():
            return True
        for attr in ("aria-label", "data-label", "title", "data-value"):
            v = td.get_attribute(attr)
            if v and v.strip():
                return True
    return False

try:
    wait.until(any_cell_has_value)
    print(" Cells found with content.")
except TimeoutException:
    print(" Cells look empty or content not immediately visible; attempting attribute-based extraction anyway.")


# ----------- SCRAPE DATA (only Time, Temp, Humidity, Wind Speed) -----------
def td_value(td):
    """Return text from <td> via visible text, attributes, or descendant attributes."""
    txt = (td.text or "").strip()
    if txt:
        return txt
    for attr in ("aria-label", "data-label", "title", "data-value"):
        v = td.get_attribute(attr)
        if v and v.strip():
            return v.strip()
    # Fallback to JavaScript for hidden text content if attributes aren't present
    val = driver.execute_script("""
        const el = arguments[0];
        let c = el.querySelector('[aria-label],[data-label],[title]');
        if (c) return (c.getAttribute('aria-label')||c.getAttribute('data-label')||c.getAttribute('title')||'').trim();
        return (el.textContent || '').trim();
    """, td)
    return val.strip() if isinstance(val, str) else ""

rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
data = []
for row in rows:
    try:
        cols = row.find_elements(By.TAG_NAME, "td")
        # Typical order: 0 Time, 1 Temp, 2 Dew Point, 3 Humidity, 4 Wind, 5 Wind Speed, 6 Pressure
        if len(cols) < 7:
            continue

        time_str  = td_value(cols[0])
        temp      = td_value(cols[1])
        humidity  = td_value(cols[3])
        wind_spd  = td_value(cols[5])

        if not any([time_str, temp, humidity, wind_spd]):
            continue

        data.append({
            "Time": time_str,
            "Temperature": temp,
            "Humidity": humidity,
            "Wind Speed": wind_spd,
        })
    except Exception as e:
        print(" Row parse error:", e)

if not data:
    debug_dump(driver, "no_values_extracted")
    print(" No data found (cells likely hidden to automation).")
    print(" Try once without headless OR switch to undetected-chromedriver.")
    driver.quit()
    raise SystemExit(0)

# ----------- SAVE RAW CSV -----------
df = pd.DataFrame(data)
raw_filename = f"wunderground_data_{icao_code}_{date_input.replace('-', '')}.csv"
df.to_csv(raw_filename, index=False)
print(f"\n Raw data saved to: {raw_filename}")
print(df.head())

# ============ BUILD TRUE HOURLY DATA (regular 00–23, no '+05:30') ============
def parse_number(x):
    if x is None:
        return np.nan
    t = str(x).replace(",", "").strip().replace("—", "").replace("\u2014", "")
    m = re.search(r"[-+]?\d+(\.\d+)?", t)
    return float(m.group(0)) if m else np.nan

def parse_time_to_dt(t_str, base_date_str):
    """Parse time strings and return tz-aware datetime in Asia/Kolkata."""
    t = str(t_str).strip()
    for fmt in ("%I:%M %p", "%I %p", "%H:%M", "%H"):
        try:
            tt = datetime.strptime(t, fmt).time()
            dt = datetime.combine(datetime.strptime(base_date_str, "%Y-%m-%d").date(), tt)
            return dt.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
        except Exception:
            pass
    m = re.search(r"\b(\d{1,2})(?:\s?[:.]?\s?(\d{2}))?\s*(AM|PM)?\b", t, flags=re.I) # Added optional space/dot and made minute group optional
    if m:
        hh = int(m.group(1))
        mm = int(m.group(2)) if m.group(2) else 0
        am_pm = (m.group(3) or "").upper()
        if am_pm == "PM" and hh < 12:
            hh += 12
        elif am_pm == "AM" and hh == 12:
            hh = 0
        dt = datetime.combine(datetime.strptime(base_date_str, "%Y-%m-%d").date(), dtime(hh, mm))
        return dt.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
    return None

# Numeric columns
# Numeric columns
df["temperature_f"] = df["Temperature"].apply(parse_number)

# Convert Fahrenheit to Celsius
df["temperature_c"] = df["temperature_f"].apply(
    lambda f: (f - 32) * 5/9 if pd.notnull(f) else np.nan
)

df["humidity_pct"]    = df["Humidity"].apply(parse_number)
df["wind_speed_kmh"]  = df["Wind Speed"].apply(parse_number)






# IST timestamps (tz-aware)
df["dt_local"] = df["Time"].apply(lambda s: parse_time_to_dt(s, date_input))
dfh = df.dropna(subset=["dt_local"]).copy().set_index("dt_local").sort_index()

# 1) Snap to nearest hour, average duplicates
dfh["rounded_hour"] = dfh.index.round("H")
hourly = (
    dfh.groupby("rounded_hour")[["temperature_c", "humidity_pct", "wind_speed_kmh"]]
       .mean()
)
hourly.index.name = "datetime_local"

# 2) Reindex to strict 24-hour grid (IST)
start_day = datetime.strptime(date_input, "%Y-%m-%d").replace(tzinfo=ZoneInfo("Asia/Kolkata"))
hours_index = pd.date_range(start=start_day, periods=24, freq="H")
hourly = hourly.reindex(hours_index)

# 3) Drop timezone so CSV shows plain 'YYYY-MM-DD HH:00' (no '+05:30')
hourly.index = hourly.index.tz_localize(None)
hourly.index.name = "datetime_local"


dfh = dfh.round(2)
# 4) Save strict-hourly CSV (NaNs where missing)
hourly_filename = f"wunderground_hourly_{icao_code}_{date_input.replace('-', '')}.csv"
hourly.to_csv(hourly_filename)
print(f"Hourly (strict) saved to: {hourly_filename}")
dfh = dfh.round(2)
# 5) Save 'filled' hourly CSV (interpolate ≤ 2-hour gaps)
hourly_filled = hourly.copy().interpolate(method="time", limit=2, limit_direction="both")
hourly_filled_filename = f"wunderground_hourly_filled_{icao_code}_{date_input.replace('-', '')}.csv"
hourly_filled.to_csv(hourly_filled_filename)
print(f"Hourly (filled) saved to: {hourly_filled_filename}")

#Visualization

import pandas as pd
import matplotlib.pyplot as plt

# Adjust this if your filename or path differs
icao_code = "VIPT"
date_input = "2025-08-01" # Corrected date to match generated file
csv_file = f"wunderground_hourly_filled_{icao_code}_{date_input.replace('-', '')}.csv"

# Load the interpolated hourly data
try:
    # Use 'datetime_local' column for parsing dates
    df = pd.read_csv(csv_file, parse_dates=["datetime_local"])
except FileNotFoundError:
    print(f" File not found: {csv_file}")
    exit()

# Set datetime_local column as index
df.set_index("datetime_local", inplace=True)

# Create separate plots for each parameter
params = {
    "temperature_c": "Temperature (°C)",
    "humidity_pct": "Humidity (%)",
    "wind_speed_kmh": "Wind Speed (km/h)"
}

for col, label in params.items():
    plt.figure(figsize=(10, 5))
    # Use the index (datetime_local) for the x-axis
    plt.plot(df.index, df[col], marker="o", linewidth=2)
    plt.title(f"{label} on {date_input}", fontsize=14)
    plt.xlabel("Time (IST)", fontsize=12) # Updated label for clarity
    plt.ylabel(label, fontsize=12)
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{col}_{icao_code}_{date_input}.png")
    print(f"Plot saved: {col}_{icao_code}_{date_input}.png")
    plt.close()
