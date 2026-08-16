import pytest

from app.services.extraction.base_extractor import (
    BaseExtractor,
)

from app.services.extraction.extraction_factory import (
    ExtractorFactory,
    UnsupportedExtractorError,
)

from app.services.extraction.pdf.pdf_extractor import (
    PdfExtractor,
)

from app.services.extraction.docx_extractor import (
    DocxExtractor,
)

from app.services.extraction.markdown_extractor import (
    MarkdownExtractor,
)

from app.services.extraction.txt_extractor import (
    TxtExtractor,
)


# ============================================================================
# FIXTURE
# ============================================================================

@pytest.fixture
def factory() -> ExtractorFactory:
    return ExtractorFactory()


# ============================================================================
# PDF
# ============================================================================

def test_pdf_mime_returns_pdf_extractor(
    factory: ExtractorFactory,
):

    extractor = factory.get_extractor(
        "application/pdf"
    )

    assert isinstance(
        extractor,
        PdfExtractor,
    )

    assert isinstance(
        extractor,
        BaseExtractor,
    )


# ============================================================================
# DOCX
# ============================================================================

def test_docx_mime_returns_docx_extractor(
    factory: ExtractorFactory,
):

    extractor = factory.get_extractor(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    assert isinstance(
        extractor,
        DocxExtractor,
    )

    assert isinstance(
        extractor,
        BaseExtractor,
    )


# ============================================================================
# MARKDOWN
# ============================================================================

def test_markdown_mime_returns_markdown_extractor(
    factory: ExtractorFactory,
):

    extractor = factory.get_extractor(
        "text/markdown"
    )

    assert isinstance(
        extractor,
        MarkdownExtractor,
    )

    assert isinstance(
        extractor,
        BaseExtractor,
    )


# ============================================================================
# TXT
# ============================================================================

def test_txt_mime_returns_txt_extractor(
    factory: ExtractorFactory,
):

    extractor = factory.get_extractor(
        "text/plain"
    )

    assert isinstance(
        extractor,
        TxtExtractor,
    )

    assert isinstance(
        extractor,
        BaseExtractor,
    )


# ============================================================================
# CASE NORMALIZATION
# ============================================================================

def test_mime_type_is_normalized(
    factory: ExtractorFactory,
):

    extractor = factory.get_extractor(
        "  TEXT/PLAIN  "
    )

    assert isinstance(
        extractor,
        TxtExtractor,
    )


# ============================================================================
# NEW INSTANCE
# ============================================================================

def test_factory_returns_new_instance_each_time(
    factory: ExtractorFactory,
):

    first = factory.get_extractor(
        "text/plain"
    )

    second = factory.get_extractor(
        "text/plain"
    )

    assert isinstance(
        first,
        TxtExtractor,
    )

    assert isinstance(
        second,
        TxtExtractor,
    )

    assert first is not second


# ============================================================================
# UNSUPPORTED TYPE
# ============================================================================

def test_unsupported_mime_type_raises(
    factory: ExtractorFactory,
):

    with pytest.raises(
        UnsupportedExtractorError,
        match="No extractor registered",
    ):
        factory.get_extractor(
            "application/zip"
        )


# ============================================================================
# EMPTY MIME
# ============================================================================

def test_empty_mime_type_raises(
    factory: ExtractorFactory,
):

    with pytest.raises(
        UnsupportedExtractorError,
        match="No extractor registered",
    ):
        factory.get_extractor(
            ""
        )


# ============================================================================
# WHITESPACE MIME
# ============================================================================

def test_whitespace_mime_type_raises(
    factory: ExtractorFactory,
):

    with pytest.raises(
        UnsupportedExtractorError,
        match="No extractor registered",
    ):
        factory.get_extractor(
            "   "
        )


# ============================================================================
# NONE
# ============================================================================

def test_none_mime_type_raises_type_error(
    factory: ExtractorFactory,
):

    with pytest.raises(
        TypeError,
        match="mime_type must be a string",
    ):
        factory.get_extractor(
            None
        )


# ============================================================================
# SUPPORTED MIME TYPES
# ============================================================================

def test_supported_mime_types(
    factory: ExtractorFactory,
):

    supported = (
        factory.supported_mime_types()
    )

    assert supported == {
        "application/pdf",
        (
            "application/"
            "vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
        "text/markdown",
        "text/plain",
    }


# ============================================================================
# SUPPORTS
# ============================================================================

@pytest.mark.parametrize(
    "mime_type",
    [
        "application/pdf",
        (
            "application/"
            "vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),
        "text/markdown",
        "text/plain",
    ],
)
def test_supports_known_mime_types(
    mime_type: str,
):

    assert (
        ExtractorFactory.supports(
            mime_type
        )
        is True
    )


@pytest.mark.parametrize(
    "mime_type",
    [
        "application/zip",
        "application/msword",
        "text/html",
        "image/png",
        "",
    ],
)
def test_supports_unknown_mime_types(
    mime_type: str,
):

    assert (
        ExtractorFactory.supports(
            mime_type
        )
        is False
    )


# ============================================================================
# SUPPORTS IS SAFE FOR INVALID INPUT
# ============================================================================

def test_supports_none_returns_false():

    assert (
        ExtractorFactory.supports(
            None
        )
        is False
    )