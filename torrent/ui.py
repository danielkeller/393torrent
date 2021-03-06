import time
import curses

class UserInterface(object):
    def __init__(self, total_pieces):
        self.window = curses.initscr()
        import atexit
        atexit.register(curses.endwin)
        self.total_pieces = total_pieces
        self.bottom = self.window.getmaxyx()[0]
        self.top_of_log = self.bottom - 16
        self.n_pieces = 0
        self.start_time = time.clock()
        self.piece_count_y = 2
        self.peer_count_y = 4
        self.unchoked_count_y = 6
        self.speed_y = 8
        self.peers = 0
        self.unchoked = 0
        self.downloaded = 0
        self.window.move(self.piece_count_y, 1)
        self.window.addstr("Pieces: 0 / " + str(self.total_pieces))
        self.window.move(self.peer_count_y, 1)
        self.window.addstr("Peers: 0")
        self.window.move(self.unchoked_count_y, 1)
        self.window.addstr("Unchoked: 0")
        self.window.move(self.speed_y, 1)
        self.window.addstr("Download Speed: 0")

    def update_log(self, log_line):
        self.window.move(self.top_of_log, 1)
        self.window.insertln()
        self.window.addstr(log_line)
        self.window.box(0,0)
        self.window.refresh()

    def peer_connected(self):
        self.peers += 1
        self.window.move(self.peer_count_y, len("Peers: ") + 1)
        self.window.clrtoeol()
        self.window.addstr(str(self.peers))
        self.window.box(0,0)
        self.window.refresh()

    def peer_unchoked(self):
        self.unchoked += 1
        self.window.move(self.unchoked_count_y, len("Unchoked: ") + 1)
        self.window.clrtoeol()
        self.window.addstr(str(self.unchoked))
        self.window.box(0,0)
        self.window.refresh()

    def peer_choked(self):
        self.unchoked -= 1
        self.window.move(self.unchoked_count_y, len("Unchoked: ") + 1)
        self.window.clrtoeol()
        self.window.addstr(str(self.unchoked))
        self.window.box(0,0)
        self.window.refresh()

    def lost_peer(self, was_unchoked = True):
        self.peers -= 1
        self.unchoked -= 1 if was_unchoked else 0
        self.window.move(self.unchoked_count_y, len("Unchoked: ") + 1)
        self.window.clrtoeol()
        self.window.addstr(str(self.unchoked))
        self.window.move(self.peer_count_y, len("Peers: ") + 1)
        self.window.clrtoeol()
        self.window.addstr(str(self.peers))
        self.window.box(0,0)
        self.window.refresh()

    def got_block(self, size):
        total_time = time.clock() - self.start_time
        self.downloaded += size
        self.window.move(self.speed_y, len("Download Speed: ") + 1)
        self.window.clrtoeol()
        self.window.addstr("{0:.2f}".format(float(self.downloaded) / total_time / 1024) + " Kbps")
        self.window.box(0,0)
        self.window.refresh()

    def got_piece(self):
        self.window.move(self.piece_count_y, len("Pieces: ") + 1)
        self.window.clrtoeol()
        self.n_pieces += 1
        self.window.addstr(str(self.n_pieces) + " / " + str(self.total_pieces))
        self.window.box(0,0)
        self.window.refresh()
