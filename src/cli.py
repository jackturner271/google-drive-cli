#!/usr/bin/env python3

from argparse import ArgumentParser
import mimetypes
from errors import printHttpError, NotFolderError
from re import sub
import google_auth
from api import API
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from os.path import isfile, join, basename, normpath
import magic

SCOPES = ['https://www.googleapis.com/auth/drive']
CLIENT_SECRET_FILE = "credentials.json"

credentials = google_auth.Auth(CLIENT_SECRET_FILE, SCOPES).get_credentials()

drive_service = build('drive', 'v3', credentials=credentials)

cli = ArgumentParser()
subparsers = cli.add_subparsers(dest="subcommand")

def printResults(items):
    if not items:
        print('No files found.')
        return
    for item in items:
        printItem(item)
        print("-------------------------------")    
        
def printItem(item):
    print(f"Name: {item['name']}")
    print(f"ID: {item['id']}")
    print(f"Parents: {item['parents']}")

def subcommand(args=[], parent=subparsers):
    def decorator(func):
        parser = parent.add_parser(func.__name__, description=func.__doc__)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(func=func)
    return decorator


def argument(*name_or_flags, **kwargs):
    return ([*name_or_flags], kwargs)

@subcommand([argument("fileId", help="The ID of the file", action="store"),
             argument("--raw", help="Flag to print the raw data.", action="store_true")])
def get(args):
    """Get a files metadata."""
    try:
        api = API(drive_service)
        file = api.getFile(args.fileId)
        if args.raw:
            print(file)
        else:
            print(f"Name: {file['name']}")
            print(f"ID: {file['id']}")
            print(f"Mime: {file['mimeType']}")
            print(f"Trashed: {file['trashed']}")
            if file['parents'] != None:
                parent = api.getParent(file['parents'][0]) 
                print(f"Parent: '{parent['name']}' ({parent['id']})")
    except HttpError as error:
        printHttpError(error)
    except NotFolderError:
        print("The parent of this file isn't a folder...")


@subcommand([argument("fileId", help="The ID of the file", action="store")])
def permissions(args):
    try:
        api = API(drive_service)
        print(api.getFilePermissions(args.fileId))
    except HttpError as error:
        printHttpError(error)

@subcommand([argument("--excludeFolders", help="Excludes folders from the list", action="store_true"),
             argument("--trash", help="List all files in the trash", action="store_true"),
             argument("--folderId", help="Folder to search within", action="store")])
def list(args):
    """List files found in drive."""
    try:
        api = API(drive_service)
        results = api.listFiles(args.trash, args.excludeFolders, args.folderId)
        print(f"Number of files found: {len(results)}")
        print("-------------------------------")
        printResults(results)
    except HttpError as error:
        printHttpError(error)

@subcommand([argument("--excludeFolders", help="Includes folders from the count", action="store_true"),
             argument("--trash", help="Count files in the trash", action="store_true"),
             argument("--folderId", help="Folder to search within", action="store"),
             argument("--all", help="Override, count all files including trash and folders", action="store_true")])
def count(args):
    """Give a count of files in drive."""
    try:
        api = API(drive_service)
        if(args.all):
            results = api.listAllFiles()
        else:
            results = api.listFiles(args.trash, args.excludeFolders, args.folderId)
        print(f"Number of files found: {len(results)}")
    except HttpError as error:
        printHttpError(error)

@subcommand([argument("term", help="Term to search by", action="store"),
             argument(
                 "--trash", help="Search within the trash folder", action="store_true"),
             argument("--folderId", help="Specific folder id to search within", action="store"),
             argument("--match", help="Match the term completely", action="store_true")])
def search(args):
    """Search for files with names that contain the search term."""
    try:
        print(f"Attempting search for files named: {args.term}...")
        api = API(drive_service)
        results = api.searchFile(args.term, args.trash, args.folderId, args.match)
        printResults(results)
    except HttpError as error:
        printHttpError(error)


@subcommand([argument("name", help="Name of the new folder", action="store"),
             argument("--folderId", help="ID of the parent folder, default is root", action="store")])
def folder(args):
    """Create a new folder."""
    try:
        api = API(drive_service)
        id = api.createFolder(args.name, args.folderId)
        print(f"Folder ID: {id}")
    except HttpError as error:
        printHttpError(error)


@subcommand([argument("name", help="The name given to the uploaded file", action="store"),
             argument("filePath", help="Path to the source file",
                      action="store"),
             argument(
                 "--mimetype", help="Force a file type such as 'image/jpeg'", action="store"),
             argument("--folderId", help="Folder ID to upload to, default root", action="store", default='root')])
def upload(args):
    """Upload a new file."""
    try:
        if(args.mimetype == None):
            mimemagic = magic.Magic(mime=True)
            mime = mimemagic.from_file(args.filePath) #Get the files mimetype
        else:
            mime = args.mimetype
        api = API(drive_service)
        print("Attempting upload...")
        id = api.uploadFile(args.name, args.filePath, mime, args.folderId)
        print(f"ID: {id}")
    except HttpError as error:
        printHttpError(error)
    
