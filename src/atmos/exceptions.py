class AtmosError(Exception):
    """Base exception for Atmos."""

    pass


class AtmosAPIError(AtmosError):
    """API Error with status code and clean message."""

    def __init__(self, status_code: int, message: str, raw_response: str = ""):
        self.status_code = status_code
        self.message = message
        self.raw_response = raw_response
        super().__init__(f"API Error ({status_code}): {message}")
