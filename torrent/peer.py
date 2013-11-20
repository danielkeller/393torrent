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
        self.bind(('0.0.0.0', port))
        self.listen(5)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print 'connect from %s' % repr(addr)
            #FIXME: notify the application that someone connected
            self.testconn = PeerConn(self.fileinfo, sock=sock)

class PeerConn(asynchat.async_chat):

    def __init__(self, fileinfo, torrent_downloader, sock=None, hostport=None):
        self.closed = False
        self.torrent_downloader = torrent_downloader
        if sock is None: #created as address
            asynchat.async_chat.__init__(self)
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connect(hostport) #expects a host-port pair
        else: #created as socket
            asynchat.async_chat.__init__(self, sock=sock)
        #handshake is length-prefixed with one byte
        self.set_terminator(1)
        self.fileinfo = fileinfo
        #record of pieces that have been recieved
        self.bitfield = len(fileinfo.pieces) * bitarray('0', endian='big')
        #queue of recieved requests
        self.requests = Queue()
        #time last seen (for keep-alive)
        self.seen = time()
        #message handling state (because not all the terminators are the same)
        self.state = _State.PreHandshake
        #standard bits of peer state
        self.am_choking = True
        self.am_interested = False
        self.peer_choking = True
        self.peer_interested = False
        self.n_requests_in_flight = 0
        #send handshake per spec
        self.push(struct.pack('>B19sq20s20s', 19, 'BitTorrent protocol',
                              0, fileinfo.info_hash, fileinfo.peer_id))
        #todo: send bitfield

    def handle_close(self):
        print 'connection terminated'
        self.close()
        self.torrent_downloader.peer_closed(self)

    #just use the default mechanism
    def collect_incoming_data(self, data):
        self._collect_incoming_data(data)

    #helper that adds the message id and length
    def message(self, msgid, fmt='', *args):
        msglen = struct.calcsize('>c' + fmt)
        self.push(struct.pack('>Lc' + fmt, msglen, msgid, *args))

    #handle state machine
    def found_terminator(self):
        if self.state == _State.PreHandshake:
            self._get_hslen()
            self.state = _State.Handshake
            self.set_terminator(19 + 48) #rest of handshake
        elif self.state == _State.Handshake:
            self._get_handshake()
            self.state = _State.PreMessage
            self.set_terminator(4) #messages are length-prefixed with 4 bytes
        elif self.state == _State.PreMessage:
            self._get_msglen()
        else:
            self._get_message()
            self.set_terminator(4)
            self.state = _State.PreMessage
            # runs first time after first HAVE
            # then again whenever needed
            while self.n_requests_in_flight < 10:
                to_get = self.torrent_downloader.get_request_to_make(self)
                if not to_get:
                    break
                piece_id, block_start, block_size = to_get
                self.request(piece_id, block_start, block_size)


    def keepalive(self):
        self.push('\x00\x00\x00\x00')

    def _get_hslen(self):
        pstrlen, = struct.unpack('B', self._get_data())
        if pstrlen != 19: #length must be 19
            self.close_when_done()
            print 'hanshake failed'
            return

    def _get_handshake(self):
        pstr, reserved, self.info_hash, self.peer_id = struct.unpack('>19sq20s20s', self._get_data())
        if pstr != 'BitTorrent protocol': #protocol string must be this
            self.close_when_done()
            print 'hanshake failed'
            return
        print 'hanshake successful'

    def _get_msglen(self):
        msglen, = struct.unpack('>L', self._get_data())
        self.seen = time() #treat all messages as keep-alives
        if msglen != 0:
            self.set_terminator(msglen) #rest of message
            self.state = _State.Message

    def _get_message(self):
        data = self._get_data()
        print repr(data)
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
            print 'have', index, self.bitfield
        if msgid == '5': #bitfield
            if len(data[1:]) !=  bitarray.bits2bytes(len(bitfield)): #wrong length
                self.close_when_done()
                return
            self.bitfield.frombytes(data[1:])
            print 'bitfield', index, self.bitfield
        if msgid == '6': #request
            if not self.am_choking:
                self.requests.put(struct.unpack('>LLL', data[1:13]))
                print 'request', repr(self.requests.get())
                self.requests.task_done()
        if msgid == '7': #piece
            block = data[9:]
            index, begin = struct.unpack('>LL', data[1:9])
            print 'got piece', repr( (index, begin, block) )
            self.torrent_downloader.got_piece(index,begin,block)
        if msgid == '8': #cancel
            print 'cancel', repr(struct.unpack('>LLL', data[1:13]))
            #DK how to i get rid of individual items from a queue?
        if msgid == '9': #dht port
            pass

    def choke(self, state):
        self.am_choking = state
        if state:
            self.message('0') #choke
            try:
                while True: #dump all pending requests on choke per spec
                    self.requests.task_done()
            except ValueError:
                pass
        else:
            self.message('1') #unchoke

    def interest(self, state):
        self.am_interested = state
        if state:
            self.message('2') #interested
        else:
            self.message('3') #uninterested

    def have(self, piece):
        if not self.bitfield[piece]: #don't send HAVE unless they might want it
            self.message('4', 'L', piece)

    def request(self, piece, begin, length):
        self.n_requests_in_flight += 1
        self.message('6', 'LLL', piece, begin, length)

    def piece(self, index, begin, block):
        self.n_requests_in_flight -= 1
        self.message('7', 'LL' + str(len(block)) + 's', index, begin, block)

    def cancel(self, piece, begin, length):
        self.message('8', 'LLL', piece, begin, length)
