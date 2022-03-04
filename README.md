# google-drive-cli
A WIP Command Line Tool for interacting with the Google Drive API. I worked on this project during the non-sprint work week for Team Robin at Meltwater (28/02/22 to 04/03/22). I chose this project as practise for working with Python, interacting with an API library and learning about Google's OAuth and backend. 

In future, I would like to make this tool far more robust, adding input validation etc. Adding more functionality surrounding permissions and sharing is something I would also like to add. This is intended entirely to be a fun side-project, I have no intentions right now to take it further.

This project requires a Google Cloud Platform Project and OAuth credentials. Please see the Google Drive API quickstart guide here for more information: https://developers.google.com/docs/api/quickstart/python

Credit to the Google Drive API documentation for the client library implementation and authorisation implementation used in this project. 

Credit also to https://mike.depalatis.net/blog/simplifying-argparse.html for information on how to create the CLI. 

To access the tool, download the `src` folder and run `./cli.py` in a Linux terminal. 

## Current Supported Functions
 - `get` - Get a files metadata. 
   - `fileId` - The ID of the file to get metadata on.
   - `--raw`  - Return all of the available metadata as JSON.

-`permissions` - Get the permission metadata of a file. 
  - `fileId` - The ID of the file to get metadata on.

- `list` - List all files within either a specific folder or the entire drive. By default, all files/folders not marked as trash are listed. 
  - `--excludeFolders` - Flag to exclude folders from the list since Google Drive considers these as files in their own right. 
  - `--trash` - Flag to list all items marked as trash. 
  - `--folderId` - Folder to search for items in. Files in nested folders are not included in the list. 
  - `--all` -  Override flag to list all items in the drive, including trash and folders. 

- `count` - Give a count of all files in a folder or the entire drive. By default, all files/folders not marked as trash are counted. 
  - `--excludeFolders` - Flag to exclude folders from the count since Google Drive considers these as files in their own right. 
  - `--trash` - Flag to count all items marked as trash. 
  - `--folderId` - Folder to search for items in. Files in nested folders are not included in the count. 
  - `--all` -  Override flag to count all items in the drive, including trash and folders. 

- `search` - Search the drive for all files with names containing the search term. 
  - `term` - The term used to search. 
  - `--trash` - Flag to search only items marked as trash. 
  - `--folderId` - Folder ID to search within. 
  - `--match` - Only return results which perfectly match the search term. 

- `folder` - Create a new folder.
  - `name` - The name of the folder.
  - `--folderId` - The ID of the folder that the new folder should be created in. By default, a new folder is created at the root folder. 
    
- `upload` - Upload a local file to the drive. 
  - `name` - The name of the new file in the Drive.
  - `filePath` - The path to the local file to be uploaded.
  - `--mimetype` - The mimeType of the new file in the Drive. By default, the mimeType is fetched from the local file if possible, this acts as an override. 
  - `--folderId` - The ID of the folder that the new file should be stored in. By default, a new file will be stored in the root folder. 

- `update` - Update an existing file stored in Google Drive with the contents of a local file. The contents of the existing Google Drive file will be lost, the content will not be merged but replaced. 
  - `fileId` - The ID of the file to update. 
  - `name` - The name of the file to be updated.
  - `filePath` - The path to the local file, the contents of which will be uploaded into the existing file.  
  - `--mimetype` - The mimeType of the existing file, in case it needs altering to suit the new content. 

- `download` - Download a file from Google Drive and save a local copy. 
  - `fileId` - The ID of the file to download.

- `export` - Export a Google Workspace document to PDF then download and save a local copy. Non Google Workspace files cannot be exported. 
  - `fileId` - The ID of the file to export.

- `move` - Move a file from one folder to another. 
  - `fileId` - The ID of the file to move. 
  - `folderID` - The ID of the new parent folder. 

- `copy` - Copy a file. Folders cannot be copied. 
  - `fileId` - The ID of the file to copy. 
  - `--folderId` - ID of the folder to move the copy into. By default, the copy is stored in the same folder as the original.
  - `--name` - New name of the copy. By default, the name remains the same. 

- `shortcut` - Create a shortcut to a file. 
  - `fileId` - The ID of the file to create a shortcut to. 
  - `--folderId` - The ID of the folder to store the new shortcut in. By default, the new shortcut is stored in the same folder as the target file. 

- `empty_trash` - Delete all files marked as trash. 

- `upload_folder` - Upload all files and folders from a specified local path. 
  - `folderPath` - Path to the local folder.
  - `--folderId` - The ID of the folder to store the uploaded files and folders to. 
  - `--depth` - The depth to recursively search for folders and files to upload. For example, a depth of 1 would create the root folder and upload and create all files and folders inside it. Any files in nested folders are not uploaded.

- `lock` - Lock a file as read-only. 
  - `fileId` - The ID of the file to lock.

- `unlock` - Unlock a file from being read-only. 
  - `fileId` - The ID of the file to unlock.  

- `trash` - Mark a file as trash.
  - `fileId` - The ID of the file to trash.
    
- `restore` - Restore a file from the trash. 
  - `fileId` - The ID of the file to restore. 

Included with this project is `api.py` which can be used to integrate into other projects to use Google Drive rather than through the command line. 
