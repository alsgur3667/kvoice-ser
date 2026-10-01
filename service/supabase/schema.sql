-- ════════════════════════════════════════════════════════════════
-- 보이스 코리안 · Supabase 스키마
-- Supabase 대시보드 → SQL Editor 에 통째로 붙여넣고 Run
-- ════════════════════════════════════════════════════════════════

create extension if not exists "pgcrypto";

-- ── 1. 분석 1건 = 통화 1건 ─────────────────────────────────────
create table if not exists public.analyses (
  id            uuid primary key default gen_random_uuid(),
  created_at    timestamptz not null default now(),
  started_at    timestamptz,
  finished_at   timestamptz,

  status        text not null default 'queued'
                check (status in ('queued','running','done','failed')),
  error         text,

  -- 입력
  filename      text,
  storage_path  text,                    -- audio 버킷 안 경로
  duration_sec  numeric,
  domain        text not null default 'counsel',   -- counsel | edu | care | hr
  region        text not null default 'seoul',     -- seoul | gyeong | jeolla | chung | gangwon | jeju | auto
  region_used   text,                    -- auto일 때 실제 적용된 지역
  threshold     numeric,                 -- 판단 보류 기준 (현장+지역으로 계산)

  -- 결과 요약 (대시보드가 이것만 읽어도 되게)
  model_version text,
  n_windows     int,
  hold_ratio    numeric,                 -- 판단 보류 비율
  flow          text,                    -- '중립 → 분노 → 슬픔 → 기쁨'
  transitions   int,
  risk_seconds  int,
  top_emotion   text,
  summary       jsonb                    -- 현장 규칙이 만든 해석(신호/근거/권장)
);

-- ── 2. 3초 구간 (통화당 100~500행) ──────────────────────────────
create table if not exists public.segments (
  id          bigserial primary key,
  analysis_id uuid not null references public.analyses(id) on delete cascade,
  idx         int  not null,             -- 0,1,2...
  t_start     numeric not null,          -- 초
  emotion     text not null,             -- 보정 후 대표 감정
  confidence  numeric not null,
  hold        boolean not null default false,   -- 판단 보류 여부
  valence     numeric,
  arousal     numeric,
  probs       jsonb not null,            -- 보정 후 7감정 확률
  probs_raw   jsonb                      -- 보정 전 (전/후 비교용)
);
create index if not exists segments_analysis_idx on public.segments(analysis_id, idx);

-- ── 3. 오분류 신고 → 재학습 데이터 ──────────────────────────────
create table if not exists public.feedback (
  id          bigserial primary key,
  created_at  timestamptz not null default now(),
  analysis_id uuid references public.analyses(id) on delete cascade,
  segment_idx int,
  said        text,                      -- 모델이 말한 감정
  correct     text,                      -- 사람이 고른 감정
  note        text
);

-- ── 4. 대시보드용 뷰 ────────────────────────────────────────────
-- security_invoker = on : 뷰를 '부른 사람의 권한'으로 실행한다.
--   이게 없으면 뷰 주인(postgres) 권한으로 돌아서 RLS를 우회하고,
--   Supabase 보안 검사에서 'Security Definer View' 경고가 뜬다.
drop view if exists public.daily_stats;
create view public.daily_stats
with (security_invoker = on) as
select date_trunc('day', created_at)::date as day,
       domain,
       count(*)                                     as calls,
       avg(hold_ratio)                              as avg_hold,
       sum(case when risk_seconds > 30 then 1 else 0 end) as risky_calls,
       avg(risk_seconds)                            as avg_risk_sec
from public.analyses
where status = 'done'
group by 1,2
order by 1 desc;

-- 익명/로그인 사용자는 뷰도 못 읽게 (서버는 secret 키라 그대로 통과)
revoke all on public.daily_stats from anon, authenticated;

-- ── 5. 보안 ────────────────────────────────────────────────────
-- 지금 구성은 "서버(FastAPI)만 DB에 접근"이라 익명 접근은 전부 막는다.
-- service_role 키는 RLS를 우회하므로 서버는 그대로 동작한다.
alter table public.analyses  enable row level security;
alter table public.segments  enable row level security;
alter table public.feedback  enable row level security;
-- (정책을 만들지 않으면 anon/authenticated 는 아무것도 못 읽는다 = 의도한 상태)

-- 나중에 로그인 붙일 때 쓸 예시 정책:
-- alter table public.analyses add column owner uuid default auth.uid();
-- create policy "본인 것만" on public.analyses for select using (owner = auth.uid());

-- ── 6. 스토리지 버킷 ────────────────────────────────────────────
-- 대시보드 → Storage → New bucket → 이름 audio, Public 체크 해제(비공개)
-- 또는 아래 SQL:
insert into storage.buckets (id, name, public)
values ('audio','audio', false)
on conflict (id) do nothing;
