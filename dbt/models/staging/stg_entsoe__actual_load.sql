with source as (
    select * from {{ source("entsoe", "actual_load")}}
),
renamed as (
    select
        cast(ts as timestamptz) as ts_utc,
        ingested_at,
        revision_num,
        load as load_mw
    from source
),
deduped as (
    select
        ts_utc,
        ingested_at,
        load_mw,
        row_number() over (
            partition by ts_utc
            order by ingested_at desc, revision_num desc
        ) as row_num
    from renamed
)
select ts_utc, ingested_at, load_mw 
from deduped
where row_num = 1