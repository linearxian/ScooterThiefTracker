import folium
from folium.plugins import FeatureGroupSubGroup
import pandas as pd
from haversine import haversine

def apply_offset(lat, lon, angle, distance=0.0001):
    import math
    new_lat = lat + distance * math.sin(math.radians(angle))
    new_lon = lon + distance * math.cos(math.radians(angle))
    return new_lat, new_lon

def format_time(minutes):
    if pd.isna(minutes):
        return "Unknown duration"
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    if hours:
        return f"{hours} h {mins} min"
    return f"{mins} min"

data = pd.read_csv("./../AirtagAlex/Airtags.csv")
data["datetime"] = pd.to_datetime(data["datetime"])
data.set_index("datetime", inplace=True)

m = folium.Map(location=[data["locationlatitude"].mean(), data["locationlongitude"].mean()], zoom_start=15)

grouped = data.groupby(data.index.date)

for day, group_data in grouped:
    group_data['timestamp_diff'] = group_data['locationtimestamp'].diff().shift(-1) / (1000 * 60)
    
    if pd.isna(group_data['timestamp_diff'].iloc[-1]):
        next_day = pd.Timestamp(day) + pd.Timedelta(days=1)
        if next_day in data.index:
            last_timestamp = group_data['locationtimestamp'].iloc[-1]
            next_timestamp = data.loc[next_day]['locationtimestamp']
            difference = (next_timestamp - last_timestamp) / (1000 * 60)
            group_data['timestamp_diff'].iloc[-1] = difference

    fg_day = folium.FeatureGroup(name=str(day))
    subgroup = FeatureGroupSubGroup(fg_day, name=str(day))
    m.add_child(fg_day)
    m.add_child(subgroup)

    locations = group_data[["locationlatitude", "locationlongitude"]].values.tolist()
    folium.PolyLine(locations, color="blue", weight=2.5, opacity=0.7).add_to(subgroup)
    
    top2_stays = group_data['timestamp_diff'].nlargest(2).index

    for i, (_, row) in enumerate(group_data.iterrows()):
        current_coords = (row["locationlatitude"], row["locationlongitude"])
        label_coords = current_coords
        for j, (_, other_row) in enumerate(group_data.iterrows()):
            if i == j:
                continue
            other_coords = (other_row["locationlatitude"], other_row["locationlongitude"])
            if haversine(label_coords, other_coords, unit="m") < 50:
                angle_offset = 45 * i
                label_coords = apply_offset(*label_coords, angle=angle_offset, distance=0.0005)
                folium.PolyLine([current_coords, label_coords], color="blue", weight=1, opacity=0.7, dash_array=[5, 5]).add_to(subgroup)

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
        ).add_to(subgroup)

        if row.name in top2_stays:
            label_style = "<div style='background-color: red; padding: 3px; border-radius: 50%; color: white;'>"
        else:
            label_style = "<div style='background-color: white; padding: 2px; border-radius: 50%;'>"

        folium.Marker(
            location=label_coords,
            icon=folium.DivIcon(html=f"{label_style}{i+1}</div>"),
            popup=f"{row.name} - Stay: {format_time(row['timestamp_diff'])}"
        ).add_to(subgroup)

folium.LayerControl(collapsed=False).add_to(m)
m.save("map.html")
