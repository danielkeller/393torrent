import unittest
import mock
from torrent.files import FilePiece, FileBlock

class FilePieceTest(unittest.TestCase):
    def test_init(self):
        piece = FilePiece(mock.MagicMock(), mock.MagicMock(), mock.MagicMock())  
        self.assertTrue(hasattr(piece, 'is_complete'))
        self.assertTrue(hasattr(piece, 'piece_index'))
        self.assertTrue(hasattr(piece, 'piece_hash'))
        self.assertTrue(hasattr(piece, 'piece_length'))
        self.assertTrue(hasattr(piece, 'blocks'))        
    
    def test_add_block(self):
        piece = FilePiece(mock.MagicMock(), mock.MagicMock(), mock.MagicMock())
        piece.add_block(mock.MagicMock(), mock.MagicMock())
    
    def test_get_next_block_id(self):
        piece = FilePiece(mock.MagicMock(), mock.MagicMock(), mock.MagicMock())
        piece.get_next_block_id()
    
    def test_is_fully_requested(self):
        piece = FilePiece(mock.MagicMock(), mock.MagicMock(), mock.MagicMock())
        is_fully_requested = piece.is_fully_requested() 
    
    def test_is_fully_downloaded(self):
        piece = FilePiece(mock.MagicMock(), mock.MagicMock(), mock.MagicMock())
        is_fully_downloaded = piece.is_fully_downloaded()

    def test_verify_and_write(self):
        piece = FilePiece(mock.MagicMock(), mock.MagicMock(), mock.MagicMock())

        

class FileBlockTest(unittest.TestCase):
    def test_init(self):
            block = FileBlock(mock.MagicMock(), mock.MagicMock())
            self.assertTrue(hasattr(block, 'block_id'))
            self.assertTrue(hasattr(block, 'data'))

if __name__ == "__main__":
    unittest.main()
