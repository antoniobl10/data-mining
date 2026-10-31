"""JSON logging shared by ingestion, transformation and orchestration."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import logging
from contextvars import ContextVar

LOG = logging.getLogger('banking')
CONTEXT = ContextVar('banking_log_context', default={})


def event(status, stage, level=logging.INFO, **fields):
    LOG.log(level, json.dumps({'timestamp': datetime.now(timezone.utc).isoformat(), 'level': logging.getLevelName(level), **CONTEXT.get(), 'component': stage, 'stage': stage, 'status': status, **fields}, default=str, ensure_ascii=False))


@contextmanager
def run_context(**fields):
    token=CONTEXT.set(fields)
    try:
        yield
    finally:
        CONTEXT.reset(token)


@contextmanager
def file_logging(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(path, encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(message)s'))
    previous_level = LOG.level
    LOG.setLevel(logging.INFO)
    LOG.addHandler(handler)
    try:
        yield
    finally:
        LOG.removeHandler(handler)
        LOG.setLevel(previous_level)
        handler.close()
