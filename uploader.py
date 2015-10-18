import os
import sys
#import dropbox
import requests
import gzip
import shutil
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


def printFiles(startFile):
    for dirPath,dirNames,fileNames in os.walk(startFile):
        for x in fileNames:
            print(dirPath+"\\"+x)


'''
Traverses the specified directory and subdirectory using the os.walk method
the file names are all added to a list and then returned as a list.

The startFile is the root of the subtree in the directory structure that you
would like the method to start at.  The method will gather filenames and dir

The startFile parameter must be a directory.  If this is not a directory
the method will return None

see printFiles comments for a synopsis of the os.walk function or for more detail
go to python docs
'''
def getFileNames(startFile):
    if os.path.isdir(startFile):
        filenames=[]
        for dirPath,dirNames,fileNames in os.walk(startFile):
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
    code = input("Enter the authorization code here: ").strip()
    access_token, user_id = flow.finish(code)
    client = dropbox.client.DropboxClient(access_token)
    if client:
        print("Succesful Login")
        return client
    else:
        print("Login Failed")

'''
Uses the requests library to send a get request. This method
returns a connection object when the request is successful and
returns None when the function fails. A dictionary can be passed
as the data argument if you would like to send query information
with the get request. 
'''
def getRequest(url,data=None):
    try:
        req=requests.get(url,params=data)
        return req
    except:
        return None

'''

'''
def writeToFile(content,fileName):
    with open(fileName,'a') as out:                            
        out.write(content)
        return True
    return False



'''
Uses gzip to compress files. If dst is specified and exists
the zipped file will be moved to the specified location.

The dst file must be a tarfile.  If the designated file is not
a tarfile one will be created. 

fileNames needs to be a list of strings that correspond to file names


'''
def compress(fileNames,dst=None):
    tar=None
    count=0
    
    tar=tarfile.open(dst,"w",)
    for x in fileNames:
        if os.path.isfile(x):
            zippedName=x+".gz"
            try:
                with open(x,"rb") as file_in:
                    with gzip.open(zippedName,'wb') as file_out:
                        shutil.copyfileobj(file_in, file_out)
                        count+=1
                if dst!=None:
                    tar.add(zippedName)
            except:
                print("A problem occured while processing "+x)
    print(str(count)+" Files Compressed")



'''
The upload part of this needs to be added.
NEEDS TO BE TESTED more but works in a perfect case

This is going to be a sort of process and control method
for sending files to dropbox. 

'''
def collectAndUpload(startFile):
    fileNames=getFileNames(startFile)
    holderFile="holder_file"
    compress(fileNames,holderFile)


def main():
    
    collectAndUpload(os.getcwd())

main()
