with source as (
    select * from {{ source("open_meteo", "weather")}}
),
renamed as (
    select
        cast(ts as timestamptz) as ts_utc,
        location,
        temperature_2m,
        relative_humidity_2m,
        precipitation,
        apparent_temperature,
        cloud_cover,
        wind_speed_10m
    from source
),
deduped as (
    select 
        *,
        row_number() over (
            partition by ts_utc, location order by temperature_2m
        ) as row_num
    from renamed
)
select  
    ts_utc,
    location,
    temperature_2m,
    relative_humidity_2m,
    precipitation,
    apparent_temperature,
    cloud_cover,
    wind_speed_10m
from deduped
where row_num = 1