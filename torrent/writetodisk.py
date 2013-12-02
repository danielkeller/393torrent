import platform
import os

class FilesystemManager(object):
    def __init__(self, fileinfo):
        self.fileinfo = fileinfo
        self.downloads_dir = os.getcwd()
        self.downloads_dir = os.path.join(self.downloads_dir, fileinfo.rootfilename)
        self.files = fileinfo.files
        self.pieces_list = [False] * len(fileinfo.pieces)
        # get the list of files and paths with the file length
        for z in self.files:                                 # for each file we need to create a place holder which can be opened later
            length = z.length
            name = z.name
            self.create_empty_file(length, name)

    def write_piece_to_file(self, piece):
        start_byte = piece.piece_index * self.fileinfo.piece_length
        # calculate the index of the piece
        current_byte = 0
        # create a count variable to determine relative index of the file
        bytes_to_write = piece.data
        for f in self.files:
            # for each file check the length to determine if the piece belongs in that file
            length = f.length
            name = f.name
            if current_byte + length < start_byte:
                current_byte = current_byte + length
            else:
                # we know the piece contains information for this file
                file_to_write = open(os.path.join(self.downloads_dir, f.name), 'wb')
                offset_this_file = start_byte - current_byte
                file_to_write.seek(offset_this_file)
                # seek to the index relative to the file
                n_bytes_this_file = length - offset_this_file
                file_to_write.write(bytes_to_write[:n_bytes_this_file])
                bytes_to_write = bytes_to_write[n_bytes_this_file:]
                if not bytes_to_write:
                    break
                else:
                    current_byte += length
                    start_byte = current_byte
                # add piece to completed pieces
                self.pieces_list[piece.piece_index] = True
                file_to_write.close()

    def create_empty_file(self, length, name):
        filePath = os.path.join(self.downloads_dir, name) # path of the directory in which the file will exist
        if not os.path.exists(filePath):
            os.makedirs(os.path.dirname(filePath))        # create the directory if it doesn't exist
        f = open(filePath, "wb")                          # open a new file to place pieces into
        f.seek(length-1)                                  # find last bit in the file
        f.write("\0")                                     # add one empty bit at the end
        f.close()                                         # place holder created
    
    def has_piece(self, piece_index):
        return self.pieces_list[piece_index]

    def get_piece(self, piece):
        if has_piece(self, piece.piece_index):
            start_byte = piece.piece_index * self.fileinfo.piece_length
            # calculate the index of the piece
            current_byte = 0
            # create a count variable to determine relative index of the file
            bytes_to_read = None
            for f in self.files:
                # for each file check the length to determine if the piece belongs in that file
                length = f.length
                name = f.name
                if current_byte + length < start_byte:
                    current_byte = current_byte + length
                else:
                    file_to_read = open(os.path.join(self.downloads_dir, f.name), 'rb')
                    offset_this_file = start_byte - current_byte
                    file_to_read.seek(offset_this_file)
                    # seek to the index relative to the file
                    n_bytes_this_file = length - offset_this_file
                    if n_bytes_this_file >= piece.piece_length:
                        file_piece.data = file_piece.data.join(file_to_read.read(piece.piece_length))
                        break
                    else:
                        file_piece.data = file_piece.data.join(file_to_read.read(n_bytes_this_file))
                        current_byte += length
                        start_byte = current_byte
                    file_to_write.close()
    
    def get_pieces_list(self):
        return self.pieces_list
