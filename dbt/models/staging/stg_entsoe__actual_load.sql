with source as (
    select * from {{ source("entsoe", "actual_load")}}
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
        row_number() over 
            (partition by ts_utc order by ts_utc) as row_num
    from renamed
)
select * from deduped