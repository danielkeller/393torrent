BLOCK_SIZE = 2 ** 14

class FilePiece(object):
    def __init__(self, piece_index, piece_hash, fileinfo):
        self.is_complete = False
        self.piece_index = piece_index
        self.piece_hash = piece_hash
        self.piece_length = fileinfo.piece_length
        self.blocks = [None] * (self.piece_length/BLOCK_SIZE)

    def add_block(self, block_id, data):
        self.blocks[block_id] = FileBlock(block_id, data)

    def get_next_block_id(self):
        for idx, block in enumerate(self.blocks):
            if block == None:
                self.blocks[idx] = FileBlock(idx)
                return idx
        raise Exception("Next Block Called On Fully Requested Piece")

    def is_fully_requested(self):
        return all(block != None for block in self.blocks)

    def is_fully_downloaded(self):
        if not self.is_fully_requested():
            return False
        return all(block.data != None for block in self.blocks)

    def verify_and_write(self, filewriter):
        pass

class FileBlock(object):
    def __init__(self, block_id, data=None):
        self.is_complete = False
        self.block_id = block_id
        self.data = data

