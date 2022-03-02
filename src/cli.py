#!/usr/bin/env python3

from argparse import ArgumentParser
import mimetypes
from errors import printHttpError, ArgumentError, MimeError, NotFoundError
from re import sub
import google_auth
import api_interaction
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
            mimemagic = magic.Magic(mime=True)
            mime = mimemagic.from_file(args.filePath) #Get the files mimetype
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
        
@subcommand([argument("fileId", help="The id of the file to be exported.", action="store")])
def export(args):
    try:
        api = api_interaction.API(drive_service)
        print("Attempting export and download...")
        api.exportFile(args.fileId)
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
        
@subcommand([argument("folderPath", help="The folder to upload", action="store"),
             argument("--folderId",help="The parent folder ID to store the uploaded files/folders", action="store", default="root"),
             argument("--depth", help="Maximum depth to traverse", action="store", type=int)])
def uploadfolder(args):
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
        api = api_interaction.API(drive_service)
        traverse(api, args.folderPath, args.folderId, 0, args.depth)
    except HttpError as error:
        printHttpError(error)
    
@subcommand([argument("fileId",help="File ID to lock",action="store")])
def lock(args):
    try:
        api = api_interaction.API(drive_service)
        print("Attempting to lock file...")
        api.lockFile(args.fileId)
    except HttpError as error:
        printHttpError(error)
        
@subcommand([argument("fileId",help="File ID to unlock",action="store")])
def unlock(args):
    try:
        api = api_interaction.API(drive_service)
        print("Attempting to unlock file...")
        api.unlockFile(args.fileId)
    except HttpError as error:
        printHttpError(error)

    
if __name__ == "__main__":
    args = cli.parse_args()
    if args.subcommand is None:
        cli.print_help()
    else:
        args.func(args)

