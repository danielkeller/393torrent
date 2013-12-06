from torrent import writetodisk
import os.path
import collections
import unittest

class WriteToDiskTest(unittest.TestCase):
    def test_all(self):
        class mock_return_piece(object):
            def __init__(self):
                self.piece_index = None
                self.piece_length = 16
                self.data = None

        class mock_piece_front(object):
            def __init__(self):
                self.piece_index = 0
                self.data = b'om'

        class mock_piece_overlap(object):
            def __init__(self):
                self.piece_index = 25
                self.data = b'ad'

        class mock_piece_end(object):
            def __init__(self):
                self.piece_index = 47
                self.data = b'jy'

        class mock_fileinfo(object):
            def __init__(self):
                self.piece_length = 16
                self.rootfilename = "Major_Lazor"
                self.files = None


        downloadfile = collections.namedtuple('downloadfile', ['length', 'name'])
        f = [downloadfile( 256 , './testPath/testFile1.data'), downloadfile( 512 , './testPath/testFile2.data') ]

        download_dir = os.getcwd()
        test_fileinfo = mock_fileinfo()
        test_fileinfo.files = f
        disk_writer = writetodisk.FilesystemManager(test_fileinfo)
#creating a new download_directory_manager using the dummy info dict
        test_download_dir = os.path.join(download_dir, "Major_Lazor/testPath")
        does_this_dir_exist = os.path.exists(test_download_dir)
        self.assertTrue(does_this_dir_exist)

        self.assertTrue(os.path.exists(os.path.join(os.getcwd(), 'Major_Lazor/testPath/testFile1.data')))
        self.assertTrue(os.path.exists(os.path.join(os.getcwd(), 'Major_Lazor/testPath/testFile2.data')))

        piece_front = mock_piece_front()
        piece_overlap = mock_piece_overlap()
        piece_end = mock_piece_end()

        return_piece_front = mock_return_piece()
        return_piece_overlap = mock_return_piece()
        return_piece_end = mock_return_piece()
        return_piece_front.piece_index = 0
        return_piece_overlap.piece_index = 25
        return_piece_end.piece_index = 47

        disk_writer.write_piece_to_file(piece_front)
        disk_writer.get_piece(return_piece_front)
        self.assertTrue(return_piece_front.data == piece_front.data)

        disk_writer.write_piece_to_file(piece_overlap)
        disk_writer.get_piece(return_piece_overlap)
        self.assertTrue(piece_overlap.data == return_piece_overlap.data)

        disk_writer.write_piece_to_file(piece_end)
        disk_writer.get_piece(return_piece_end)
        self.assertTrue(piece_end.data == return_piece_end.data)

if __name__ == '__main__':
    unittest.main()
