from app.services.observability.rag_trace import RAGTrace


def test_trace_finish_records_latency():

    trace = RAGTrace(
        request_id="test-request",
    )

    trace.finish(
        status="SUCCESS"
    )

    assert trace.status == "SUCCESS"
    assert trace.total_latency_ms >= 0


def test_trace_defaults():

    trace = RAGTrace()

    assert trace.vector_candidates == 0
    assert trace.reranked_chunks == 0
    assert trace.source_document_ids == []
    assert trace.status == "RUNNING"