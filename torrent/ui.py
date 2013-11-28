import time
import curses

class UserInterface(object):
    def __init__(self):
        self.window = curses.initscr()
        self.bottom = self.window.getmaxyx()[0]
        self.top_of_log = self.bottom - 4
        self.n_pieces = 0
        self.start_time = time.clock()
        self.window.move(self.piece_count_y - len("Pieces: "), self.piece_count_x)
        self.window.addstr("Pieces: 0")
        self.window.move(self.speed_y - len("Download Speed: ", self.speed_x)
        self.window.addstr("Download Speed: 0")

    def __del__(self):
        curses.endwin()

    def update_log(self, log_line):
        self.window.move(self.top_of_log, 0)
        self.window.insertln(log_line)
        self.window.refresh()

    def got_piece(self, size):
        total_time = time.clock() - self.start_time
        self.downloaded += size
        self.window.move(self.piece_count_y, self.piece_count_x)
        self.window.addstr(self.n_pieces)
        self.window.move(self.speed_y, self.speed_x)
        self.window.addstr("{.2f}".format(float(self.downloaded) / total_time) + " Kbps")
