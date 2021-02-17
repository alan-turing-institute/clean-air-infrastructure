from enum import Enum, unique


class LogTag(str, Enum):
    "Log message type"
    info = "info"
    warn = "warn"
    error = "error"
    job_start = "job_start"
    job_finish = "job_finish"


class DatabaseLogger:
    """Database logging for use with urbanair on kubernetes"""

    def _record(self, message, tag):
        pass

    def logger(self, tag):
        def log(self, message):
            self._record(message, tag)
        return log
