# -*- coding: utf-8 -*-
"""
Supabase 접근 (REST). 클라이언트 라이브러리 대신 httpx로 직접 호출 —
의존성이 적고, 무슨 요청이 오가는지 그대로 보여서 발표 때 설명하기 쉽다.
service_role 키는 서버에서만 쓴다 (웹에 내려보내지 않음).
"""
import httpx
from typing import Any, Dict, List, Optional
from .config import settings


# ── Supabase 설정이 비어 있으면 메모리 저장소로 동작 (개발용) ──────────
MEMORY = not bool(settings.supabase_url)
_MEM: Dict[str, list] = {"analyses": [], "segments": [], "feedback": []}
_FILES: Dict[str, bytes] = {}


def _headers(extra: Optional[dict] = None) -> dict:
    key = settings.supabase_service_key
    h = {"apikey": key, "Content-Type": "application/json"}
    # 옛 service_role 키는 JWT(eyJ...) → Authorization 헤더도 같이 보낸다.
    # 새 secret 키(sb_secret_...)는 JWT가 아니라 apikey 헤더로만 보내야 한다.
    if key.startswith("eyJ"):
        h["Authorization"] = f"Bearer {key}"
    if extra:
        h.update(extra)
    return h


def _rest(path: str) -> str:
    return f"{settings.supabase_url}/rest/v1/{path}"


# ── 테이블 ────────────────────────────────────────────────────────────
def insert(table: str, row: Dict[str, Any]) -> Dict[str, Any]:
    if MEMORY:
        import uuid as _u, datetime as _d
        row = dict(row)
        row.setdefault("id", str(_u.uuid4()))
        row.setdefault("created_at", _d.datetime.utcnow().isoformat() + "Z")
        _MEM[table].append(row)
        return row
    r = httpx.post(_rest(table), headers=_headers({"Prefer": "return=representation"}),
                   json=row, timeout=30)
    r.raise_for_status()
    return r.json()[0]


def insert_many(table: str, rows: List[Dict[str, Any]], chunk: int = 500) -> int:
    if MEMORY:
        _MEM[table].extend(rows)
        return len(rows)
    n = 0
    for i in range(0, len(rows), chunk):
        r = httpx.post(_rest(table), headers=_headers({"Prefer": "return=minimal"}),
                       json=rows[i:i + chunk], timeout=60)
        r.raise_for_status()
        n += len(rows[i:i + chunk])
    return n


def update(table: str, match: Dict[str, Any], patch: Dict[str, Any]) -> None:
    if MEMORY:
        import datetime as _d
        patch = {k: (_d.datetime.utcnow().isoformat() + "Z" if v == "now()" else v) for k, v in patch.items()}
        for r0 in _MEM[table]:
            if all(r0.get(k) == v for k, v in match.items()):
                r0.update(patch)
        return
    q = "&".join(f"{k}=eq.{v}" for k, v in match.items())
    r = httpx.patch(f"{_rest(table)}?{q}", headers=_headers({"Prefer": "return=minimal"}),
                    json=patch, timeout=30)
    r.raise_for_status()


def select(table: str, query: str = "select=*") -> List[Dict[str, Any]]:
    if MEMORY:
        rows = list(_MEM.get(table, []))
        for part in query.split("&"):
            if "=eq." in part and not part.startswith("select"):
                k, v = part.split("=eq.")
                rows = [r0 for r0 in rows if str(r0.get(k)) == v]
        if "order=created_at.desc" in query:
            rows = rows[::-1]
        if "order=idx.asc" in query:
            rows = sorted(rows, key=lambda r0: r0.get("idx", 0))
        for part in query.split("&"):
            if part.startswith("limit="):
                rows = rows[: int(part.split("=")[1])]
        return rows
    r = httpx.get(f"{_rest(table)}?{query}", headers=_headers(), timeout=30)
    r.raise_for_status()
    return r.json()


def claim_next_queued() -> Optional[Dict[str, Any]]:
    """워커가 큐에서 하나 집어오기 (status 를 running 으로 바꾸며 선점)."""
    rows = select("analyses", "select=*&status=eq.queued&order=created_at.asc&limit=1")
    if not rows:
        return None
    row = rows[0]
    if MEMORY:
        update("analyses", {"id": row["id"]}, {"status": "running", "started_at": "now()"})
        return row
    r = httpx.patch(f"{_rest('analyses')}?id=eq.{row['id']}&status=eq.queued",
                    headers=_headers({"Prefer": "return=representation"}),
                    json={"status": "running", "started_at": "now()"}, timeout=30)
    r.raise_for_status()
    got = r.json()
    return got[0] if got else None      # 다른 워커가 먼저 가져갔으면 None


# ── 스토리지 ──────────────────────────────────────────────────────────
def upload_audio(path: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    if MEMORY:
        _FILES[path] = data
        return path
    url = f"{settings.supabase_url}/storage/v1/object/{settings.supabase_bucket}/{path}"
    h = _headers({"Content-Type": content_type, "x-upsert": "true"})
    r = httpx.post(url, headers=h, content=data, timeout=120)
    r.raise_for_status()
    return path


def download_audio(path: str) -> bytes:
    if MEMORY:
        return _FILES[path]
    url = f"{settings.supabase_url}/storage/v1/object/{settings.supabase_bucket}/{path}"
    r = httpx.get(url, headers=_headers(), timeout=120)
    r.raise_for_status()
    return r.content


def sign_audio(path: str, expires: int = 3600) -> str:
    """비공개 버킷의 파일을 '일정 시간만 유효한 링크'로 만들어 준다.
    브라우저가 Supabase에서 직접 받아가므로 우리 서버가 큰 파일을 중계하지 않는다."""
    url = f"{settings.supabase_url}/storage/v1/object/sign/{settings.supabase_bucket}/{path}"
    r = httpx.post(url, headers=_headers(), json={"expiresIn": expires}, timeout=30)
    r.raise_for_status()
    signed = r.json()["signedURL"]           # 예: /object/sign/audio/xxx?token=...
    return f"{settings.supabase_url}/storage/v1{signed}"


def ping() -> bool:
    if MEMORY:
        return True
    try:
        httpx.get(_rest("analyses?select=id&limit=1"), headers=_headers(), timeout=5).raise_for_status()
        return True
    except Exception:
        return False
