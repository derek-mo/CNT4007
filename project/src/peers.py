#class of peers
import socket
import threading
import time
import datetime

def sendHandshake(client_socket, peerId):
    header = b"P2PFILESHARINGPROJ"
    zeroBits = b"\x00" * 10
    peerIdBytes = str(peerId).zfill(4).encode()
    client_socket.sendall(header + zeroBits + peerIdBytes)

def receiveHandshake(client_socket):
    expected_header = b"P2PFILESHARINGPROJ"
    data = client_socket.recv(32)
    header = data[:18]
    if header != expected_header:
        raise ValueError("Invalid handshake header")
    peerIdBytes = data[28:]
    peerId = int(peerIdBytes.decode())
    return peerId

class PeerClass:
    def __init__(self, peer_id, host, port, has_file, otherPeerInfo):
        self.peer_id = peer_id
        self.host = host
        self.port = port
        self.has_file = has_file
        self.otherPeerInfo = otherPeerInfo
        self.PeersConnections = {}

    def createServerSocket(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        
        print("Peer {} Server socket created and listening on {}:{}".format(self.peer_id, self.host, self.port))

        while True:
            client_socket, addr = server_socket.accept()
            #threading.Thread(target=self.handleIncomingHandshake, args=(client_socket,)).start()
            print("Peer {}: Connection established with {}".format(self.peer_id, addr))
            self.handleIncomingHandshake(client_socket)
            # Writing log logic
            # peer accepts a TCP connection from other peer (peer is connected from peer))
            otherPeerId = next((pid for pid, socket in self.PeersConnections.items() if socket == client_socket), None)
            with open("../log_peer_{}.log".format(self.peer_id), "a") as log_file:
                log_file.write("{}: Peer {} accepted connection from {}\n".format(datetime.datetime.now().strftime("%c"), self.peer_id, otherPeerId)) # need access to other peer id
            

    def connectToPeer(self):
        for otherPeerId, (otherPeerHost, otherPeerPort, otherPeerHasFile) in self.otherPeerInfo.items():
            if otherPeerId < self.peer_id:
                try:
                    print("Peer {}: Attempting to connect to peer {} at {}:{}".format(self.peer_id, otherPeerId, otherPeerHost, otherPeerPort))
                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client_socket.connect((otherPeerHost, otherPeerPort))
                    sendHandshake(client_socket, self.peer_id)
                    receivedPeerId = receiveHandshake(client_socket)
                    print("Peer {}: Handshake successful with peer {}".format(self.peer_id, receivedPeerId))
                    self.PeersConnections[receivedPeerId] = client_socket
                    # Further communication logic would go here
                    # Writing log logic
                    # peer makes a TCP connection to other peer
                    with open("../log_peer_{}.log".format(self.peer_id), "a") as log_file:
                        log_file.write("{}: Peer {} made connection to peer {}\n".format(datetime.datetime.now().strftime("%c"), self.peer_id, otherPeerId))
                        
                except Exception as e:
                    print("Peer {}: Failed to connect to peer {} at {}:{} - {}".format(self.peer_id, otherPeerId, otherPeerHost, otherPeerPort, e))
        
    def startPeer(self):
        server_thread = threading.Thread(target=self.createServerSocket)
        server_thread.start()

        time.sleep(1)  # Give the server a moment to start

        self.connectToPeer()

        while True:
            time.sleep(10)  # Keep the main thread alive

    def handleIncomingHandshake(self, client_socket):
        try:
            receivedPeerId = receiveHandshake(client_socket)
            print("Peer {}: Handshake received from peer {}".format(self.peer_id, receivedPeerId))
            sendHandshake(client_socket, self.peer_id)
            print("Peer {}: Handshake response sent to peer {}".format(self.peer_id, receivedPeerId))
            self.PeersConnections[receivedPeerId] = client_socket
        except Exception as e:
            print("Peer {}: Handshake failed - {}".format(self.peer_id, e))


    
