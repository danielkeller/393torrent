import unittest
from torrent.ui import UserInterface

class UISmokeTest(unittest.TestCase):
    def test_all_methods(self):
        ui = UserInterface(1)
        ui.update_log('something')
        ui.peer_connected()
        ui.peer_unchoked()
        self.assertEqual(1, ui.unchoked)
        ui.peer_choked()
        self.assertEqual(0, ui.unchoked)
        ui.lost_peer(True)
        ui.got_block(100)
        ui.got_piece()

if __name__ == "__main__":
    unittest.main()
