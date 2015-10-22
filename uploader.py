from os import walk, remove,stat,getcwd
from os.path import isdir, isfile
import sys
import dropbox
from requests import get
import gzip
from shutil import copyfileobj
import tarfile


'''
Basic Design Idea

Command Line Options [path,drop]

Use os.walk(top, topdown=True, onerror=None, followlinks=False) to traverse dirs
top is a directory

this returns a tuple (dirpath, dirnames, filenames)
    dirpath is a string
    dirnames is a list of subdirectories
    filenames is a list of filenames

topdown is default to true
dont worry about onerror default is good
followlinks is refering to symlinks or shortcuts to other directories

Once I have the tuple I can upload the file to dropbox via
the API


DROPBOX NOTES and REFERENCES
for tutorial on authorization code go to
https://www.dropbox.com/developers-v1/core/start/python

Link for all python methods in the API
https://www.dropbox.com/developers-v1/core/docs/python#
'''



'''
Traverses the specified directory and subdirectories using the os.walk method
the file names are all added to a list and then returned as a list.

parameters:
startFile is the root of the subtree in the directory structure that you
would like the method to start at.  The method will gather filenames and dir
The startFile parameter must be a directory.

returns:
list if successful and If the startFile is not a directory
the method will return None
'''
def getFileNames(startFile):
    if isdir(startFile):
        filenames=[]
        for dirPath,dirNames,fileNames in walk(startFile):
            for x in fileNames:
                filenames.append(x)
        return filenames
    else:
        return None

'''
Problems:
I don't want to store my apiKey and appSecret in plain text because that is not secure
in anyway.

This methods purpose it to perform the OAuth2 process with drop box.  The
process is shamelessly copied from the Dropbox docs. Why reinvent the wheel right???

This method should, in the end, return a client object.  This will allow access to
the other dropbox methods. 
'''
def dropBoxAuth():
    #need to find a better way to do this
    apiKey=""
    appSecret=""

    #let dropbox know i'm legit
    flow=dropbox.client.DropboxOAuth2FlowNoRedirect(apiKey,appSecret)
    #Get the url to authorize users
    authorizationURL=flow.start()
    print ('1. Go to: ' + authorizationURL)
    print ('2. Click "Allow" (you might have to log in first)')
    print ('3. Copy the authorization code.')
    code = raw_input("Enter the authorization code here: ").strip()
    access_token, user_id = flow.finish(code)
    client = dropbox.client.DropboxClient(access_token)
    if client:
        print("Succesful Login")
        return client
    else:
        print("Login Failed")


'''
Uses gzip to compress files. If dst is specified and exists
the zipped file will be moved to the specified location.

The dst file must be a tarfile.  If the designated file is not
a tarfile one will be created. 

fileNames needs to be a list of strings that correspond to file names
'''
def compressAddToTar(fileNames,dst=None):
    tar=None
    count=0
    tar=tarfile.open(dst,"w",)
    for x in fileNames:
        if isfile(x):
            zippedName=x+".gz"
            try:
                with open(x,"rb") as file_in:
                    with gzip.open(zippedName,'wb') as file_out:
                        copyfileobj(file_in, file_out)
                        count+=1
                if dst!=None:
                    tar.add(zippedName)
                    remove(zippedName)
            except Exception as e:
                print(e.message, e.args)
                print("A problem occured while processing "+x)
    tar.close()
    print(str(count)+" Files Compressed")
    return tar.name


'''
Since gzip doesn't take directories or folders this method exists
to compress the tar file created by compressAddToTar() to a gzip file
so that the chucked_uploader() method will upload it to dropbox.

Parameters;
fileName: String representation of a file

returns:
No return val

Exception:
Prints a message
'''
def compress(fileName):
    zippedName=fileName+".gz"
    try:
        with open(fileName,"rb") as file_in:
            with gzip.open(zippedName,'wb') as file_out:
                copyfileobj(file_in, file_out)
                count+=1
    except:
        print("A problem occured while processing "+fileName)

    
'''
This is supposed to upload files that are in excess of 150mb limit
that Dropbox has placed on the dropbox.put_file() method.  The upload_chunked()
only takes gzip files.. So Files must be run through the compress() method before
they are sent here. 


Parameters:
    file:
        must be a file object or path in the form of a string.
local Vars:
    size is the size of the file in bytes
    uploadAttempts is the number of upload attempts for the current chunk
    uploader is the uploader object
    uploadDetails is the data returned by get_chunked_uploader
    filePath is a string representation of the filePath

Returns:
    True if the process succeeded else false


NEEDS TESTING
'''
def uploadBigFile(file,client):
    size=getFileSize(file)
    uploadAttempts=1
    uploader=None
    uploadDetails=None
    filePath=""    
    if type(file) is str:
        filePath=file
        file=open(filePath,"rw")
    else:
        filePath=file.name
    try:
        uploader=client.get_chunked_uploader(file,size)
    except:
        print("Unable to open file")

    while uploader.offset<size and uploadAttempts<5:
        try:
            uploadDetails=uploader.upload_chunked()
            uploadAttempts=1
        except:
            uploadAttempts+=1
            uploadDetails=uploader.upload_chunked()
    uploader.finish(filePath)
    return uploadDetails

'''
This is used in the uploadBigFile() method to make let the uploader
how big the file to be uploaded is 
parameters:
a file path as a string or a file object

return:
the size of the file in bytes or -1 if the operation fails 

'''
def getFileSize(file):
    try:
        return stat(file).st_size
    except:
        try:
            return stat(file.name).st_size
        except:
            return -1


'''
The upload part of this needs to be added.
NEEDS TO BE TESTED more but works in a perfect case

This is going to be a sort of process and control method
for sending files to dropbox. 

'''
def collectAndUpload(startFile,client):
    fileNames=getFileNames(startFile)
    if len(fileNames)>0:
        holderFile="holder_file"
        holderFile=compressAddToTar(fileNames,holderFile)
        if holderFile!=None:
            compress(holderFile)
            uploadBigFile(holderFile,client)
    else:
        print("No files in specified directory")

    #dont forget to remove the tar file with os.remove("holder_file")


def main():
    client=dropBoxAuth()
    collectAndUpload(getcwd(),client)

main()
