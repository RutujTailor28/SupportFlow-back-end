"""Routing rule Pydantic schemas."""

from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RuleMatchType(str, Enum):
    """How conditions are combined."""

    ALL = "ALL"
    ANY = "ANY"


class RuleField(str, Enum):
    """Fields available for rule conditions."""

    CATEGORY = "Category"
    URGENCY = "Urgency"
    SENTIMENT = "Sentiment"
    CUSTOMER_PLAN = "CustomerPlan"
    SUBJECT = "Subject"
    LANGUAGE = "Language"


class RuleOperator(str, Enum):
    """Comparison operators for rule conditions."""

    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    CONTAINS_ANY = "contains_any"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    IN = "in"


class RuleCondition(BaseModel):
    """Single routing rule condition."""

    model_config = ConfigDict(populate_by_name=True)

    id: str | None = None
    field: RuleField
    operator: RuleOperator
    value: str | list[str]


class RuleAction(BaseModel):
    """Actions applied when a rule matches."""

    model_config = ConfigDict(populate_by_name=True)

    assign_to_team: str = Field(alias="assignToTeam")
    set_priority: str = Field(alias="setPriority")
    auto_tag: str | None = Field(default=None, alias="autoTag")
    notify_escalation_manager: bool | None = Field(default=None, alias="notifyEscalationManager")
    flag_escalation: bool | None = Field(default=None, alias="flagEscalation")
    escalation_reason: str | None = Field(default=None, alias="escalationReason")
    sla_target_minutes: int | None = Field(default=None, alias="slaTargetMinutes")


class RoutingRuleCreateRequest(BaseModel):
    """API request body for creating a routing rule."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""
    order: int = Field(default=1, ge=1, alias="order")
    enabled: bool = True
    match_type: RuleMatchType = Field(default=RuleMatchType.ALL, alias="matchType")
    conditions: list[RuleCondition] = Field(default_factory=list)
    actions: RuleAction


class RoutingRuleUpdateRequest(BaseModel):
    """API request body for updating a routing rule."""

    model_config = ConfigDict(populate_by_name=True)

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    order: int | None = Field(default=None, ge=1, alias="order")
    enabled: bool | None = None
    match_type: RuleMatchType | None = Field(default=None, alias="matchType")
    conditions: list[RuleCondition] | None = None
    actions: RuleAction | None = None


class RoutingRuleResponse(BaseModel):
    """Routing rule returned by the API."""

    model_config = ConfigDict(populate_by_name=True)

    id: UUID
    name: str
    description: str
    order: int
    enabled: bool
    match_type: RuleMatchType = Field(alias="matchType")
    conditions: list[dict[str, Any]]
    actions: dict[str, Any]
    matches_last_30_days: int = Field(alias="matchesLast30Days")
    last_triggered: str | None = Field(default=None, alias="lastTriggered")
