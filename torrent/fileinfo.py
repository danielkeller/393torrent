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
        self.peer_id = '393Torrent' + os.urandom(10)
        self.files = self.get_files_from_info_dict(torrent_dict['info'])
        self.rootfilename = torrent_dict['info']['name']
        self.total_size = sum([file.length for file in self.files])
        self.bytes_downloaded = 0
        self.bytes_uploaded = 0
        self.trackers = [[TorrentTracker(torrent_dict['announce'], self)]]
        if 'announce-list' in torrent_dict:
            self.trackers = [[TorrentTracker(d, self) for d in l] for l in torrent_dict['announce-list']]

    def begin_download(self):
        self.tracker_communicate(event='started')

    def end_download(self):
        self.tracker_communicate(event='stopped')

    def used_peer(self, peer):
        for trackerlist in self.trackers:
            for tracker in trackerlist:
                if peer in tracker.peers:
                    tracker.peers.remove(peer)

        if len(self.get_all_peers()) == 0:
            self.tracker_communicate()

    def get_all_peers(self):
        peers = []
        for trackerlist in self.trackers:
            for tracker in trackerlist:
                peers.extend(tracker.peers)

        return peers

    def tracker_communicate(self, event = None):
        any_successes = False
        for equiv_list in self.trackers:
            for tracker in equiv_list:
                try:
                    tracker._communicate(event=event)
                    any_successes = True
                except IOError as e:
                    pass
            if any_successes:
                break
        if not any_successes:
            raise IOError("No trackers responded.")

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
        bencode.bdecode(info_string)
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

    def __str__(self):
        return '<TorrentTracker, %i peers>' % len(self.peers)

    def __repr__(self):
        return str(self)

    def get_basic_params(self):
        params = {}
        params['info_hash'] = self.torrent_info.info_hash
        params['peer_id'] = self.torrent_info.peer_id
        params['port'] = PORT
        params['downloaded'] = self.torrent_info.bytes_downloaded
        params['uploaded'] = self.torrent_info.bytes_uploaded
        params['left'] = self.torrent_info.total_size - self.torrent_info.bytes_downloaded
        params['compact'] = 1
        params['no_peer_id'] = 1
        if self.tracker_id:
            params['tracker_id'] = self.tracker_id
        return params

    def _communicate(self, event=None):
        params = self.get_basic_params()
        if event:
            params['event'] = event
        response = requests.get(self.tracker_url, params = params)
        self._process_response(response.content)

    def _process_response(self, response_text):
        try:
            response_dict = bencode.bdecode(response_text)
        except bencode.BTFailure:
            raise IOError(response_text)
        if 'failure reason' in response_dict:
            raise IOError(response_dict['failure reason'])
        self.complete = response_dict.get('complete', 0)
        self.incomplete = response_dict.get('incomplete', 0)
        if isinstance(response_dict['peers'], dict):
            # dict representation
            self.peers = [TorrentPeer(peer['ip'], peer['port']) for peer in response_dict['peers']]
        elif isinstance(response_dict['peers'], basestring):
            # compact representation
            peers = response_dict['peers']
            peerbytes = [peers[i:i+6] for i in range(0, len(peers), 6)]
            self.peers = [TorrentPeer('.'.join(map(str, [ord(x) for x in peer[:4]])), ord(peer[4])*256 + ord(peer[5])) for peer in peerbytes]
        self.interval = response_dict['interval']
        if 'tracker id' in response_dict:
            self.tracker_id = response_dict['tracker id']

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

    def __repr__(self):
        return str(self)
