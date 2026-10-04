from datetime import date, timedelta

from deps import get_user_today, get_user_tz
from routers.habits import _calc_streak

TODAY = date(2026, 10, 4)


def days_ago(*offsets: int) -> set[date]:
    return {TODAY - timedelta(days=n) for n in offsets}


def test_no_completions():
    assert _calc_streak(set(), TODAY) == 0


def test_streak_including_today():
    assert _calc_streak(days_ago(0, 1, 2), TODAY) == 3


def test_streak_survives_until_today_is_checked():
    # Feito ontem e anteontem, hoje ainda não — streak continua vivo
    assert _calc_streak(days_ago(1, 2), TODAY) == 2


def test_streak_breaks_after_a_full_missed_day():
    assert _calc_streak(days_ago(2, 3, 4), TODAY) == 0


def test_gap_stops_the_count():
    assert _calc_streak(days_ago(0, 1, 3, 4), TODAY) == 2


def test_user_today_uses_timezone_header():
    # Kiribati (UTC+14) e Samoa Americana (UTC-11) nunca estão no mesmo dia
    kiritimati = get_user_today(get_user_tz("Pacific/Kiritimati"))
    pago_pago = get_user_today(get_user_tz("Pacific/Pago_Pago"))
    assert kiritimati != pago_pago


def test_user_today_falls_back_on_bad_timezone():
    assert get_user_tz("Not/AZone") is None
    assert get_user_today(get_user_tz(None)) == date.today()
