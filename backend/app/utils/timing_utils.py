"""Timezone and timestamp utilities for IST conversion and timing analysis."""
from datetime import datetime, date, time, timedelta, timezone
import pytz
from app.config import settings

IST = pytz.timezone(settings.TIMEZONE)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_ist(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST)


def ist_now() -> datetime:
    return datetime.now(IST)


def ist_today() -> date:
    return ist_now().date()


def ist_start_of_day(d: date | None = None) -> datetime:
    d = d or ist_today()
    return IST.localize(datetime.combine(d, time.min))


def ist_end_of_day(d: date | None = None) -> datetime:
    d = d or ist_today()
    return IST.localize(datetime.combine(d, time.max))


def meal_spacing_ok(timestamps: list[datetime], min_gap_hours: float = 3.0) -> bool:
    """Check that major meals have ≥ min_gap_hours between them."""
    if len(timestamps) < 2:
        return True
    sorted_ts = sorted(timestamps)
    for i in range(1, len(sorted_ts)):
        gap = (sorted_ts[i] - sorted_ts[i - 1]).total_seconds() / 3600
        if gap < min_gap_hours:
            return False
    return True


def post_meal_activity_ok(meal_ts: list[datetime], workout_ts: list[datetime], gap_minutes: int = 60) -> bool:
    """No intense workout within gap_minutes of a meal."""
    for m in meal_ts:
        for w in workout_ts:
            if abs((w - m).total_seconds()) < gap_minutes * 60:
                return False
    return True


def morning_hydration(water_ts: list[datetime], wake_time: datetime | None = None) -> bool:
    """Water logged within 30 min of assumed wake time (default 07:00)."""
    if not water_ts:
        return False
    if wake_time is None:
        wake_time = water_ts[0].replace(hour=7, minute=0, second=0, microsecond=0)
    for wt in water_ts:
        if 0 <= (wt - wake_time).total_seconds() <= 1800:
            return True
    return False


def exercise_in_window(workout_ts: list[datetime], start_hour: int = 6, end_hour: int = 20) -> bool:
    """Workout between start_hour and end_hour (circadian alignment)."""
    for wt in workout_ts:
        local = to_ist(wt)
        if start_hour <= local.hour < end_hour:
            return True
    return False


def sleep_consistency(today_sleep: datetime | None, yesterday_sleep: datetime | None, tolerance_hours: float = 1.0) -> bool:
    """Sleep time within ±tolerance of previous night."""
    if today_sleep is None or yesterday_sleep is None:
        return False
    diff = abs((today_sleep - yesterday_sleep).total_seconds() - 86400)
    return diff <= tolerance_hours * 3600


def late_night_meal(meal_ts: list[datetime], cutoff_hour: int = 21) -> bool:
    """Any meal after cutoff_hour."""
    for mt in meal_ts:
        local = to_ist(mt)
        if local.hour >= cutoff_hour:
            return True
    return False
