"""One JSON object per line; no customer records or credential-bearing values."""

import json
import logging
import re
from datetime import datetime, timezone

SECRET = re.compile(r"(?i)(bearer\s+\S+|(?:token|password|secret|authorization)\s*[:=]\s*\S+)")


def redact(value):
    return SECRET.sub("[REDACTED]", str(value))


class JsonFormatter(logging.Formatter):
    def format(self, record):
        fields = getattr(record, "context", {})
        return json.dumps(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": record.levelname,
                **fields,
                "message": redact(record.getMessage()),
            },
            default=str,
        )


def logger(file, context, level="INFO"):
    log = logging.getLogger("platform." + context["pipeline_run_id"])
    log.setLevel(level)
    log.propagate = False
    if not log.handlers:
        handler = logging.FileHandler(file, encoding="utf-8")
        handler.setFormatter(JsonFormatter())
        log.addHandler(handler)
    return logging.LoggerAdapter(log, context)


def close_logger(log):
    for handler in list(log.logger.handlers):
        log.logger.removeHandler(handler)
        handler.close()
