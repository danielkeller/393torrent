import bencode
import hashlib
import requests
import time
import collections
import os

PORT = 6881

class TorrentFileInfo(object):
    def __init__(self, torrent_file_text):
        torrent_dict = bencode.bdecode(torrent_file_text)
        self.comment = torrent_dict.get('comment')
        self.created = time.localtime(torrent_dict.get('creation date'))
        self.author = torrent_dict.get('created by')
        pieces = torrent_dict['info']['pieces']
        self.pieces = [pieces[i:i+20] for i in range(0, len(pieces), 20)]
        self.piece_length = torrent_dict['info']['piece length']
        self.info_hash = self.find_info_hash(torrent_file_text)
        self.peer_id = '393Torrent' + os.urandom(9)
        self.files = self.get_files_from_info_dict(torrent_dict['info'])
        self.total_size = sum([file.length for file in self.files])
        self.bytes_downloaded = 0
        self.bytes_uploaded = 0
        self.tracker = TorrentTracker(torrent_dict['announce'], self)

    def find_info_hash(self, text):
        info_dict_start = text.find('4:infod') + len('4:info')
        success = False
        end = info_dict_start
        while not success and end <= len(text):
            end += 1
            try:
                bencode.bdecode(text[info_dict_start:end])
                break
            except bencode.BTFailure:
                pass
        info_string = text[info_dict_start:end]
        return hashlib.sha1(info_string).digest()

    def get_files_from_info_dict(self, info_dict):
        downloadfile = collections.namedtuple('downloadfile', ['length', 'name'])
        if 'files' in info_dict:
            return [
                    downloadfile(f['length'],os.path.join([info_dict['name']] + f['path']))
                    for f in info_dict['files']
                   ]
        else:
            return [downloadfile(info_dict['length'], info_dict['name'])]

    def got_piece(self, index, begin, block):
        pass

class TorrentTracker(object):
    def __init__(self, tracker_url, torrent):
        self.tracker_url = tracker_url
        self.torrent_info = torrent
        self.tracker_id = None
        self.complete = 0
        self.incomplete = 0
        self.peers = []
        self.interval = 60 * 10
        
    def get_basic_params(self):
        params = {}
        params['info_hash'] = self.torrent_info.info_hash
        params['peer_id'] = self.peer_id
        params['port'] = PORT
        params['uploaded'] = self.torrent_info.bytes_downloaded
        params['downloaded'] = self.torrent_info.bytes_uploaded
        params['left'] = self.torrent_info.total_size - self.torrent_info.bytes_downloaded
        params['compact'] = 0
        params['no_peer_id'] = 1
        if self.tracker_id:
            params['tracker_id'] = self.tracker_id
        return params

    def _communicate(self, event=None):
        params = self.get_basic_params()
        if event:
            params['event'] = event
        response = requests.get(self.tracker_url, params = params)
        self._process_response(response.text)
        
    def _process_response(self, response_text):
        response_dict = bencode.bdecode(response_text)
        if 'failure reason' in response_dict:
            raise IOException(response_dict['failure reason'])
        self.complete = response_dict['complete']
        self.incomplete = response_dict['incomplete']
        self.peers = [TorrentPeer(peer['ip'], peer['port']) for peer in response_dict['peers']]
        self.interval = response_dict['interval']
        if 'tracker id' in self.response_dict:
            self.tracker_id = self.response_dict['tracker id']        

    def update_tracker_on_progress(self):
        self._communicate()
        
    def begin_download(self):
        self._communicate('started')
    
    def end_download(self):
        self._communicate('stopped')

class TorrentPeer(object):
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        
    def __str__(self):
        return str({'ip' : self.ip, 'port' : self.port})
