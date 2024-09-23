from datetime import datetime, timezone

utc = timezone.utc


def now():
    return datetime.now(tz=utc)


def today():
    return now().date()
