#!/usr/bin/env python3

from argparse import ArgumentParser
import mimetypes
from errors import printHttpError, ArgumentError, MimeError, NotFoundError
from re import sub
import google_auth
import api_interaction
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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
        
def printItem(item):
    print(f"Name: {item['name']}")
    print(f"ID: {item['id']}")
    print(f"Parents: {item['parents']}")
    print("-------------------------------")

def subcommand(args=[], parent=subparsers):
    def decorator(func):
        parser = parent.add_parser(func.__name__, description=func.__doc__)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(func=func)
    return decorator


def argument(*name_or_flags, **kwargs):
    return ([*name_or_flags], kwargs)


@subcommand([argument("--excludeFolders", help="Excludes folders from the list", action="store_true"),
             argument("--trash", help="List all files in the trash", action="store_true"),
             argument("--folderId", help="Folder to search within", action="store")])
def list(args):
    try:
        api = api_interaction.API(drive_service)
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
    try:
        api = api_interaction.API(drive_service)
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
    try:
        print(f"Attempting search for files named: {args.term}...")
        api = api_interaction.API(drive_service)
        results = api.searchFile(args.term, args.trash, args.folderId, args.match)
        printResults(results)
    except HttpError as error:
        printHttpError(error)


@subcommand([argument("name", help="Name of the new folder", action="store"),
             argument("--folderId", help="ID of the parent folder, default is root", action="store")])
def folder(args):
    try:
        api = api_interaction.API(drive_service)
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
    try:
        if(args.mimetype == None):
            # Try and guess the extension
            print("Attempting to guess the mimetype...")
            mime = mimetypes.guess_extension(args.filePath)
            if(mime == None):
                # If it cannot be guessed then raise error
                raise MimeError
        else:
            mime = args.mimetype
        api = api_interaction.API(drive_service)
        print("Attempting upload...")
        id = api.uploadFile(args.name, args.filePath, mime, args.folderId)
        print(f"ID: {id}")
    except HttpError as error:
        printHttpError(error)
    except MimeError:
        print("Could not detect the mime type from the local file, try manually forcing the type, if known, with --mimetype")


@subcommand([argument("fileId", help="The id of the file to be downloaded.", action="store")])
def download(args):
    try:
        api = api_interaction.API(drive_service)
        print("Attempting download...")
        api.downloadFile(args.fileId)
    except HttpError as error:
        printHttpError(error)

@subcommand([argument("fileId",help="ID of the file to move.", action="store"),
             argument("folderId",help="ID of the folder to move the file to.", action="store")])
def move(args):
    try:
        api = api_interaction.API(drive_service)
        api.moveFiles(args.fileId, args.folderId)
        print("File Moved.")
    except HttpError as error:
        printHttpError(error)
    
@subcommand([argument("fileId",help="The ID of the file to create a shortcut to", action="store"),
             argument("--folderId",help="The ID of the shortcut's parent folder",action="store")])    
def shortcut(args):
    try:
        api = api_interaction.API(drive_service)
        id = api.addShortcut(args.fileId, args.folderId)
        print(f"Shortcut ID: {id}")
    except HttpError as error:
        printHttpError(error)
        
@subcommand()
def trash(args):
    try:
        api = api_interaction.API(drive_service)
        api.emptyTrash()
        print("Trash emptied.")
    except HttpError as error:
        printHttpError(error)
        
if __name__ == "__main__":
    args = cli.parse_args()
    if args.subcommand is None:
        cli.print_help()
    else:
        args.func(args)

