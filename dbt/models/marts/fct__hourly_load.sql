with load as (
    select 
        date_trunc('hour', ts_utc) as ts_hour,
        avg(load_mw) as load_mw
    from {{ ref("stg_entsoe__actual_load") }}
    group by 1
),

forecast as (
    select 
        date_trunc('hour', ts_utc) as ts_hour,
        avg(load_mw) as forecast_mw
    from {{ ref("stg_entsoe__forecast_load") }}
    group by 1
),

weather as (
    select 
        ts_utc as ts_hour,
        location,
        temperature_2m,
        relative_humidity_2m,
        precipitation,
        apparent_temperature,
        cloud_cover,
        wind_speed_10m
    from {{ ref("stg_open_meteo__actual_weather") }}
)

select
    l.ts_hour,
    l.load_mw,
    f.forecast_mw,
    w.location,
    w.temperature_2m,
    w.relative_humidity_2m,
    w.precipitation,
    w.apparent_temperature,
    w.cloud_cover,
    w.wind_speed_10m,
    extract(hour  from l.ts_hour) as hour_of_the_day,
    extract(dow   from l.ts_hour) as day_of_the_week,
    extract(month from l.ts_hour) as month
from load l
left join forecast f on l.ts_hour = f.ts_hour
left join weather w  on l.ts_hour = w.ts_hour