from __future__ import annotations

import json
import logging
from dataclasses import asdict

from app.services.observability.rag_trace import RAGTrace

logger = logging.getLogger("intellex.rag")

def log_rag_trace(trace: RAGTrace)-> None:

    #One log event as One Rag Execution finsihes

    payload = {
        "event": "rag_execution",
        **asdict(trace) #Converts dataclasses to Py Dict
    }

    payload.pop("_started_at", None)

    logger.info(json.dumps(
        payload,
        default=str
    ))

    