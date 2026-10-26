with parsed as (
    select
        issue_id,
        repo,
        cast(json_value(payload, '$.number') as int64)   as issue_number,
        json_value(payload, '$.title')                   as title,
        json_value(payload, '$.state')                   as state,
        json_value(payload, '$.state_reason')            as state_reason,
        json_value(payload, '$.user.login')              as author_login,
        json_value(payload, '$.author_association')      as author_association,
        cast(json_value(payload, '$.comments') as int64) as comments_count,
        timestamp(json_value(payload, '$.created_at'))   as created_at,
        updated_at,
        timestamp(json_value(payload, '$.closed_at'))    as closed_at,
        json_query(payload, '$.pull_request') is not null as is_pull_request,
        array(
            select json_value(l, '$.name')
            from unnest(json_query_array(payload, '$.labels')) as l
        ) as labels,
        _ingested_at
    from {{ source('raw', 'github_issues') }}
),

deduped as (
    select *
    from parsed
    where true  -- BigQuery cere un WHERE lângă QUALIFY
    qualify row_number() over (
        partition by issue_id
        order by updated_at desc, _ingested_at desc
    ) = 1
)

select * from deduped
where not is_pull_request