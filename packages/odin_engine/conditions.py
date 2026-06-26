from enum import Enum

from pydantic import BaseModel, Field


class Operator(str, Enum):
    EQ = "equal"
    GT = "greater_than"
    LT = "less_than"
    GTE = "greater_than_or_equal"
    LTE = "less_than_or_equal"
    CROSSES_ABOVE = "crosses_above"
    CROSSES_BELOW = "crosses_below"


class Condition(BaseModel):
    left_indicator: str
    operator: Operator
    right_value: float | None = None
    right_indicator: str | None = None
    case_id: int = 1


class RuleSet(BaseModel):
    conditions: list[Condition] = Field(default_factory=list)
    logic: str = "and"
