import platform
import os
from gi.repository import GLib

class download_directory_manager(object):
    
    
    def __init__(info_dict):
                                                    # get the users downlaods directory
                                                    # edit the downloads dir for a test file downlaod
    self.downloads_dir = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD)
    os.path.join(downloads_dir, "testdownload")
    if not os.path.exists(downlaods_dir):
        os.makedirs(downloads_dir)
    
    self.files = get_files_from_info_dict(info_dict)# get the list of files and paths with the file length
    for z in files:                                 # for each file we need to create a place holder which can be opened later 
        length = z['length']
        name = z['name']
        path = z['path']
        createEmptyFile(self, length, path, name)
    
    
    
    def write_peice_to_file(self, piece):
        index = piece.piece_index * piece.piece_length             # calculate the index of the piece
        count = 0                                   # create a count variable to determine relative index of the file
        total_written_bytes = 0
        for f in self.files:                        # for each file check the length to determine if the piece belongs in that file
            length = f['length']
            name = f['name']
            path = f['path']
            count = count + length
            if count >= index:                      # we know the piece contains information for this file
                fout=open(name, wb)                 # open the file
                f.seek(index - (count - length))    # seek to the index relative to the file
                eof = length - (index - (count - length)) 
                                                    # calculates the length of writable area within this file
                h = 0
                while h<eof and (total_written_bytes + h) < piece.data_length:    
                                                    # while loop constraints:
                                                    # 1. If we reach the end of the file stop writing we need to move on to the next one
                                                    # 2. If we reach the end of the piece stop writing theres no more data dont go out of bounds
                                                    # fix to work with rosses code
                    f.write(piece.blocks[h])        # write the bytes one at a time POSSIBLY CHANGE TO BYTEARRAY for faster performance
					h++
                fout.close()                        # while conditions met = finished with this file
                total_written_bytes += h            # how many bytes did we write in total? this keeps track of the total number of bytes that need to be written         
                if total_written_bytes==piece.data_length: 
                                                    # we now know the piece is completely finished being written
                    break                           # we dont want to keep iterating through the files
                
            
    
                
    def create_empty_file(self, length, path, name):        
        filePath = os.path.join(self.downloads_dir, path)   
                                                    # path of the directory in which the file will exist
        fullPath = os.path.join(filePath, name)     # Full path including name of the file
        if not os.path.exists(filePath):
            os.makedirs(filePath)                   # create the directory if it doesn't exist
        fo = open(name, "wb")                       # open a new file to place peices into
        f.seek(length-1)                            # find last bit in the file
        f.write("\0")                               # add one empty bit at the end
        f.close()                                   # place holder created
                                                    #fin