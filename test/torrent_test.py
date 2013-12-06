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

    def test_connect_to_peers(self):
        pass

    def test_rarest(self):
        pass

    def test_choking(self):
        pass

    def test_got_piece(self):
        pass

    def test_got_request(self):
        pass

    def test_interest_state(self):
        pass

    def test_close_peers(self):
        pass

    def test_get_request_to_make(self):
        pass

    def test_peer_closed(self):
        pass


if __name__ == "__main__":
    unittest.main()
