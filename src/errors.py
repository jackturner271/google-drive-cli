class NotFolderError(Exception):
    """Raised when the fetched file is not a folder"""
    pass

def printHttpError(error):
    print(
        f"Error Occured:\nStatus: {error.status_code}\nReason: {error._get_reason}")