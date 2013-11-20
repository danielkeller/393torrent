import os
import argparse
import bencode
import fileinfo

class TorrentApplication(object):
    def __init__(self, torrent_file, seed):
        self.file_info = TorrentFileRetriever(torrent_file).retrieve()
        self.seed = seed

    def start(self):
        self.file_info.begin_download()
        print self.file_info.trackers

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
    pass

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
