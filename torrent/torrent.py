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
    def __init__(self, fileinfo, n_connections = 10):
        self.fileinfo = fileinfo
        self.n_connections = n_connections
        self.pieces =  [FilePiece(idx, sha1, fileinfo) for idx, sha1 in enumerate(fileinfo.pieces)]
        self.peers = []
        self.queue = Queue()
        self.ui = UserInterface(self.fileinfo.total_size)
        self.server = peer.PeerServer(6880, self.fileinfo)
        self.filesystem_manager = FilesystemManager(self.fileinfo)

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

    def get_rarest_piece_had_by(self, peer):
        id_to_have_map = {}
        for idx, has in enumerate(peer.bitfield):
            if not self.pieces[idx].is_fully_requested():
                id_to_have_map[idx] = 1

        for otherpeer in self.peers:
            for idx, has in enumerate(otherpeer.bitfield):
                if idx in id_to_have_map:
                    id_to_have_map[idx] = id_to_have_map[idx] + 1

        if not id_to_have_map:
            return None
        piece_id = min(id_to_have_map, key=lambda x: id_to_have_map[x])
        return self.pieces[piece_id]

    def update_choking_status(self, new_unchoke):
        if new_unchoke:
            self.ui.peer_unchoked()
        else:
            self.ui.peer_choke()

    def got_piece(self, piece_id, block_begin, data):
        block_id = block_begin / BLOCK_SIZE
        piece = self.pieces[piece_id]
        piece.add_block(block_id, data)
        if piece.is_fully_downloaded():
            piece.verify_and_write()
        if all(piece.is_fully_downloaded() for piece in self.pieces):
            self.close_all_peers()

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
        self.ui.lost_peer(peer.peer_choking)
        self.peers.remove(peer)
        self.connect_to_peers()

    def start(self):
        self.connect_to_peers()
        asyncore.loop()

class TorrentUploader(object):
    pass

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
