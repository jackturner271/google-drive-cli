from __future__ import print_function

import io
import shutil

from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload


class API:

    def __init__(self, service):
        self.service = service

    def listFiles(self, trash=False, excludeFolders=False, folderId='root'):
        query = f"trashed = {trash}"
        if(excludeFolders):
            query += " AND mimeType != 'application/vnd.google-apps.folder'"
        if(folderId != None):
            query += f' AND "{folderId}" in parents'

        results = self.service.files().list(
            q=query, fields="files(id, name, parents)").execute()
        return results.get('files', [])

    def listAllFiles(self):  
        results = self.service.files().list(fields="files(id, name, parents)").execute()
        return results.get('files',[])

    def searchFile(self, name, trash=False, folder=None):
        query = f"name contains '{name}'"
        if(folder):
            query += f" AND '{folder}' in parents"
        if(trash == False):
            query += f" AND trashed = False"
        results = self.service.files().list(
            q=query, fields="nextPageToken, files(id, name, parents)").execute()
        items = results.get('files', [])
        return items

    def createFolder(self, name, folder_id='root'):
        if(folder_id == None):
            folder_id = self.service.files().get(fileId='root').execute()
        file_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [folder_id]
        }
        file = self.service.files().create(body=file_metadata, fields='id').execute()
        print('Folder ID: %s' % file.get('id'))

    def uploadFile(self, folder_id, file_name, file_path, mime_type):
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }

        media = MediaFileUpload(
            file_path, mimetype=mime_type, resumable=True)
        file = self.service.files().create(body=file_metadata,
                                           media_body=media,
                                           fields='id').execute()
        print('File ID: %s' % file.get('id'))

    def downloadFile(self, file_id):
        file = self.service.files().get(fileId=file_id).execute()
        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print("Download %d%%." % int(status.progress() * 100))

        fh.seek(0)
        with open(file.get('name'), 'wb') as f:
            shutil.copyfileobj(fh, f, length=10000)

    def moveFiles(self, file_id, folder_id):
        file = self.service.files().get(fileId=file_id, fields='parents').execute()
        previous_parents = ",".join(file.get('parents'))

        file = self.service.files().update(fileId=file_id, addParents=folder_id,
                                           removeParents=previous_parents, fields='id, parents').execute()

    def addShortcut(self, file_id, folder_id='root'):
        file = self.service.files().get(fileId=file_id).execute()
        shortcut_metadata = {
            'Name': 'Shortcut to %s' % file.get('name'),
            'mimeType': 'application/vnd.google-apps.shortcut',
            'parents': [folder_id],
            'shortcutDetails': {
                'targetId': file_id
            }
        }
        shortcut = self.service.files().create(body=shortcut_metadata,
                                               fields='id,shortcutDetails').execute()
        print('File ID: %s, Shortcut Target ID: %s, Shortcut Target MIME type: %s' % (
            shortcut.get('id'),
            shortcut.get('shortcutDetails').get('targetId'),
            shortcut.get('shortcutDetails').get('targetMimeType')))

    def emptyTrash(self):
        self.service.files().emptyTrash().execute()
