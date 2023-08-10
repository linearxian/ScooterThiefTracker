import folium
import pandas as pd
from datetime import datetime
from haversine import haversine

def apply_offset(lat, lon, angle, distance=0.0001):
    """
    Apply a slight offset to a latitude and longitude pair.
    """
    import math
    new_lat = lat + distance * math.sin(math.radians(angle))
    new_lon = lon + distance * math.cos(math.radians(angle))
    return new_lat, new_lon

data = pd.read_csv("./../AirtagAlex/Airtags.csv")
data["datetime"] = pd.to_datetime(data["datetime"])

m = folium.Map(location=[data["locationlatitude"].mean(), data["locationlongitude"].mean()], zoom_start=15)

# Draw the trajectory
locations = data[["locationlatitude", "locationlongitude"]].values.tolist()
folium.PolyLine(locations, color="blue", weight=2.5, opacity=0.7).add_to(m)

# Calculate time difference for stay duration
data['timestamp_diff'] = data['locationtimestamp'].diff().shift(-1) / (1000 * 60)  # Convert to minutes

for i, row in data.iterrows():
    current_coords = (row["locationlatitude"], row["locationlongitude"])
    
    # Check for close markers and apply offset
    for j, other_row in data.iterrows():
        if i == j:
            continue
        other_coords = (other_row["locationlatitude"], other_row["locationlongitude"])
        if haversine(current_coords, other_coords, unit="m") < 50:  # points closer than 50 meters
            angle_offset = 45 * i  # Varying the angle for multiple close points
            current_coords = apply_offset(*current_coords, angle=angle_offset)

    # Decide marker size based on stay duration
    if row['timestamp_diff'] <= 10:
        size = 5
    elif row['timestamp_diff'] <= 60:
        size = 10
    elif row['timestamp_diff'] <= 120:
        size = 15
    elif row['timestamp_diff'] <= 240:
        size = 20
    elif row['timestamp_diff'] <= 1440:
        size = 25
    else:
        size = 5

    folium.CircleMarker(
        location=current_coords,
        radius=size,
        fill=True,
        color='blue',
        fill_opacity=0.6
    ).add_to(m)

    folium.Marker(
        location=current_coords,
        icon=folium.DivIcon(html=f"<div style='background-color: white; padding: 2px; border-radius: 50%;'>{i+1}</div>"),
        popup=f"{row['datetime']} - Stay: {row['timestamp_diff']:.2f} minutes"
    ).add_to(m)

m.save("map.html")
