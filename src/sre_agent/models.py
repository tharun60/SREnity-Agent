from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class Severity(StrEnum):
    info = "info"
    warning = "warning"
    critical = "critical"


class Signal(BaseModel):
    source: str
    kind: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    labels: dict[str, str] = Field(default_factory=dict)
    value: float | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class ToolCall(BaseModel):
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    rationale: str


class Finding(BaseModel):
    title: str
    confidence: float = Field(ge=0, le=1)
    explanation: str
    evidence: list[str]
    remediation: list[str]
    verification: list[str]


class ProposedAction(BaseModel):
    action: str
    target: str
    command: str
    risk: str = "medium"
    requires_approval: bool = True


class Incident(BaseModel):
    id: str = Field(default_factory=lambda: f"inc-{uuid4().hex[:10]}")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    environment: str
    namespace: str
    severity: Severity
    summary: str
    status: str = "open"
    signals: list[Signal] = Field(default_factory=list)
    finding: Finding | None = None
    proposed_actions: list[ProposedAction] = Field(default_factory=list)
    timeline: list[str] = Field(default_factory=list)

