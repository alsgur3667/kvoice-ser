-- ════════════════════════════════════════════════════════════
-- 'Security Definer View' 경고 해소용 — SQL Editor 에 붙여넣고 Run
-- ════════════════════════════════════════════════════════════
drop view if exists public.daily_stats;

create view public.daily_stats
with (security_invoker = on) as        -- 뷰를 '부른 사람의 권한'으로 실행
select date_trunc('day', created_at)::date as day,
       domain,
       count(*)                                           as calls,
       avg(hold_ratio)                                    as avg_hold,
       sum(case when risk_seconds > 30 then 1 else 0 end) as risky_calls,
       avg(risk_seconds)                                  as avg_risk_sec
from public.analyses
where status = 'done'
group by 1,2
order by 1 desc;

revoke all on public.daily_stats from anon, authenticated;
