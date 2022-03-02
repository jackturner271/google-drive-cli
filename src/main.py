import google_auth
import api_interaction
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive']
CLIENT_SECRET_FILE = "credentials.json"

credentials = google_auth.Auth(CLIENT_SECRET_FILE, SCOPES).get_credentials()

drive_service = build('drive', 'v3', credentials=credentials)

try:
    api = api_interaction.API(drive_service)
    api.swapLock('13I4Sty4wxQimVA5-_iHQbOSs9FIXlhrt10YB0YKWBJo')
    result = api.getLockState('13I4Sty4wxQimVA5-_iHQbOSs9FIXlhrt10YB0YKWBJo')
    #print(result['contentRestrictions'][0]['readOnly'])
    print(result)


except HttpError as error:
    print(f'An error occurred: {error}')