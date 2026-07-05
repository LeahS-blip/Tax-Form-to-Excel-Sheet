"""tax_extractor — pull structured data from W-2 and 1040 PDFs into Excel."""
from .pipeline import process_file, process_forms, process_path
from .writer import write_workbook, FileResult
from .schemas import SCHEMAS, detect_form_type

__all__ = [
    "process_file", "process_forms", "process_path", "write_workbook",
    "FileResult", "SCHEMAS", "detect_form_type",
]
__version__ = "0.1.0"
