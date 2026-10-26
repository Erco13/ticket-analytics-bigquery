with issues as (
    select repo, created_at, closed_at from {{ ref('fct_issues') }}
),
days as (
    select day
    from unnest(generate_date_array(
        (select min(date(created_at)) from issues), current_date())) as day
),
repos as (select distinct repo from issues),
opened as (
    select repo, date(created_at) as day, count(*) as opened
    from issues group by 1, 2
),
closed as (
    select repo, date(closed_at) as day, count(*) as closed
    from issues where closed_at is not null group by 1, 2
)
select
    r.repo,
    d.day,
    coalesce(o.opened, 0) as opened,
    coalesce(c.closed, 0) as closed,
    sum(coalesce(o.opened, 0) - coalesce(c.closed, 0))
        over (partition by r.repo order by d.day) as backlog
from days as d
cross join repos as r
left join opened as o on o.repo = r.repo and o.day = d.day
left join closed as c on c.repo = r.repo and c.day = d.day