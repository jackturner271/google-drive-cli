from __future__ import print_function

import io
import shutil

from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload


class API:

    def __init__(self, service):
        self.service = service

    def listFiles(self, trash=False, excludeFolders=False, folder_id='root') -> list:
        """List all files in a folder

        Args:
            trash: A flag to list items marked as trash.
            excludeFolders: A flag to exclude folders from the list. 
            folder_id: The ID of the root folder to list from. If None is given, all files in the entire drive, including nested files, are given. (Default is root)

        Returns:
            A list of found files with their ID, Name and a list of Parents.

        Raises:
            HttpError: An error occured in the request. 
        """

        query = f"trashed = {trash}"
        if(excludeFolders):
            query += " AND mimeType != 'application/vnd.google-apps.folder'"
        if(folder_id != None):
            query += f' AND "{folder_id}" in parents'

        results = self.service.files().list(
            q=query, fields="files(id, name, parents)").execute()
        return results.get('files', [])

    def listAllFiles(self) -> list:
        """List all files in the entire drive, including nested items, folders and items marked as trash. 

        Returns:
            A list of found files with their ID, Name and a list of Parents.

        Raises:
            HttpError: An error occured in the request. 
        """

        results = self.service.files().list(fields="files(id, name, parents)").execute()
        return results.get('files', [])

    def searchFile(self, name, trash=False, folder_id=None, match=False) -> list:
        """Searches the drive for any files with names that contain the search term.

        Args:
            name: The term to search against. 
            trash: A flag to search items marked as trash. 
            folder_id: A folder ID to search within. If no value given, the entire drive is searched. 

        Returns:
            A list of found files with names that match the search term. Returned files include their ID, Name and a list of Parents.

        Raises:
            HttpError: An error occured in the request. 
        """

        if(match):
            query = f"name = '{name}'"
        else:
            query = f"name contains '{name}'"
        if(folder_id):
            query += f" AND '{folder_id}' in parents"
        query += f" AND trashed = {trash}"
        results = self.service.files().list(
            q=query, fields="nextPageToken, files(id, name, parents)").execute()
        items = results.get('files', [])
        return items

    def createFolder(self, name, folder_id='root') -> str:
        """Create a new folder. 

        Args:
            name: The name given to the folder.
            folder_id: The ID of the parent folder. By default, the new folder is created at the root. 

        Returns:
            The ID of the new folder. 

        Raises:
            HttpError: An error occured in the request. 
        """

        if(folder_id == None):
            folder_id = self.service.files().get(fileId='root').execute()
        file_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [folder_id]
        }
        file = self.service.files().create(body=file_metadata, fields='id').execute()
        return file.get('id')

    def uploadFile(self, name, file_path, mime_type, folder_id='root') -> str:
        """Upload a file to the drive. 

        Args:
            name: The name of the new file. This does not have to match the name of the local file but should match the extension. 
            file_path: The path of the file to be uploaded. 
            mime_type: The Mime Type of the file, eg. image/jpeg
            folder_id: The parent folder of the new file. Default is 'root'

        Returns:
            The ID of the new file.

        Raises:
            HttpError: An error occured in the request. 
        """

        file_metadata = {
            'name': name,
            'parents': [folder_id]
        }

        media = MediaFileUpload(
            file_path, mimetype=mime_type, resumable=True)
        file = self.service.files().create(body=file_metadata,
                                           media_body=media,
                                           fields='id').execute()
        return file.get('id')

    def downloadFile(self, file_id) -> None:
        """Download a file from the drive. 

        Args:
            file_id: The ID of the file to download. 

        Raises:
            HttpError: An error occured in the request.

        """
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

    def moveFiles(self, file_id, folder_id='root') -> None:
        """Move a file in the drive by changing the parent.  

        Args:
            file_id: The ID of the file to move. 
            folder_id: The ID of the new parent folder. Default is root.

        """
        file = self.service.files().get(fileId=file_id, fields='parents').execute()
        previous_parents = ",".join(file.get('parents'))

        file = self.service.files().update(fileId=file_id, addParents=folder_id,
                                           removeParents=previous_parents, fields='id, parents').execute()

    def addShortcut(self, file_id, folder_id=None):
        """Create a shortcut to a file.

        Args:
            file_id: The ID of the file to create a shortcut to.
            folder_id: The ID of the shortcuts parent folder. If no folder_id is provided, the shortcut will have the same parent as the original file. 

        Returns:
            The ID of the shortcut.

        Raises:
            HttpError: An error occured in the request.

        """
        file = self.service.files().get(file_id=file_id, fields="id, parents").execute()
        if(folder_id == None):
            folder_id = file.get('parents')[0]

        shortcut_metadata = {
            'Name': 'Shortcut to %s' % file.get('name'),
            'mimeType': 'application/vnd.google-apps.shortcut',
            'parents': [folder_id],
            'shortcutDetails': {
                'targetId': file_id
            }
        }
        shortcut = self.service.files().create(body=shortcut_metadata,
                                               fields='id').execute()
        return shortcut['id']

    def emptyTrash(self):
        """Permanently deletes all items marked as trash.

        Raises:
            HttpError: An error occured in the request.

        """
        self.service.files().emptyTrash().execute()

    def lockFile(self, file_id, reason="No reason given"):
        self.service.files().update(fileId=file_id, body={"contentRestrictions":
                                                          [{"readOnly": "true", "reason": reason}]}).execute()

    def unlockFile(self, file_id):
        self.service.files().update(fileId=file_id, body={"contentRestrictions":
                                                          [{"readOnly": "false"}]}).execute()
        
    def swapLock(self, file_id):
        file = self.getLockState(file_id)
        if 'contentRestrictions.readOnly' not in file:
            self.lockFile(file_id)
        else:
            if file['contentRestrictions'][0]['readOnly'] == 'True':
                #unlock
                print("unlocking")
                self.unlockFile(file_id)
            else:
                self.lockFile(file_id)
                #lock
                
    def getLockState(self, file_id):
        file = self.service.files().get(fileId = file_id, fields='id, contentRestrictions').execute()
        return file