{{ config(
    materialized='incremental',
    incremental_strategy='merge',
    unique_key='issue_id',
    partition_by={'field': 'created_at', 'data_type': 'timestamp', 'granularity': 'month'},
    cluster_by=['repo', 'state'],
    on_schema_change='append_new_columns'
) }}

select
    issue_id, repo, issue_number, title, state, state_reason,
    author_login, author_association, comments_count, labels,
    created_at, updated_at, closed_at,
    state = 'closed' and coalesce(state_reason, 'completed') = 'completed' as is_resolved,
    timestamp_diff(closed_at, created_at, hour) / 24.0 as days_to_close,
    _ingested_at
from {{ ref('stg_github__issues') }}

{% if is_incremental() %}
where _ingested_at >= (
    select timestamp_sub(max(_ingested_at), interval 3 day) from {{ this }}
)
{% endif %}