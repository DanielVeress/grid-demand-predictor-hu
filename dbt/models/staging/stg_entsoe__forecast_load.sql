with source as (
    select * from {{ source("entsoe", "forecast_load")}}
),
renamed as (
    select
        cast(ts as timestamptz) as ts_utc,
        load as load_mw
    from source
),
deduped as (
    select 
        ts_utc, 
        load_mw,
        row_number() over (
            partition by ts_utc order by load_mw
        ) as row_num
    from renamed
)
select ts_utc, load_mw 
from deduped
where row_num = 1