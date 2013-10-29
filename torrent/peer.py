import asyncore, asynchat
import socket
import struct
from bitarray import bitarray
from time import time, sleep
from Queue import Queue

class _State:
    (PreHandshake, Handshake, PreMessage, Message) = range(0, 4)

class PeerServer(asyncore.dispatcher):
    
    def __init__(self, port, fileinfo):
        self.fileinfo = fileinfo
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(('localhost', port))
        self.listen(5)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print 'connect from %s' % repr(addr)
            conn = PeerConn(self.fileinfo, sock=sock)

class PeerConn(asynchat.async_chat):

    def __init__(self, fileinfo, sock=None, host=None):
        if sock is None:
            asynchat.async_chat.__init__(self)
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connect( (host, 6880) )
        else:
            asynchat.async_chat.__init__(self, sock=sock)
        self.set_terminator(1) #handshake is length-prefixed with one byte
        self.fileinfo = fileinfo
        self.bitfield = len(fileinfo.pieces) * bitarray('0', endian='big')
        self.requests = Queue()
        self.seen = time()
        self.state = _State.PreHandshake
        self.am_choking = True
        self.am_interested = False
        self.peer_choking = True
        self.peer_interested = False
        self.push(struct.pack('>B19sq20s20s', 19, 'BitTorrent protocol', 0, 'test', 'test'))
        #todo: send bitfield

    def collect_incoming_data(self, data):
        self._collect_incoming_data(data)

    def message(self, msgid, fmt='', *args):
        msglen = struct.calcsize(fmt) + 1
        self.push(struct.pack('>Lc' + fmt, msglen, msgid, *args))

    def keepalive(self):
        self.push('\x00\x00\x00\x00')

    def found_terminator(self):

        if self.state == _State.PreHandshake:
            pstrlen, = struct.unpack('B', self._get_data())
            if pstrlen != 19:
                self.close_when_done()
                return
            self.state = _State.Handshake
            self.set_terminator(pstrlen + 48)

        elif self.state == _State.Handshake:
            pstr, reserved, self.info_hash, self.peer_id = struct.unpack('>19sq20s20s', self._get_data())
            if pstr != 'BitTorrent protocol':
                self.close_when_done()
                print 'hanshake failed'
                return
            #prepare to receive message
            self.set_terminator(4)
            print 'hanshake successful'
            self.state = _State.PreMessage

        elif self.state == _State.PreMessage:
            msglen, = struct.unpack('>L', self._get_data())
            self.seen = time() #treat all messages as keep-alives
            if msglen != 0:
                self.set_terminator(msglen)
                self.state = _State.Message

        else:
            data = self._get_data()
            msgid = data[0]
            if msgid == '0': #choke
                self.peer_choking = True
                print 'choked'
            if msgid == '1': #unchoke
                self.peer_choking = False
                print 'unchoked'
            if msgid == '2': #interested
                self.peer_interested = True
                print 'interested'
            if msgid == '3': #uninstrested
                self.peer_interested = False
                print 'uninterested'
            if msgid == '4': #have
                index, = struct.unpack('>L', data[1:])
                self.bitfield[index] = True
            if msgid == '5': #bitfield
                self.bitfield.frombytes(data[1:])
            if msgid == '6': #request
                if not self.am_choking:
                    self.requests.put(struct.unpack('>LLL', data[1:13]))
            if msgid == '7': #piece
                index, begin, block = struct.unpack('>LL', data[1:9]), data[9:]
                self.fileinfo.got_piece(index, begin, block)
            if msgid == '8': #cancel
                pass #DK how to i get rid of individual items from a queue?
            if msgid == '9': #dht port
                pass
            self.set_terminator(4)
            self.state = _State.PreMessage

    def choke(self, state):
        self.am_choking = state
        if state:
            self.message('0')
            try:
                while True: #dump all pending requests
                    self.requests.task_done()
            except ValueError:
                pass
        else:
            self.message('1')

    def interest(self, state):
        self.am_interested = state
        if state:
            self.message('2')
        else:
            self.message('3')

    def have(self, piece):
        if not self.bitfield[piece]: #don't send HAVE unless they might want it
            self.message('4', 'L', piece)

    def request(self, piece, begin, length):
        self.message('6', 'LLL', piece, begin, length)

    def piece(self, index, begin, block):
        self.message('7', 'LL' + len(block) + 's', index, begin, block)

    def cancel(self, piece, begin, length):
        self.message('8', 'LLL', piece, begin, length)

if __name__ == '__main__':
    import fileinfo
    import threading
    import asyncore
    torrfile = fileinfo.TorrentFileInfo(open("testcases/singlefile.torrent").read())
    server = PeerServer(6880, torrfile)
    client = PeerConn(torrfile, host='localhost')
    thr = threading.Thread(target = asyncore.loop)
    thr.start()
    client.choke(True)
    client.choke(False)
    client.interest(True)
    client.interest(False)
    thr.join(1)
    
