import time
import curses

class UserInterface(object):
    def __init__(self, total_pieces):
        self.window = curses.initscr()
        self.total_pieces = total_pieces
        self.bottom = self.window.getmaxyx()[0]
        self.top_of_log = self.bottom - 4
        self.n_pieces = 0
        self.start_time = time.clock()
        self.piece_count_y = 1
        self.peer_count_y = 3
        self.unchoked_count_y = 5
        self.speed_y = 7
        self.peers = 0
        self.unchoked = 0
        self.window.move(self.piece_count_y, 0)
        self.window.addstr("Pieces: 0 / " + str(self.total_pieces))
        self.window.move(self.peer_count_y, 0)
        self.window.addstr("Peers: 0")
        self.window.move(self.unchoked_count_y, 0)
        self.window.addstr("Unchoked: 0")
        self.window.move(self.speed_y, 0)
        self.window.addstr("Download Speed: 0")
        import atexit
        atexit.register(curses.endwin)

    def update_log(self, log_line):
        self.window.move(self.top_of_log, 0)
        self.window.insertln()
        self.window.addstr(log_line)
        self.window.refresh()

    def peer_connected(self):
        self.peers += 1
        self.window.move(self.peer_count_y, len("Peers: "))
        self.window.clrtoeol()
        self.window.addstr(str(self.peers))
        self.window.refresh()

    def peer_unchoked(self):
        self.unchoked += 1
        self.window.move(self.unchoked_count_y, len("Unchoked: "))
        self.window.clrtoeol()
        self.window.addstr(str(self.unchoked))
        self.window.refresh()

    def peer_choked(self):
        self.unchoked -= 1
        self.window.move(self.unchoked_count_y, len("Unchoked: "))
        self.window.clrtoeol()
        self.window.addstr(str(self.unchoked))
        self.window.refresh()

    def lost_peer(self, was_unchoked = True):
        self.peers -= 1
        self.unchoked -= 1 if was_unchoked else 0
        self.window.move(self.unchoked_count_y, len("Unchoked: "))
        self.window.clrtoeol()
        self.window.addstr(str(self.unchoked))
        self.window.move(self.peer_count_y, len("Peers: "))
        self.window.clrtoeol()
        self.window.addstr(str(self.peers))
        self.window.refresh()

    def got_piece(self, size):
        total_time = time.clock() - self.start_time
        self.downloaded += size
        self.window.move(self.piece_count_y, len("Pieces: "))
        self.window.clrtoeol()
        self.window.addstr(str(self.n_pieces) + " / " + str(self.total_pieces))
        self.window.move(self.speed_y, len("Download Speed: "))
        self.window.clrtoeol()
        self.window.addstr("{.2f}".format(float(self.downloaded) / total_time) + " Kbps")
        self.window.refresh()
