import mock
import unittest
from torrent import fileinfo

class TrackerTest(unittest.TestCase):
    def test_communicate(self):
        tracker = fileinfo.TorrentTracker(mock.MagicMock(), mock.MagicMock())
        with mock.patch.object(fileinfo.requests, 'get', mock.Mock()) as m:
            with mock.patch.object(tracker, '_process_response', mock.Mock()) as m2:
                tracker._communicate()
                m2.assert_called_with(m().content)

    def test_params(self):
        tracker = fileinfo.TorrentTracker(mock.MagicMock(), mock.MagicMock())
        param_dict = tracker.get_basic_params()
        self.assertNotIn('event', param_dict)
        self.assertIn('info_hash', param_dict)
        self.assertIn('peer_id', param_dict)
        self.assertIn('port', param_dict)
        self.assertIn('uploaded', param_dict)
        self.assertIn('downloaded', param_dict)
        self.assertIn('left', param_dict)
        self.assertIn('compact', param_dict)

    def test_begin(self):
        tracker = fileinfo.TorrentTracker(mock.MagicMock(), mock.MagicMock())
        with mock.patch.object(tracker, '_communicate', mock.Mock()) as m:
            tracker.begin_download()
            m.assert_called_with('started')

if __name__ == "__main__":
    unittest.main()
