import io
import os

import pandas as pd
import psycopg2
from dotenv import load_dotenv
from entsoe import EntsoePandasClient

SCHEMA = "raw"


def _get_env_variable(var_name: str):
    var_value = os.getenv(var_name)
    if var_value is None:
        raise RuntimeError(f"{var_name} is not set in .env")
    return var_value


def get_load_data(start_date=None, end_date=None, interval=90):
    ENTSOE_API = _get_env_variable("ENTSOE_KEY")

    if start_date is None and end_date is None:
        # Dynamically create interval start and end date
        end_date = pd.Timestamp.now(tz="UTC") + pd.Timedelta(days=2)
        start_date = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=interval)
    elif start_date is None or end_date is None:
        raise ValueError(
            "Both start_date and end_date must be provided together, or both must be left as None."
        )

    country_code = "HU"

    client = EntsoePandasClient(api_key=ENTSOE_API)
    load_df = client.query_load(country_code, start=start_date, end=end_date)
    forecast_df = client.query_load_forecast(
        country_code, start=start_date, end=end_date
    )

    return load_df.reset_index(), forecast_df.reset_index()


def save_load_to_postgres(df, table_name):
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
                CREATE TABLE IF NOT EXISTS {SCHEMA}.{table_name} (
                    ts TIMESTAMPTZ,
                    ingested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    revision_num BIGSERIAL,
                    load FLOAT
                )        
            """)

        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, header=False)
        csv_buffer.seek(0)

        cur.copy_expert(
            f"""
                COPY {SCHEMA}.{table_name} 
                (ts, load)
                FROM STDIN WITH CSV
            """,
            csv_buffer,
        )

        conn.commit()


def main():
    load_dotenv()
    load_df, forecast_df = get_load_data()
    save_load_to_postgres(load_df, "actual_load")
    save_load_to_postgres(forecast_df, "forecast_load")


if __name__ == "__main__":
    main()
