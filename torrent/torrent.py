import os
import argparse
from Queue import Queue

import bencode

import fileinfo
from files import FilePiece

BLOCK_SIZE = 2 ** 14

class TorrentApplication(object):
    def __init__(self, torrent_file, seed):
        self.file_info = TorrentFileRetriever(torrent_file).retrieve()
        self.seed = seed

    def start(self):
        self.file_info.begin_download()
        print [repr(tr.peers) for trs in self.file_info.trackers for tr in trs]
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
        self.pieces = [FilePiece(idx, sha1, fileinfo) for idx, sha1 in enumerate(fileinfo.pieces)]
        self.peers = []
        self.queue = Queue()

    def connect_to_peers(self):
        pass

    def get_rarest_piece_had_by(self, peer):
        id_to_have_map = {}
        for idx, has in enumerate(peer.bitfield):
            id_to_have_map[idx] = 1

        for otherpeer in self.peers:
            for idx, has in enumerate(otherpeer.bitfield):
                if idx in id_to_have_map:
                    id_to_have_map[idx] = id_to_have_map[idx] + 1

        piece_id = min(id_to_have_map, key=lambda x: id_to_have_map[x])
        return self.pieces[piece_id]

    def start(self):
        while not all(self.pieces.is_complete):
            self.connect_to_peers()
            while not self.queue.empty():
                piece_id, begin_byte, data = self.queue.get()
                block_id = begin_byte / BLOCK_SIZE
                self.pieces[piece_id].add_block(block_id, data)

            peers_to_remove = []
            for peer in self.peers:
                if peer.closed:
                    peers_to_remove.append(peer)
                    continue
                piece_to_get = self.get_rarest_piece_had_by(peer)
                block_idx = piece_to_get.get_next_block_id()
                peer.request(piece_to_get.piece_index, BLOCK_SIZE * block_idx, BLOCK_SIZE)

            for peer in peers_to_remove:
                self.peers.remove(peer)

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
