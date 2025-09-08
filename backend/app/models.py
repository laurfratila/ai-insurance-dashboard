
from pydantic import BaseModel
from datetime import date
from typing import Optional

class TimeSeriesPoint(BaseModel):
    period: date
    value: float | int | None

class TwoSeriesPoint(BaseModel):
    period: date
    a: float | int
    b: float | int

class RatioSeriesPoint(BaseModel):
    period: date
    numerator: float | int
    denominator: float | int
    ratio: float | None

class BreakdownItem(BaseModel):
    key: str
    value: float | int

class DemographicItem(BaseModel):
    age_band: str
    county_name: str
    customers: int

class SLAItem(BaseModel):
    period: date
    breaches_gt_30d: int
    breaches_gt_60d: int
    still_open: int
    total_reported: int
