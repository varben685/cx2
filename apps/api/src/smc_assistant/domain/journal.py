from enum import StrEnum


class JournalExecutionStatus(StrEnum):
    NOT_RECORDED = "NOT_RECORDED"
    TAKEN = "TAKEN"
    SKIPPED = "SKIPPED"
