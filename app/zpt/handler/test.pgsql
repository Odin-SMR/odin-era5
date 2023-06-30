WITH stwlimits AS (
    SELECT
        min(stw),
        max(stw)
    FROM
        attitude_level1
    WHERE
        mjd > 59881
        AND mjd < 59881.2
)
FROM
    getscansac1((
        SELECT
            min
        FROM stw),(
    SELECT
        max
    FROM stw))
    join 
WHERE
    START != - 1
;