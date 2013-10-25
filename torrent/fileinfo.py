import bencode
import hashlib
import requests

class TorrentFileInfo(object):
    def __init__(self, torrent_file_text):
        torrent_dict = bencode.bdecode(torrent_file_text)
        self.tracker = TorrentTracker(torrent_dict['announce'])
        self.comment = torrent_dict.get('comment')
        self.created = time.localtime(torrent_dict.get('creation date'))
        self.author = torrent_dict.get('created by')
        pieces = torrent_dict['info']['pieces']
        self.pieces = [pieces[i:i+20] for i in range(0, len(pieces), 20)]
        self.info_hash = self.find_info_hash(torrent_file_text)
        self.files = self.get_files_from_info_dict(torrent_dict['info'])


    def find_info_hash(self, text):
        info_dict_start = text.find('4:infod') + len('4:info')
        success = False
        end = info_dict_start
        while not success and end <= len(text):
            end += 1
            try:
                bencode.bdecode(text[info_dict_start:end])
                break
            except BTFailure:
                pass
        info_string = text[info_dict_start:end]
        return hashlib.sha1(info_string).digest()

    def get_files_from_info_dict(self, info_dict):
        downloadfile = namedtuple('length', 'name')
        if 'files' in info_dict:
            return [
                    downloadfile(f['length'],os.path.join([info_dict['name']] + f['path']))
                    for f in info_dict['files']
                   ]
        else:
            return [downloadfile(info_dict['length'], info_dict['name'])]


class TorrentTracker(object):
    def __init__(self, tracker_url):
        self.tracker_url = tracker_url

    def initiate_download(self):
        pass

    def get_peer_list(self):
        pass

    def update_tracker_on_progress(self, amount_downloaded, amount_uploaded):
        pass

class TorrentPeer(object):
    pass
