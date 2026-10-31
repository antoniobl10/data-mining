class PlatformError(Exception):
    """Base error for actionable platform failures."""


class ContractViolationError(PlatformError):
    """A dataset violates a versioned contract."""


class DataQualityError(PlatformError):
    """Critical quality failure; fix data before resuming."""


class PipelineExecutionError(PlatformError):
    """A dependency, checkpoint or stage execution failed."""


class ModelScoringError(PlatformError):
    """Model artifact/schema/lifecycle prevents scoring."""


class SchemaValidationError(ContractViolationError):
    """Required columns or types are incompatible."""
