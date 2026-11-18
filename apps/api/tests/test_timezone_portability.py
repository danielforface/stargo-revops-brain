"""Portability regression: Windows must have the IANA time-zone data installed.

The CI Windows/Python 3.14 job executes this test to catch missing tzdata
before an operator sees an unresponsive API worker.
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def test_jerusalem_timezone_is_resolvable_and_correct_for_weekly_kpi():
    jerusalem = ZoneInfo("Asia/Jerusalem")
    # 2026-10-08T21:30Z is already Friday in Israel, and must not count
    # towards the Sun–Thu acquisition reporting window.
    late_utc = datetime(2026, 10, 8, 21, 30, tzinfo=timezone.utc)
    local = late_utc.astimezone(jerusalem)
    assert local.isoformat() == "2026-10-09T00:30:00+03:00"
    # Winter time must differ from the DST offset used in October.
    winter = datetime(2026, 12, 1, 12, 0, tzinfo=timezone.utc).astimezone(jerusalem)
    assert winter.utcoffset() == timedelta(hours=2)
