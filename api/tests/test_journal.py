from datetime import date, datetime, timezone
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError

from models.daily_log import LogEntry
from routers.journal import _Day, _local_midnight, _to_journal_day
from schemas.journal import CheckinUpdate, LogEntryCreate

SP = ZoneInfo("America/Sao_Paulo")


def test_local_midnight_uses_user_timezone():
    midnight = _local_midnight(date(2026, 10, 4), SP)
    # Meia-noite em São Paulo (UTC-3) = 03:00 UTC
    assert midnight.astimezone(timezone.utc) == datetime(2026, 10, 4, 3, 0, tzinfo=timezone.utc)


def test_journal_day_recap_sums_and_top_categories():
    day = _Day(mood=4, energy=2, tasks_done=["a", "b"])
    for category, amount in [("mercado", 50.0), ("uber", 12.5), ("mercado", 30.0), ("cafe", 8.0), ("livro", 40.0)]:
        day.spent += amount
        day.by_category[category] += amount

    out = _to_journal_day(date(2026, 10, 4), day)

    assert out.mood == 4 and out.energy == 2
    assert out.recap.tasks_done == ["a", "b"]
    assert out.recap.spent == 140.5
    assert [c.category for c in out.recap.top_categories] == ["mercado", "livro", "uber"]


def test_journal_day_keeps_entries():
    entry = LogEntry(id=uuid4(), user_id=uuid4(), date=date(2026, 10, 4), content="oi", url=None,
                     created_at=datetime(2026, 10, 4, 12, tzinfo=timezone.utc))
    out = _to_journal_day(date(2026, 10, 4), _Day(entries=[entry]))
    assert [e.content for e in out.entries] == ["oi"]


@pytest.mark.parametrize("url", ["https://wotaku.wiki/", "http://localhost:5173"])
def test_entry_accepts_http_urls(url):
    assert LogEntryCreate(content="link", url=url).url == url


@pytest.mark.parametrize("url", ["javascript:alert(1)", "data:text/html,oi", "ftp://x"])
def test_entry_rejects_other_url_schemes(url):
    with pytest.raises(ValidationError):
        LogEntryCreate(content="link", url=url)


def test_entry_requires_content():
    with pytest.raises(ValidationError):
        LogEntryCreate(content="")


@pytest.mark.parametrize("value", [0, 6])
def test_checkin_scale_is_1_to_5(value):
    with pytest.raises(ValidationError):
        CheckinUpdate(mood=value)


def test_checkin_only_sends_what_changed():
    assert CheckinUpdate(energy=3).model_dump(exclude_unset=True) == {"energy": 3}
