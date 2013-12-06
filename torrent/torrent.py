import os
import time
import argparse
from Queue import Queue
import bencode
import fileinfo
from files import FilePiece
from writetodisk import FilesystemManager
import peer
import threading
import asyncore
import socket
import random
from ui import UserInterface
BLOCK_SIZE = 2 ** 14

class TorrentApplication(object):
    def __init__(self, torrent_file, seed):
        self.file_info = TorrentFileRetriever(torrent_file).retrieve()
        self.seed = seed

    def start(self):
        self.file_info.begin_download()
        downloader = TorrentDownloader(self.file_info)
        downloader.start()

class TorrentFileRetriever(object):
    def __init__(self, torrent_file):
        self.torrent_file = torrent_file

    def retrieve(self):
        # either read the torrent file if it's a file or
        try:
            file_text = open(self.torrent_file).read()
            return self.handle_torrent_file(file_text)
        except IOError as e:
            print "Sorry!  File doesn't appear to be readable!"
            print "Error:  " + str(e)

    def handle_torrent_file(self, torrent_file_text):
        return fileinfo.TorrentFileInfo(torrent_file_text)

    def handle_magnet_link(self, magnet_link_url):
        raise NotImplementedError

class TorrentDownloader(object):
    def __init__(self, fileinfo, n_connections = 30):
        self.fileinfo = fileinfo
        self.n_connections = n_connections
        self.pieces =  [FilePiece(idx, sha1, fileinfo) for idx, sha1 in enumerate(fileinfo.pieces)]
        self.peers = []
        self.queue = Queue()
        self.ui = UserInterface(self.fileinfo.total_size)
        self.server = peer.PeerServer(6880, self.fileinfo)
        self.filesystem_manager = FilesystemManager(self.fileinfo)
        #start with wrong estimate
        self.piece_freq = [1] * len(self.pieces)

    def connect_to_peers(self):
        for p in self.fileinfo.get_all_peers():
            if len(self.peers) == self.n_connections:
                break
            if any(other.host == p.ip and other.port == p.port for other in self.peers):
                continue
            try:
                self.ui.update_log('connect ' + str(p))
                self.fileinfo.used_peer(p)
                self.ui.peer_connected()
                self.peers += [peer.PeerConn(self.fileinfo, self, hostport=(p.ip, p.port))]
            except socket.error as e:
                self.ui.update_log(str(e))

    def update_piece_freq(self):
        self.piece_freq = [0] * len(self.pieces)

        for otherpeer in self.peers:
            for idx, has in enumerate(otherpeer.bitfield):
                self.piece_freq[idx] += has

    def get_rarest_piece_had_by(self, peer):
        if random.randint(0, 50) == 0:
            self.update_piece_freq() #only do this occasionally to save time
        piece_id, freq = min(enumerate(self.piece_freq),
            key=lambda (i, f): f if peer.bitfield[i] and not self.pieces[i].is_fully_requested() else 99999)
        if self.pieces[piece_id].is_fully_requested():
            return None
        else:
            return self.pieces[piece_id]

    def update_choking_status(self, new_unchoke):
        if new_unchoke:
            self.ui.peer_unchoked()
        else:
            self.ui.peer_choked()

    def got_piece(self, piece_id, block_begin, data):
        self.ui.got_block(len(data))
        block_id = block_begin / BLOCK_SIZE
        piece = self.pieces[piece_id]
        piece.add_block(block_id, data)
        if piece.is_fully_downloaded():
            [p.have(piece.piece_index) for p in self.peers]
            piece.verify_and_write(self.filesystem_manager)
            self.ui.got_piece()
        if all(piece.is_fully_downloaded() for piece in self.pieces):
            self.close_all_peers()

    def got_request(self, peer, req):
        piece_index, block_offset, block_len = req
        self.fileinfo.get_piece(FilePiece(piece_index, 0, self.fileinfo))
        block = piece.data[block_offset : block_offset + block_len]
        peer.piece(piece_index, block_offset, block)

    #this algorithm is extremely simple. but it should work reasonably well.
    def interest_state(self, peer):
        if peer.peer_interested:
            if sum([not p.am_choking for p in self.peers]) < 4:
                peer.choke(False) #unchoke this peer if it's okay
            elif random.randint(0, 9) == 0:
                #sometimes, randomly choke someone else and unchoke anyway
                random.choice([p for p in self.peers if not p.am_choking]).choke(True)
                peer.choke(False)
        else:
            peer.choke(True)
            #optomistically unchoke
            random.choice([p for p in self.peers if p.am_choking]).choke(False)

    def close_all_peers(self):
        for peer in self.peers:
            peer.close()

        self.peers = []

    def get_request_to_make(self, peer):
        piece_to_get = self.get_rarest_piece_had_by(peer)
        if not piece_to_get:
            return None
        block_idx = piece_to_get.get_next_block_id()
        return piece_to_get.piece_index, block_idx * BLOCK_SIZE, BLOCK_SIZE

    def peer_closed(self, peer):
        self.ui.lost_peer(not peer.peer_choking)
        self.peers.remove(peer)
        self.connect_to_peers()

    def start(self):
        self.connect_to_peers()
        asyncore.loop()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process a torrent file.')
    parser.add_argument('torrent_file', type=str,
                   help='a single torrent file')
    parser.add_argument('--seed', dest='seed', action='store_true',
                   default=False,
                   help='seed forever (default: seed while downloading)')
    parser.add_argument('--port', dest='port', action='store',
                    default=6881,
                    help='Optionally set the port for the client to listen on')
    args = parser.parse_args()
    fileinfo.PORT = args.port
    TorrentApplication(args.torrent_file, args.seed).start()
