import socket
import threading
import time
import datetime
import os
from pathlib import Path
import shutil
from messageHandler import MessageHandler, Message
from bitfieldManager import BitfieldManager
from chokingHandler import ChokingHandler

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
    def __init__(self, peer_id, host, port, has_file, otherPeerInfo, file_name, file_size, piece_size, num_preferred_neighbors, unchoking_interval, optimistic_unchoking_interval):

        self.peer_id = peer_id
        self.host = host
        self.port = port
        self.has_file = has_file
        self.otherPeerInfo = otherPeerInfo
        self.PeersConnections = {}
        
        # Neighbor state tracking for choking decisions
        self.neighbor_states = {}  # peer_id -> {interested: bool, choked: bool, download_rate: float, bytes_received: int, last_rate_calc: time, bitfield: BitfieldManager, pending_requests: set}
        self.download_start_time = time.time()
        
        self.msgHandler = MessageHandler(self)
        self.peer_dir = f"../peer_{self.peer_id}"
        os.makedirs(self.peer_dir, exist_ok=True)
        if has_file == 1:
            # locate repository root robustly and copy `thefile` into the peer directory
            src_file = Path(__file__).resolve().parents[2] / file_name
            dest_file = Path(self.peer_dir) / file_name
            try:
                shutil.copyfile(src_file, dest_file)
                # print(f"Peer {self.peer_id}: copied {src_file} -> {dest_file}")
            except FileNotFoundError:
                # print(f"Peer {self.peer_id}: source file not found at {src_file}")
                pass
            except Exception as e:
                # print(f"Peer {self.peer_id}: failed to copy file - {e}")
                pass
        
        self.bitfield = BitfieldManager(total_size=file_size, piece_size=piece_size, peer_dir=self.peer_dir, has_complete=(has_file == 1))
        
        # Initialize choking handler
        self.choking_handler = ChokingHandler(
            peer=self,
            num_preferred_neighbors=num_preferred_neighbors,
            unchoking_interval=unchoking_interval,
            optimistic_unchoking_interval=optimistic_unchoking_interval
        )

        # --- NEW: global "we're done" flag ---
        self.shutdown_event = threading.Event()

    def createServerSocket(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        
        # print("Peer {} Server socket created and listening on {}:{}".format(self.peer_id, self.host, self.port))

        while not self.shutdown_event.is_set():
            try:
                server_socket.settimeout(1.0)  # Set timeout to check shutdown periodically
                client_socket, addr = server_socket.accept()
                self.handleIncomingHandshake(client_socket)

                # Writing log logic
                # peer accepts a TCP connection from other peer (peer is connected from peer))
                otherPeerId = next((pid for pid, socket in self.PeersConnections.items() if socket == client_socket), None)
                with open("../log_peer_{}.log".format(self.peer_id), "a") as log_file:
                    log_file.write("{}: Peer {} is connected from Peer {}\n".format(datetime.datetime.now().strftime("%c"), self.peer_id, otherPeerId)) # need access to other peer id

                # Always send bitfield message to allow other peer to determine interest
                bitfield_bytes = self.bitfield.to_bytes()
                # print(f"Peer {self.peer_id}: Sending bitfield to Peer {otherPeerId} ({len(bitfield_bytes)} bytes, has_file={self.has_file})")
                self.msgHandler.sendMessage(client_socket, Message(5, bitfield_bytes), otherPeerId)

                #messaging
                threading.Thread(target=self.msgHandler.handleIncomingMessages, args=(client_socket, otherPeerId)).start()
            except socket.timeout:
                # Timeout is expected - just continue to check shutdown
                continue
            except Exception as e:
                # If shutdown is set, break out
                if self.shutdown_event.is_set():
                    break
                # print(f"Peer {self.peer_id}: Server socket error: {e}")
        
        # Close server socket when shutting down
        print(f"Peer {self.peer_id}: Server socket shutting down")
        server_socket.close()
            
    def connectToPeer(self):
        for otherPeerId, (otherPeerHost, otherPeerPort, otherPeerHasFile) in self.otherPeerInfo.items():
            if otherPeerId < self.peer_id:
                try:
                    # print("Peer {}: Attempting to connect to peer {} at {}:{}".format(self.peer_id, otherPeerId, otherPeerHost, otherPeerPort))
                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client_socket.connect((otherPeerHost, otherPeerPort))
                    sendHandshake(client_socket, self.peer_id)
                    receivedPeerId = receiveHandshake(client_socket)
                    # print("Peer {}: Handshake successful with peer {}".format(self.peer_id, receivedPeerId))
                    self.PeersConnections[receivedPeerId] = client_socket
                    self.initializeNeighborState(receivedPeerId)

                    # Writing log logic
                    # peer makes a TCP connection to other peer
                    with open("../log_peer_{}.log".format(self.peer_id), "a") as log_file:
                        log_file.write("{}: Peer {} makes a connection to Peer {}\n".format(datetime.datetime.now().strftime("%c"), self.peer_id, otherPeerId))

                    # Always send bitfield message to allow other peer to determine interest
                    bitfield_bytes = self.bitfield.to_bytes()
                    # print(f"Peer {self.peer_id}: Sending bitfield to Peer {otherPeerId} ({len(bitfield_bytes)} bytes, has_file={self.has_file})")
                    self.msgHandler.sendMessage(client_socket, Message(5, bitfield_bytes), otherPeerId)

                    threading.Thread(target=self.msgHandler.handleIncomingMessages, args=(client_socket, otherPeerId)).start()

                except Exception as e:
                    # print("Peer {}: Failed to connect to peer {} at {}:{} - {}".format(self.peer_id, otherPeerId, otherPeerHost, otherPeerPort, e))
                    pass
        
    def initializeNeighborState(self, peer_id):
        self.neighbor_states[peer_id] = {
            'interested': False,
            'choked': True,  # Start with peer choked
            'download_rate': 0.0,
            'bytes_received': 0,
            'last_rate_calc': time.time(),
            'bitfield': None,  # Store their bitfield
            'pending_requests': set()  # Track piece indices we've requested from this peer
        }
        # print(f"Peer {self.peer_id}: Initialized neighbor state for Peer {peer_id} (choked=True, interested=False)")
    
    def updateDownloadRate(self, peer_id, bytes_received):
        if peer_id not in self.neighbor_states:
            return
        
        current_time = time.time()
        state = self.neighbor_states[peer_id]
        state['bytes_received'] += bytes_received
        
        # Calculate rate based on time since last calculation
        time_elapsed = current_time - state['last_rate_calc']
        if time_elapsed > 0:
            state['download_rate'] = state['bytes_received'] / time_elapsed
            state['last_rate_calc'] = current_time
            # print(f"Peer {self.peer_id}: Updated download rate for Peer {peer_id} - {state['download_rate']:.0f} bytes/s (total: {state['bytes_received']} bytes)")
    
    def getInterestedNeighbors(self):
        return [peer_id for peer_id, state in self.neighbor_states.items() if state['interested']]

    def check_all_peers_complete(self):
        # We must have the complete file
        if self.bitfield.missing():
            return False

        # Check each other peer's bitfield
        for pid in self.otherPeerInfo.keys():
            if pid == self.peer_id:
                continue

            state = self.neighbor_states.get(pid)
            if not state:
                return False

            bf = state.get('bitfield')
            if bf is None:
                return False

            if bf.missing():  # they are still missing some pieces
                return False

        return True
    
    def selectPieceToRequest(self, peer_id):
        import random
        
        if peer_id not in self.neighbor_states:
            return None
        
        state = self.neighbor_states[peer_id]
        if state['bitfield'] is None:
            return None
        
        # Get pieces we need
        our_missing = self.bitfield.missing()
        if not our_missing:
            return None  # We have everything
        
        # Get pieces they have that we need and haven't requested yet
        # Check all pending requests across all peers to avoid duplicate requests
        all_pending = set()
        for pid, pstate in self.neighbor_states.items():
            all_pending.update(pstate['pending_requests'])
        
        available_pieces = []
        for piece_index in our_missing:
            if state['bitfield'].has(piece_index) and piece_index not in all_pending:
                available_pieces.append(piece_index)
        
        if not available_pieces:
            return None
        
        # Select randomly
        return random.choice(available_pieces)
    
    def readPiece(self, piece_index):
        # Find the file in peer directory
        import os
        file_list = [f for f in os.listdir(self.peer_dir) if os.path.isfile(os.path.join(self.peer_dir, f)) and not f.endswith('.log')]
        if not file_list:
            raise FileNotFoundError(f"No file found in {self.peer_dir}")
        
        file_path = Path(self.peer_dir) / file_list[0]
        
        offset = piece_index * self.bitfield.piece_size
        piece_size = self.bitfield.piece_size
        
        # Last piece might be smaller
        if piece_index == self.bitfield.num_pieces - 1:
            remaining = self.bitfield.total_size - offset
            piece_size = min(piece_size, remaining)
        
        with open(file_path, 'rb') as f:
            f.seek(offset)
            return f.read(piece_size)
    
    def writePiece(self, piece_index, data):
        file_path = Path(self.peer_dir) / 'thefile'  # Default filename
        
        offset = piece_index * self.bitfield.piece_size
        
        # Create/open file in read-write binary mode
        with open(file_path, 'r+b' if file_path.exists() else 'wb') as f:
            # Ensure file is large enough
            f.seek(0, 2)  # Seek to end
            current_size = f.tell()
            if current_size < self.bitfield.total_size:
                f.seek(self.bitfield.total_size - 1)
                f.write(b'\0')
            
            # Write the piece
            f.seek(offset)
            f.write(data)
    
    def startPeer(self):
        server_thread = threading.Thread(target=self.createServerSocket)
        server_thread.daemon = True
        server_thread.start()

        time.sleep(1)  # Give the server a moment to start

        self.connectToPeer()
        
        # Start choking cycle threads
        # print(f"Peer {self.peer_id}: Starting choking handler (preferred={self.choking_handler.num_preferred_neighbors}, interval={self.choking_handler.unchoking_interval}s, optimistic_interval={self.choking_handler.optimistic_unchoking_interval}s)")
        choking_thread = threading.Thread(target=self.choking_handler.run_choking_cycle)
        choking_thread.daemon = True
        choking_thread.start()

        # --- NEW: main shutdown loop ---
        while not self.shutdown_event.is_set():
            time.sleep(5)  # Check every 5 seconds

            if self.check_all_peers_complete():
                print(f"Peer {self.peer_id}: All peers have completed downloading. Beginning shutdown.")
                self.shutdown_event.set()

        # Close all connections once shutdown is signaled
        for peer_id, socket_conn in list(self.PeersConnections.items()):
            try:
                socket_conn.close()
                print(f"Peer {self.peer_id}: Closed connection to Peer {peer_id}")
            except Exception:
                pass

        print(f"Peer {self.peer_id}: Termination complete.")

    def handleIncomingHandshake(self, client_socket):
        try:
            receivedPeerId = receiveHandshake(client_socket)
            # print("Peer {}: Handshake received from peer {}".format(self.peer_id, receivedPeerId))
            sendHandshake(client_socket, self.peer_id)
            # print("Peer {}: Handshake response sent to peer {}".format(self.peer_id, receivedPeerId))
            self.PeersConnections[receivedPeerId] = client_socket
            self.initializeNeighborState(receivedPeerId)
        except Exception as e:
            # print("Peer {}: Handshake failed - {}".format(self.peer_id, e))
            pass