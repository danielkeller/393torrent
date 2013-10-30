import mock
import unittest
import time
import os
import hashlib
from torrent import fileinfo

class TorrentInfoTest(unittest.TestCase):
    def test_init(self):
        with mock.patch.object(fileinfo.bencode, 'bdecode', mock.MagicMock()) as decode_mock:
            f_info = fileinfo.TorrentFileInfo('mocked_out_test')
            self.assertEqual(f_info.comment, decode_mock('mocked_out_test').get('comment'))
            self.assertEqual(f_info.created, time.localtime(decode_mock('mocked_out_test').get('creation date')))
            self.assertEqual(f_info.author, decode_mock('mocked_out_test').get('created by'))
            self.assertTrue(hasattr(f_info, 'pieces'))
            self.assertTrue(hasattr(f_info, 'piece_length'))
            self.assertTrue(hasattr(f_info, 'info_hash'))
            self.assertTrue(hasattr(f_info, 'peer_id'))
            self.assertTrue(hasattr(f_info, 'files'))
            self.assertTrue(hasattr(f_info, 'total_size'))
            self.assertTrue(hasattr(f_info, 'bytes_downloaded'))
            self.assertTrue(hasattr(f_info, 'bytes_uploaded'))
            self.assertTrue(hasattr(f_info, 'tracker'))

    def test_file_from_dict(self):
        with mock.patch.object(fileinfo.bencode, 'bdecode', mock.MagicMock()) as decode_mock:
            f_info = fileinfo.TorrentFileInfo('mocked_out_test')
            files = f_info.get_files_from_info_dict({'length': 5, 'name': 'something'})
            self.assertEqual(len(files), 1)
            self.assertEqual(files[0][0], 5)
            self.assertEqual(files[0][1], 'something')

    def test_files_from_dict(self):
        with mock.patch.object(fileinfo.bencode, 'bdecode', mock.MagicMock()) as decode_mock:
            f_info = fileinfo.TorrentFileInfo('mocked_out_test')
            files = f_info.get_files_from_info_dict({'name': 'thing', 'files': [{'length': 5, 'path': ['something']}]})
            self.assertEqual(len(files), 1)
            self.assertEqual(files[0][0], 5)
            self.assertEqual(files[0][1], os.path.join(['thing', 'something']))

    def test_info_hash(self):
        text = 'd4:infod1:a1:bee'
        with mock.patch.object(fileinfo.bencode, 'bdecode', mock.MagicMock()) as decode_mock:
            f_info = fileinfo.TorrentFileInfo('mocked_out_test')
        self.assertEqual(f_info.find_info_hash(text), hashlib.sha1('d1:a1:be').digest())

if __name__ == "__main__":
    unittest.main()
