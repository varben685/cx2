from typing import Annotated, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel

from smc_assistant.domain.journal import JournalExecutionStatus


class JournalContentRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        alias_generator=to_camel,
    )

    execution_status: JournalExecutionStatus = JournalExecutionStatus.NOT_RECORDED
    user_note: Annotated[str | None, Field(max_length=5000)] = None
    screenshot_reference: Annotated[str | None, Field(max_length=2048)] = None
    manual_rating: Annotated[int | None, Field(ge=1, le=5)] = None
    manual_override: bool = False
    override_reason: Annotated[str | None, Field(max_length=1000)] = None
    tags: Annotated[list[str], Field(max_length=10)] = Field(default_factory=list)

    @field_validator("user_note", "screenshot_reference", "override_reason")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for value in values:
            tag = value.strip()
            if not tag:
                raise ValueError("Journal tags must not be empty.")
            if len(tag) > 40:
                raise ValueError("Journal tags must not exceed 40 characters.")
            key = tag.casefold()
            if key not in seen:
                normalized.append(tag)
                seen.add(key)
        return normalized

    @model_validator(mode="after")
    def validate_override_reason(self) -> Self:
        if self.manual_override and self.override_reason is None:
            raise ValueError("overrideReason is required for a manual override.")
        if not self.manual_override and self.override_reason is not None:
            raise ValueError("overrideReason requires manualOverride=true.")
        return self


class JournalCreateRequest(JournalContentRequest):
    outcome_id: UUID | None = None


class JournalUpdateRequest(JournalContentRequest):
    expected_revision: Annotated[int, Field(ge=1)]
