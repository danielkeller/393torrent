import asyncore, asynchat
import socket
import struct

class _State:
    (PreHandshake, Handshake, PreMessage, Message) = range(0, 4)

class PeerServer(asyncore.dispatcher):
    
    def __init__(self, port):
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
            conn = PeerConn(sock=sock)

class PeerConn(asynchat.async_chat):

    def __init__(self, sock=None, host=None):
        if sock is None:
            asynchat.async_chat.__init__(self)
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connect( (host, 6880) )
        else:
            asynchat.async_chat.__init__(self, sock=sock)
        self.set_terminator(1) #handshake is length-prefixed with one byte
        self.state = _State.PreHandshake
        self.am_choking = True
        self.am_interested = False
        self.peer_choking = True
        self.peer_interested = False
        self.push(struct.pack('>B19sq20s20s', 19, 'BitTorrent protocol', 0, 'test', 'test'))

    def collect_incoming_data(self, data):
        self._collect_incoming_data(data)

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
            msglen = struct.unpack('>L', self._get_data())
            if msglen == 0:
                pass # handle keep-alive
            else:
                self.set_terminator(msglen)
                self.state = _State.Message

        else:
            data = self._get_data()
            msgid = data[0]
            if msgid == '0': #choke
                self.peer_choking = True
            if msgid == '1': #unchoke
                self.peer_choking = False
            if msgid == '2': #interested
                self.peer_interested = True
            if msgid == '3': #uninstrested
                self.peer_interested = False

if __name__ == '__main__':
    server = PeerServer(6880)
    client = PeerConn(host='localhost')
    asyncore.loop()
