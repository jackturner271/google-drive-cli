class NotFoundError(Exception):
    """Raised when no search results are found"""
    pass


class ArgumentError(Exception):
    """Raised when there are errors in cli arguments that aren't handled by argparse"""
    pass


class MimeError(Exception):
    """Raised when the file extension cannot be guessed"""
    pass


def printHttpError(error):
    print(
        f"Error Occured:\nStatus: {error.status_code}\nReason: {error._get_reason}")