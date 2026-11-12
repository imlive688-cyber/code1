import pandas as pd
import requests
import clickhouse_connect

url = "https://archive-api.open-meteo.com/v1/archive"

params = {
    "latitude": 40.3674,
    "longitude": 82.9962,

    "start_date": "2025-11-01",
    "end_date": "2025-11-30",

    "hourly": [
        "temperature_2m",
        "relative_humidity_2m",
        "precipitation",
        "wind_speed_10m"
    ],

    "timezone": "auto"
}


response = requests.get(url, params=params, timeout=30)

data = response.json()


df = pd.DataFrame(data["hourly"])

df["time"] = df["time"].astype(str)

# Handle missing values
df = df.astype(object).where(pd.notna(df), None)

print("\nData extracted successfully!")

print(df.head())

print("\nTotal rows:", len(df))



print("\nConnecting to ClickHouse...")

client = clickhouse_connect.get_client(
    host="localhost",
    port=8123,
    username="admin",
    password="Admin123",
    database="default"
)

print("Connected to ClickHouse successfully!")


client.command("""
    CREATE DATABASE IF NOT EXISTS dwh
""")

print("Database created successfully!")


client.command("""
    CREATE TABLE IF NOT EXISTS dwh.weather_data
    (
        time String,
        temperature_2m Nullable(Float64),
        relative_humidity_2m Nullable(Float64),
        precipitation Nullable(Float64),
        wind_speed_10m Nullable(Float64)
    )
    ENGINE = MergeTree()
    ORDER BY time
""")

print("Table created successfully!")


print("\nInserting weather data...")

client.insert_df(
    table="weather_data",
    database="dwh",
    df=df
)

print("Data inserted successfully!")

result = client.query("""
    SELECT *
    FROM dwh.weather_data
    ORDER BY time
    LIMIT 10
""")

print("\nFirst 10 records:")

for row in result.result_rows:
    print(row)


count = client.query("""
    SELECT COUNT(*)
    FROM dwh.weather_data
""")

print("\nTotal records in ClickHouse:",
      count.result_rows[0][0])


client.close()

print("\nProgram completed successfully!")
