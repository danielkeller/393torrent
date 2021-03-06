import asyncore, asynchat
import socket
import struct
from bitarray import bitarray, bits2bytes
from time import time, sleep
from Queue import Queue
import traceback

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
            self.torrent_downloader.ui.update_log( 'connect from %s' % repr(addr))
            #FIXME: notify the application that someone connected
            self.testconn = PeerConn(self.fileinfo, self.torrent_downloader, sock=sock)

class PeerConn(asynchat.async_chat):

    def __init__(self, fileinfo, torrent_downloader, sock=None, hostport=None):
        self.closed = False
        self.torrent_downloader = torrent_downloader
        if sock is None: #created as address
            asynchat.async_chat.__init__(self)
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connect(hostport) #expects a host-port pair
            self.host = hostport[0]
            self.port = hostport[1]
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
        #for piece in self.fileinfo.pieces:
            #if piece.is_fully_downloaded():
                #self.have(piece.piece_index)

    def handle_error(self):
        #self.torrent_downloader.ui.update_log(tbinfo)
        #traceback.print_exc()
        self.torrent_downloader.ui.update_log("Peer disconnected due to error")

    def handle_close(self):
        self.torrent_downloader.ui.update_log( 'connection terminated')
        self.close()
        self.torrent_downloader.peer_closed(self)

    #just use the default mechanism
    def collect_incoming_data(self, data):
        self._collect_incoming_data(data)

    #helper that adds the message id and length
    def message(self, msgid, fmt='', *args):
        msglen = struct.calcsize('>B' + fmt)
        self.push(struct.pack('>LB' + fmt, msglen, msgid, *args))

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
            if self.peer_choking and self.torrent_downloader.get_request_to_make(self):
                self.interest(True)
            while not self.peer_choking and self.n_requests_in_flight < 10:
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
            return

    def _get_handshake(self):
        pstr, reserved, self.info_hash, self.peer_id = struct.unpack('>19sq20s20s', self._get_data())
        if pstr != 'BitTorrent protocol': #protocol string must be this
            self.close_when_done()
            return

    def _get_msglen(self):
        msglen, = struct.unpack('>L', self._get_data())
        self.seen = time() #treat all messages as keep-alives
        if msglen != 0:
            self.set_terminator(msglen) #rest of message
            self.state = _State.Message

    def _get_message(self):
        data = self._get_data()
        msgid = ord(data[0])
        if msgid == 0: #choke
            if not self.peer_choking:
                self.torrent_downloader.update_choking_status(False)
            self.peer_choking = True
            self.torrent_downloader.ui.update_log('choked')
            self.n_requests_in_flight = 0
        if msgid == 1: #unchoke
            if self.peer_choking:
                self.torrent_downloader.update_choking_status(True)
            self.peer_choking = False
            self.torrent_downloader.ui.update_log( 'unchoked')
        if msgid == 2: #interested
            self.peer_interested = True
            self.torrent_downloader.interest_state(self)
            self.torrent_downloader.ui.update_log( 'interested')
        if msgid == 3: #uninstrested
            self.peer_interested = False
            self.torrent_downloader.interest_state(self)
            self.torrent_downloader.ui.update_log( 'uninterested')
        if msgid == 4: #have
            index, = struct.unpack('>L', data[1:])
            self.bitfield[index] = True
            self.torrent_downloader.ui.update_log('have ' + str(index) + ' for ' + str(self.bitfield.count()))
        if msgid == 5: #bitfield
            if len(data[1:]) != bits2bytes(len(self.bitfield)): #wrong length
                self.close_when_done()
                return
            self.bitfield = bitarray('')
            self.bitfield.frombytes(data[1:])
            self.bitfield = self.bitfield[:len(self.fileinfo.pieces)]
            self.torrent_downloader.ui.update_log( 'bitfield, has ' + str(self.bitfield.count()))
        if msgid == 6: #request
            if not self.am_choking:
                req = struct.unpack('>LLL', data[1:13])
                self.torrent_downloader.ui.update_log( 'request for piece' + repr(req))
                self.torrent_downloader.got_request(self, req)
        if msgid == 7: #piece
            block = data[9:]
            index, begin = struct.unpack('>LL', data[1:9])
            self.n_requests_in_flight -= 1
            #self.torrent_downloader.ui.update_log( 'got block for piece ' +  repr(index) + ' at ' + str(begin))
            self.torrent_downloader.got_piece(index,begin,block)
        if msgid == 8: #cancel
            self.torrent_downloader.ui.update_log( 'cancel ' + repr(struct.unpack('>LLL', data[1:13])))
            #DK how to i get rid of individual items from a queue?
        if msgid == 9: #dht port
            pass

    def choke(self, state):
        if self.am_choking == state:
            return #reduce chatter
        self.am_choking = state
        if state:
            self.message(0) #choke
            try:
                while True: #dump all pending requests on choke per spec
                    self.requests.task_done()
            except ValueError:
                pass
        else:
            self.message(1) #unchoke

    def interest(self, state):
        if self.am_interested == state:
            return #reduce chatter
        self.am_interested = state
        self.torrent_downloader.ui.update_log(('is' if state else 'not') + ' interested')
        if state:
            self.message(2) #interested
        else:
            self.message(3) #uninterested

    def have(self, piece):
        if not self.bitfield[piece]: #don't send HAVE unless they might want it
            self.torrent_downloader.ui.update_log( 'have for ' + str(piece) + ' to ' + repr(self))
            self.message(4, 'L', piece)

    def bitfield(self, bitfield):
        self.message(5, 'L', self.bitfield) 

    def request(self, piece, begin, length):
        #self.torrent_downloader.ui.update_log( 'sent request for ' + str(piece) + ' at ' + str(begin))
        self.n_requests_in_flight += 1
        self.message(6, 'LLL', piece, begin, length)

    def piece(self, index, begin, block):
        self.message(7, 'LL' + str(len(block)) + 's', index, begin, block)

    def cancel(self, piece, begin, length):
        self.message(8, 'LLL', piece, begin, length)