@subcommand([argument("fileId", help="The ID of the file to update", action="store"),
             argument("name", help="The name given to the uploaded file", action="store"),
             argument("filePath", help="Path to the source file",
                      action="store"),
             argument(
                 "--mimetype", help="Force a file type such as 'image/jpeg'", action="store")])
def update(args):
    """Update an existing file,"""
    try:
        if(args.mimetype == None):
            mimemagic = magic.Magic(mime=True)
            mime = mimemagic.from_file(args.filePath) #Get the files mimetype
        else:
            mime = args.mimetype
        api = API(drive_service)
        id = api.updateFile(args.fileId, args.name, args.filePath, mime)
        print(f"Updated file {id} Successfully.")
    except HttpError as error:
        printHttpError(error)


@subcommand([argument("fileId", help="The id of the file to be downloaded.", action="store")])
def download(args):
    """Download a file."""
    try:
        api = API(drive_service)
        print("Attempting download...")
        api.downloadFile(args.fileId)
        print("File Downloaded Successfully.")
    except HttpError as error:
        printHttpError(error)
        
@subcommand([argument("fileId", help="The id of the file to be exported.", action="store")])
def export(args):
    """Export a Google Workspaces file to PDF."""
    try:
        api = API(drive_service)
        print("Attempting export and download...")
        api.exportFile(args.fileId)
        print("File Exported Successfully.")
    except HttpError as error:
        printHttpError(error)

@subcommand([argument("fileId",help="ID of the file to move.", action="store"),
             argument("folderId",help="ID of the folder to move the file to.", action="store")])
def move(args):
    """Move a file into another folder."""
    try:
        api = API(drive_service)
        api.moveFiles(args.fileId, args.folderId)
        print("File Moved Successfully.")
    except HttpError as error:
        printHttpError(error)
    
@subcommand([argument("fileId",help="The ID of the file to create a shortcut to", action="store"),
             argument("--folderId",help="The ID of the shortcut's parent folder",action="store")])    
def shortcut(args):
    """Create a shortcut for a file."""
    try:
        api = API(drive_service)
        id = api.addShortcut(args.fileId, args.folderId)
        print(f"Shortcut ID: {id}")
    except HttpError as error:
        printHttpError(error)
        
@subcommand()
def empty_trash(args):
    """Permanently delete all files marked as trash."""
    try:
        api = API(drive_service)
        api.emptyTrash()
        print("Trash emptied.")
    except HttpError as error:
        printHttpError(error)
        
@subcommand([argument("folderPath", help="The folder to upload", action="store"),
             argument("--folderId",help="The parent folder ID to store the uploaded files/folders", action="store", default="root"),
             argument("--depth", help="Maximum depth to traverse", action="store", type=int)])
def upload_folder(args):
    """Upload a local folders contents."""
    def traverse(api, path, root, depth, maxdepth):
        print(f"Creating {path} folder...")
        id = api.createFolder(basename(normpath(path)), root)
        
        if(maxdepth == None or depth < maxdepth): #If max depth is reached, do not upload anything or create new folders
            print(depth)
            print(maxdepth)
            items = os.listdir(path)
            
            for item in items:
                itempath = join(path, item)
                if isfile(itempath):
                    mimemagic = magic.Magic(mime=True)
                    mime = mimemagic.from_file(itempath) #Get the files mimetype
                    print(f"Attempting upload of {itempath}...")
                    api.uploadFile(item, itempath, mime, id)
                else:
                    traverse(api, itempath, id, depth + 1, maxdepth)
    
    try:
        api = API(drive_service)
        traverse(api, args.folderPath, args.folderId, 0, args.depth)
        print("Finished Uploading Folder")
    except HttpError as error:
        printHttpError(error)
    
@subcommand([argument("fileId",help="File ID to lock",action="store")])
def lock(args):
    """Lock a file to read-only."""
    try:
        api = API(drive_service)
        print("Attempting to lock file...")
        api.lockFile(args.fileId)
        print("File Locked Successfully.")
    except HttpError as error:
        printHttpError(error)
        
@subcommand([argument("fileId",help="File ID to unlock",action="store")])
def unlock(args):
    """Unlock a file."""
    try:
        api = API(drive_service)
        print("Attempting to unlock file...")
        api.unlockFile(args.fileId)
        print("File Unlocked Successfully.")
    except HttpError as error:
        printHttpError(error)

@subcommand([argument("fileId", help="File ID to trash",action="store")])
def trash(args):
    """Mark a file as trash."""
    try: 
        api = API(drive_service)
        print("Attempting to mark file as trash...")
        api.trashFile(args.fileId)
        print("File Trashed Successfully.")
    except HttpError as error:
        printHttpError(error)

@subcommand([argument("fileId", help="File ID to trash",action="store")])
def restore(args):
    """Restore a file from trash."""
    try:
        api = API(drive_service)
        print("Attempting to restore a file...")
        api.untrashFile(args.fileId)
        print("File Restored Successfully.")
    except HttpError as error:
        printHttpError(error)

if __name__ == "__main__":
    args = cli.parse_args()
    if args.subcommand is None:
        cli.print_help()
    else:
        args.func(args)

