from datetime import date

from src.dress.models import Season


def season_for_date(d: date) -> Season:
    """Northern Hemisphere meteorological seasons."""
    month = d.month
    if month in (3, 4, 5):
        return Season.spring
    if month in (6, 7, 8):
        return Season.summer
    if month in (9, 10, 11):
        return Season.fall
    return Season.winter
