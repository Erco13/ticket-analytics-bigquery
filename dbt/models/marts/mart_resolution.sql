select
    repo,
    date_trunc(date(created_at), month) as month_created,
    count(*) as created,
    countif(is_resolved) as resolved,
    approx_quantiles(if(is_resolved, days_to_close, null), 100)[safe_offset(50)]
        as median_days_to_close,
    safe_divide(countif(is_resolved and days_to_close <= 7), countif(is_resolved))
        as pct_resolved_within_7d
from {{ ref('fct_issues') }}
group by 1, 2