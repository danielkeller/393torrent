import mock
import unittest
from torrent import torrent
from torrent.torrent import TorrentApplication, TorrentFileRetriever, TorrentDownloader

class TorrentTest(unittest.TestCase):
    def test_app(self):
        app = None
        with mock.patch.object(torrent, 'TorrentFileRetriever', mock.Mock()) as m:
            app = TorrentApplication('test', False)
            m.assert_called_with('test')
            self.assertEqual(app.file_info, m().retrieve())
            self.assertEqual(app.seed, False)

        with mock.patch.object(torrent, 'TorrentDownloader', mock.Mock()) as m:
            app.start()
            app.file_info.begin_download.assert_called_with()
            m().start.assert_called_with()

class TorrentDownloaderTest(unittest.TestCase):
    def setUp(self):
        fileinfo = TorrentFileRetriever('testcases/debian.torrent').retrieve()
        with mock.patch.object(torrent, 'UserInterface', mock.Mock()):
            with mock.patch.object(torrent.peer, 'PeerServer', mock.Mock()):
                self.downloader = TorrentDownloader(fileinfo)

    def test_connect_to_peers(self):
        self.downloader.fileinfo.begin_download()
        with mock.patch.object(torrent.peer, 'PeerConn', mock.Mock()) as m:
            self.downloader.connect_to_peers()
            self.assertEqual(30, m.call_count)

    def test_got_piece(self):
        with mock.patch.object(self.downloader, 'pieces', [mock.Mock()]):
            with mock.patch.object(self.downloader, 'close_all_peers', mock.Mock()):
                self.downloader.got_piece(0, 0, 'abcd')
                self.downloader.pieces[0].verify_and_write.assert_called_with(self.downloader.filesystem_manager)
                self.downloader.close_all_peers.assert_called()

    def test_close_peers(self):
        with mock.patch.object(self.downloader, 'peers', [mock.Mock()] * 5) as mocks:
            self.downloader.close_all_peers()
            for m in mocks:
                m.close.assert_called_with()
            self.assertEqual(self.downloader.peers,[])

    def test_get_request_to_make(self):
        with mock.patch.object(self.downloader, 'get_rarest_piece_had_by'):
            p, b, size = self.downloader.get_request_to_make(mock.Mock())

    def test_update_choking(self):
        self.downloader.update_choking_status(True)
        self.downloader.update_choking_status(False)

    def test_got_request(self):
        self.downloader.got_request(mock.Mock(), tuple([mock.MagicMock()]*3))

    def test_interest_state(self):
        self.downloader.interest_state(mock.MagicMock())

    def test_peer_closed(self):
        m1 = mock.Mock()
        m2 = mock.Mock()
        m3 = mock.Mock()
        with mock.patch.object(self.downloader, 'peers', [m1, m2, m3]) as fakepeers:
            self.downloader.peer_closed(m2)
            self.assertEqual(fakepeers, [m1, m3])

if __name__ == "__main__":
    unittest.main()
