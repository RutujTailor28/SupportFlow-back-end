"""Escalation-related Pydantic schemas."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class EscalationReason(str, Enum):
    """Escalation trigger reasons (matches frontend)."""

    CHURN_RISK = "Churn Risk Detected"
    LEGAL_LANGUAGE = "Legal Language"
    SLA_RISK = "SLA Risk"
    REPEAT_CONTACT = "Repeat Contact"
    EXECUTIVE_ESCALATION = "Executive Escalation"
    SECURITY_THREAT = "Security Threat"


class EscalationSource(str, Enum):
    """How the escalation was created."""

    MANUAL = "manual"
    AI = "ai"
    RULE = "rule"
    DETECTION = "detection"


class EscalationCreateRequest(BaseModel):
    """API request body for creating an escalation record."""

    model_config = ConfigDict(populate_by_name=True)

    reason: EscalationReason
    trigger_phrases: list[str] = Field(default_factory=list, alias="triggerPhrases")
    notes: str | None = None
    source: EscalationSource = EscalationSource.MANUAL


class EscalationAcknowledgeRequest(BaseModel):
    """API request body for acknowledging an escalation."""

    model_config = ConfigDict(populate_by_name=True)

    acknowledged: bool = True
    notes: str | None = None
