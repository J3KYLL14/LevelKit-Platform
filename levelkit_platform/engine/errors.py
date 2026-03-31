class PlainEnglishError(Exception):
    """A content or setup error phrased for students and teachers."""


def format_syntax_error(err):
    filename = err.filename or "unknown file"
    line = err.lineno or "unknown line"
    detail = err.msg or "Python syntax error"
    return PlainEnglishError(
        f"There is a Python syntax error in {filename} on line {line}.\n"
        f"Plain English: Python could not understand that line.\n"
        f"Check for a missing comma, bracket, quote, or colon.\n"
        f"Technical detail: {detail}"
    )
