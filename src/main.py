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
    api.searchFile('photo.jpg', folder='root')


except HttpError as error:
    print(f'An error occurred: {error}')