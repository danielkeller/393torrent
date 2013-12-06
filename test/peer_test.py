import unittest
import thread
import signal
import mock
from torrent import peer
import socket
from torrent.peer import PeerConn, PeerServer
import asyncore

class TimeoutError(Exception): pass

# define the timeout handler
def handler(signum, frame):
    raise TimeoutError()

class PeerServerTest(unittest.TestCase):
    def test_create(self):
        with mock.patch.object(peer, 'PeerConn', mock.Mock()) as m:
            fileinfo = mock.MagicMock()
            fileinfo.info_hash = ''
            fileinfo.peer_id = ''
            svr = PeerServer(6880, fileinfo)
            svr.torrent_downloader = mock.MagicMock()
            with mock.patch.object(svr, 'torrent_downloader', mock.Mock()) as m1:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(('localhost', 6880)) #expects a host-port pair

class PeerConnTest(unittest.TestCase):
    def test_init(self):
        fileinfo = mock.MagicMock()
        fileinfo.info_hash = ''
        fileinfo.peer_id = ''
        downloader = mock.MagicMock()
        (a, b) = socket.socketpair()
        connA = PeerConn(fileinfo, downloader, sock=a)
        connB = PeerConn(fileinfo, downloader, sock=b)
        connA.bitfield = [1] * 30
        connB.bitfield = [1] * 30
        #connA.keepalive()
        connA.choke(False)
        connA.choke(True)
        connA.interest(True)
        connA.interest(False)
        connA.have(10)
        connA.request(10, 10, 10)
        connA.cancel(10, 10, 10)
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(10)
        try:
            asyncore.loop()
        except TimeoutError as exc:
            print "timeout"
        finally:
            signal.alarm(0)

if __name__ == "__main__":
    unittest.main()
