import fitz
from pathlib import Path
from app.exceptions.document_exceptions import DocumentExtractionError,UnsupportedDocumentTypeError,EmptyDocumentError
from app.models.documents import Document
from docx import Document as DocxDocument

def _extract_pdf(file_path:str)->str:
    try:
        with fitz.open(file_path) as pdf:
            return "\n".join(  # joins txt from all pages into one string
                 page.get_text() #Extract all txt from pgs
                 for page in pdf #Moves one pg at a time 
            )
    except Exception as e :
        raise DocumentExtractionError(
            f"Failed to extract PDF: {e}"
        ) from e

def _extract_docx(file_path:str)->str:
    try:
        doc=DocxDocument(file_path) #Load the Word file
        return "\n".join(  #gets all valid sentence nd joins into single txt
            paragraph.text
            for paragraph in doc.paragraphs
            if paragraph.text.strip() #strip removes all blank spaces 
        )
    except Exception as e:
        raise DocumentExtractionError(
            f"Failed to extract DOCX: {e}"
        ) from e

def _extract_text_file(file_path:str)->str:
    try:
        with open(file_path,"r",encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        raise DocumentExtractionError(
            f"Failed to read text file {e}"
        ) from e

def extract_text(document:Document)->str:

    extension=Path(document.file_path).suffix.lower()

    if extension == "pdf":
        text = _extract_pdf(document.file_path)
        
    elif extension == "docx":
        text = _extract_docx(document.file_path)

    elif extension == {"txt","md"}:
        text = _extract_text_file(document.file_path)

    else:
        raise UnsupportedDocumentTypeError(
            f"Unsupported document type: {extension}"
        )
    if not text.strip:
        raise EmptyDocumentError("Document contains no extractable text.")

    return text


