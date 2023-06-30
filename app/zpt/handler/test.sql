with att as (
    select stw,
        mjd,
        latitude,
        longitude
    from attitude_level1
    where mjd >= 59881
        and mjd < 59881.2
),
min_stw as (
    select min(stw)
    from att
),
max_stw as (
    select max(stw)
    from att
),
scans as (
    select 'ac1' as backend,
        *
    from getscansac1(
            (
                select min
                from min_stw
            ),
            (
                select max
                from max_stw
            )
        )
    union all
    select 'ac2' as backend,
        *
    from getscansac2(
            (
                select min
                from min_stw
            ),
            (
                select max
                from max_stw
            )
        )
),
data as (
    select start as scanid,
        stw,
        backend,
        mjd,
        latitude,
        longitude,
        row_number() over (
            partition by start,
            backend
            order by mjd
        ),
        last_value(latitude) over w as end_latitude,
        last_value(longitude) over w as end_longitude,
        last_value(mjd) over w as end_mjd
    from scans
        left join att using (stw) WINDOW w AS (
            partition by start,
            backend
            order by stw RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        )
)
select scanid,
    backend,
    mjd,
    end_mjd,
    latitude,
    end_latitude,
    longitude,
    end_longitude
from data
where row_number = 1
    and scanid != -1::bigint