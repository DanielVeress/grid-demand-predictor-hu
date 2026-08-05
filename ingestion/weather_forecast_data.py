import io
import os
import time

import openmeteo_requests
import pandas as pd
import psycopg2
import requests_cache
from dotenv import load_dotenv
from retry_requests import retry

SCHEMA = "raw"


def _get_env_variable(var_name: str):
    var_value = os.getenv(var_name)
    if var_value is None:
        raise RuntimeError(f"{var_name} is not set in .env")
    return var_value


def get_weather_data(run_date):
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession(
        ".cache/weather_forecast_cache", expire_after=3600
    )
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://single-runs-api.open-meteo.com/v1/forecast"
    location = "Budapest"
    params = {
        "latitude": 47.4979,
        "longitude": 19.0402,
        "run": run_date.strftime("%Y-%m-%d"),
        "hourly": [
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "apparent_temperature",
            "cloud_cover",
            "wind_speed_10m",
        ],
        "timezone": "GMT",
        "models": "ecmwf_ifs",
        "forecast_days": 2,  # 48 hours
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_relative_humidity_2m = hourly.Variables(1).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()
    hourly_apparent_temperature = hourly.Variables(3).ValuesAsNumpy()
    hourly_cloud_cover = hourly.Variables(4).ValuesAsNumpy()
    hourly_wind_speed_10m = hourly.Variables(5).ValuesAsNumpy()

    hourly_data = {
        "timestamp": pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left",
        )
    }

    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["relative_humidity_2m"] = hourly_relative_humidity_2m
    hourly_data["precipitation"] = hourly_precipitation
    hourly_data["apparent_temperature"] = hourly_apparent_temperature
    hourly_data["cloud_cover"] = hourly_cloud_cover
    hourly_data["wind_speed_10m"] = hourly_wind_speed_10m

    hourly_dataframe = pd.DataFrame(data=hourly_data)
    hourly_dataframe["location"] = location

    hourly_dataframe["run_ts"] = pd.to_datetime(run_date, utc=True)

    col_order = ["run_ts", "timestamp", "location"] + [
        col for col in hourly_data if col != "timestamp"
    ]
    hourly_dataframe = hourly_dataframe[col_order]

    return hourly_dataframe


def save_weather_forecast_to_postgres(hourly_dataframe):
    POSTGRES_USER = _get_env_variable("POSTGRES_USER")
    POSTGRES_PASSWORD = _get_env_variable("POSTGRES_PASSWORD")
    POSTGRES_DB = _get_env_variable("POSTGRES_DB")
    POSTGRES_HOST = _get_env_variable("POSTGRES_HOST")
    POSTGRES_PORT = _get_env_variable("POSTGRES_PORT")

    with (
        psycopg2.connect(
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
        ) as conn,
        conn.cursor() as cur,
    ):
        cur.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")

        cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {SCHEMA}.weather_forecast (
                    run_ts TIMESTAMPTZ,
                    ts TIMESTAMPTZ,
                    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    revision_num BIGSERIAL,
                    location TEXT,
                    temperature_2m FLOAT,
                    relative_humidity_2m FLOAT,
                    precipitation FLOAT,
                    apparent_temperature FLOAT,
                    cloud_cover FLOAT,
                    wind_speed_10m FLOAT
                )        
            """)

        csv_buffer = io.StringIO()
        hourly_dataframe.to_csv(csv_buffer, index=False, header=False)
        csv_buffer.seek(0)

        cur.copy_expert(
            f"""
                COPY {SCHEMA}.weather_forecast 
                (run_ts, ts, location, temperature_2m, 
                relative_humidity_2m, precipitation, 
                apparent_temperature, cloud_cover, wind_speed_10m)
                FROM STDIN WITH CSV
            """,
            csv_buffer,
        )

        conn.commit()


def main():
    load_dotenv()

    current_date = pd.Timestamp(year=2024, month=8, day=3)
    end_date = pd.Timestamp(year=2026, month=8, day=3)

    while current_date <= end_date:
        # Get and save run
        try:
            print("Date:", current_date.strftime("%Y-%m-%d"))
            hourly_dataframe = get_weather_data(run_date=current_date)
            save_weather_forecast_to_postgres(hourly_dataframe)
        except Exception as e:
            print("\tError:", e)

        # Go to next run time
        current_date += pd.Timedelta(days=1)
        time.sleep(0.5)


if __name__ == "__main__":
    main()
