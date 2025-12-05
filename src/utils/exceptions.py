# src/utils/exceptions.py
class RetryableError(Exception):
    pass

class FatalError(Exception):
    pass

class DataValidationError(Exception):
    pass

class DriftDetectedWarning(Warning):
    pass

class RetryLimitError(RetryableError):
    pass
