"""Pydantic schemas for AI Financial Analyst service and API boundaries."""

from typing import List
from pydantic import BaseModel, ConfigDict, Field, field_validator


class AnalystQuestion(BaseModel):
    """Input payload containing user's portfolio inquiry."""

    model_config = ConfigDict(extra="forbid")

    question: str = Field(
        ...,
        description="Natural language question regarding portfolio performance, risk, or asset allocation.",
        examples=["Why did my portfolio underperform the benchmark last month?"],
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Question cannot be empty or contain only whitespace.")
        if len(trimmed) > 1000:
            raise ValueError(
                f"Question exceeds maximum allowed length of 1000 characters (received {len(trimmed)})."
            )
        return trimmed


class AnalystResponse(BaseModel):
    """Structured response from the AI Financial Analyst with deterministic grounding."""

    model_config = ConfigDict(from_attributes=True)

    question: str = Field(..., description="The original sanitized question asked by the user.")
    answer: str = Field(..., description="Evidence-grounded explanation based strictly on supplied metrics.")
    portfolio_id: str = Field(..., description="Unique identifier of the analyzed portfolio.")
    metrics_used: List[str] = Field(
        default_factory=list,
        description="List of deterministic metrics supplied to and referenced in the analysis.",
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Informative warnings regarding missing, partial, or uninitialized portfolio data.",
    )
