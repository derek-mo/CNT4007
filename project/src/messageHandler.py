import datetime

class Message:
    def __init__(self, msg_type, payload=b''):
        self.msg_type = msg_type
        self.payload = payload
        self.length = len(payload) + 1  # +1 for the message type byte

    def encode(self):
        length_bytes = self.length.to_bytes(4, byteorder='big')
        msg_type_byte = self.msg_type.to_bytes(1, byteorder='big')
        return length_bytes + msg_type_byte + self.payload

    @staticmethod
    def decode(data):
        length = int.from_bytes(data[:4], byteorder='big')
        msg_type = data[4]
        payload = data[5:5 + length - 1]  # -1 for the message type byte
        return Message(msg_type, payload)
    
class MessageHandler:
    def __init__(self, peer): # essentially who are we handling the message for
        self.peer = peer

    def sendMessage(self, socket_connected, msg, peer_receiving_msg):
        try:
            encoded_msg = msg.encode()
            socket_connected.sendall(encoded_msg)
            print(f"Peer {self.peer.peer_id}: Sent message type {msg.msg_type} with payload: {msg.payload} to Peer {peer_receiving_msg}")
        except Exception as e:
            print(f"Peer {self.peer.peer_id}: Error sending message - {e}")
    
    def receiveMessage(self, socket_connected, peer_sending_msg):
        try:
            length_bytes = socket_connected.recv(4)
            if not length_bytes:
                return None
            length = int.from_bytes(length_bytes, byteorder='big')
            msg_data = socket_connected.recv(length)
            full_data = length_bytes + msg_data
            msg = Message.decode(full_data)
            print(f"Peer {self.peer.peer_id}: Received message type {msg.msg_type} with payload: {msg.payload} from Peer {peer_sending_msg}")
            return msg
        except Exception as e:
            print(f"Peer {self.peer.peer_id}: Error receiving message - {e}")
            return None
        
        
    def handleIncomingMessages(self, socket_connected, peer_sending_msg):
        while True:
            msg = self.receiveMessage(socket_connected, peer_sending_msg)
            if msg is None:
                print(f"Peer {self.peer.peer_id}: Connection closed by Peer {peer_sending_msg}")
                break
            # Message type logic
            # Each message type needs logic implemented. If there a log file write then implement logic above.
            if msg.msg_type == 0:  # Choke
                with open("../log_peer_{}.log".format(self.peer.peer_id), "a") as log_file:
                        log_file.write("{}: Peer {} is choked by Peer {}\n".format(datetime.datetime.now().strftime("%c"), self.peer.peer_id, peer_sending_msg))

            elif msg.msg_type == 1:  # Unchoke
                # We've been unchoked, request a piece if available
                piece_index = self.peer.selectPieceToRequest(peer_sending_msg)
                if piece_index is not None:
                    # Mark as pending request
                    self.peer.neighbor_states[peer_sending_msg]['pending_requests'].add(piece_index)
                    # Send request message with piece index (4 bytes)
                    request_payload = piece_index.to_bytes(4, byteorder='big')
                    self.sendMessage(socket_connected, Message(6, request_payload), peer_sending_msg)
                    print(f"Peer {self.peer.peer_id}: Requesting piece {piece_index} from Peer {peer_sending_msg}")
                else:
                    print(f"Peer {self.peer.peer_id}: Unchoked by Peer {peer_sending_msg} but no pieces to request")
                
                with open("../log_peer_{}.log".format(self.peer.peer_id), "a") as log_file:
                        log_file.write("{}: Peer {} is unchoked by Peer {}\n".format(datetime.datetime.now().strftime("%c"), self.peer.peer_id, peer_sending_msg))

            elif msg.msg_type == 2:  # Interested
                # Update neighbor state to mark them as interested
                if peer_sending_msg in self.peer.neighbor_states:
                    self.peer.neighbor_states[peer_sending_msg]['interested'] = True
                    print(f"Peer {self.peer.peer_id}: Peer {peer_sending_msg} is now INTERESTED")
                
                with open("../log_peer_{}.log".format(self.peer.peer_id), "a") as log_file:
                        log_file.write("{}: Peer {} received the 'interested' message from Peer {}\n".format(datetime.datetime.now().strftime("%c"), self.peer.peer_id, peer_sending_msg))

            elif msg.msg_type == 3:  # Not Interested
                # Update neighbor state to mark them as not interested
                if peer_sending_msg in self.peer.neighbor_states:
                    self.peer.neighbor_states[peer_sending_msg]['interested'] = False
                    print(f"Peer {self.peer.peer_id}: Peer {peer_sending_msg} is now NOT INTERESTED")
                
                with open("../log_peer_{}.log".format(self.peer.peer_id), "a") as log_file:
                        log_file.write("{}: Peer {} received the 'uninterested' message from Peer {}\n".format(datetime.datetime.now().strftime("%c"), self.peer.peer_id, peer_sending_msg))

            elif msg.msg_type == 4:  # Have
                # Peer is notifying us they have a new piece
                if len(msg.payload) < 4:
                    print(f"Peer {self.peer.peer_id}: Invalid have message from Peer {peer_sending_msg}")
                    continue
                
                piece_index = int.from_bytes(msg.payload[:4], byteorder='big')
                print(f"Peer {self.peer.peer_id}: Peer {peer_sending_msg} now has piece {piece_index}")
                
                # Update their bitfield if we're tracking it
                if peer_sending_msg in self.peer.neighbor_states:
                    neighbor_state = self.peer.neighbor_states[peer_sending_msg]
                    if neighbor_state['bitfield'] is not None:
                        try:
                            neighbor_state['bitfield'].mark_have(piece_index)
                            
                            # Check if WE should become interested in THEM
                            # (because they now have a piece we need)
                            if not self.peer.bitfield.has(piece_index):
                                # They have a piece we don't have WE send interested to THEM
                                self.sendMessage(socket_connected, Message(2, b''), peer_sending_msg)
                                print(f"Peer {self.peer.peer_id}: Sending INTERESTED to Peer {peer_sending_msg} (they have piece {piece_index} that we need)")
                            
                        except Exception as e:
                            print(f"Peer {self.peer.peer_id}: Error updating bitfield for Peer {peer_sending_msg} - {e}")
                
                with open("../log_peer_{}.log".format(self.peer.peer_id), "a") as log_file:
                        log_file.write("{}: Peer {} received the 'have' message from Peer {} for the piece {}.\n".format(datetime.datetime.now().strftime("%c"), self.peer.peer_id, peer_sending_msg, piece_index))
            
            elif msg.msg_type == 5:  # Bitfield
                # Parse the received bitfield
                print(f"Peer {self.peer.peer_id}: Received bitfield from Peer {peer_sending_msg} ({len(msg.payload)} bytes)")
                
                # Store their bitfield 
                # For now, compare with our bitfield to determine if we're interested
                try:
                    # Create a temporary bitfield manager to parse their bitfield
                    from bitfieldManager import BitfieldManager
                    their_bitfield = BitfieldManager(
                        total_size=self.peer.bitfield.total_size,
                        piece_size=self.peer.bitfield.piece_size,
                        peer_dir=None,
                        has_complete=False
                    )
                    their_bitfield.from_bytes(msg.payload)
                    
                    # Store their bitfield for later piece selection
                    if peer_sending_msg in self.peer.neighbor_states:
                        self.peer.neighbor_states[peer_sending_msg]['bitfield'] = their_bitfield
                    
                    # Check if they have anything we need
                    we_are_interested = False
                    our_missing = self.peer.bitfield.missing()
                    
                    if our_missing:  # If we're missing pieces
                        for piece_index in our_missing:
                            if their_bitfield.has(piece_index):
                                we_are_interested = True
                                break
                    
                    # Send interested or not interested message
                    if we_are_interested:
                        print(f"Peer {self.peer.peer_id}: Peer {peer_sending_msg} has pieces we need - sending INTERESTED")
                        self.sendMessage(socket_connected, Message(2, b''), peer_sending_msg)
                    else:
                        print(f"Peer {self.peer.peer_id}: Peer {peer_sending_msg} has no pieces we need - sending NOT INTERESTED")
                        self.sendMessage(socket_connected, Message(3, b''), peer_sending_msg)
                
                except Exception as e:
                    print(f"Peer {self.peer.peer_id}: Error processing bitfield from Peer {peer_sending_msg} - {e}")
                

            elif msg.msg_type == 6:  # Request
                # Peer is requesting a piece from us
                if len(msg.payload) < 4:
                    print(f"Peer {self.peer.peer_id}: Invalid request message from Peer {peer_sending_msg}")
                    continue
                
                piece_index = int.from_bytes(msg.payload[:4], byteorder='big')
                print(f"Peer {self.peer.peer_id}: Received request for piece {piece_index} from Peer {peer_sending_msg}")
                
                # Check if they are choked
                if peer_sending_msg in self.peer.neighbor_states:
                    if self.peer.neighbor_states[peer_sending_msg]['choked']:
                        print(f"Peer {self.peer.peer_id}: Peer {peer_sending_msg} is choked, ignoring request")
                        continue
                
                # Check if we have the piece
                if not self.peer.bitfield.has(piece_index):
                    print(f"Peer {self.peer.peer_id}: Don't have piece {piece_index} requested by Peer {peer_sending_msg}")
                    continue
                
                # Read the piece from file and send it
                try:
                    piece_data = self.peer.readPiece(piece_index)
                    # Piece message: 4 bytes index + piece data
                    piece_payload = piece_index.to_bytes(4, byteorder='big') + piece_data
                    self.sendMessage(socket_connected, Message(7, piece_payload), peer_sending_msg)
                    print(f"Peer {self.peer.peer_id}: Sent piece {piece_index} ({len(piece_data)} bytes) to Peer {peer_sending_msg}")
                except Exception as e:
                    print(f"Peer {self.peer.peer_id}: Error sending piece {piece_index} to Peer {peer_sending_msg} - {e}")

            elif msg.msg_type == 7:  # Piece
                # Received a piece
                if len(msg.payload) < 4:
                    print(f"Peer {self.peer.peer_id}: Invalid piece message from Peer {peer_sending_msg}")
                    continue
                
                piece_index = int.from_bytes(msg.payload[:4], byteorder='big')
                piece_data = msg.payload[4:]
                
                print(f"Peer {self.peer.peer_id}: Received piece {piece_index} ({len(piece_data)} bytes) from Peer {peer_sending_msg}")
                
                # Remove from pending requests
                if peer_sending_msg in self.peer.neighbor_states:
                    self.peer.neighbor_states[peer_sending_msg]['pending_requests'].discard(piece_index)
                    # Update download rate
                    self.peer.updateDownloadRate(peer_sending_msg, len(piece_data))
                
                # Save the piece
                try:
                    self.peer.writePiece(piece_index, piece_data)
                    self.peer.bitfield.mark_have(piece_index)
                    print(f"Peer {self.peer.peer_id}: Successfully saved piece {piece_index}")
                    
                    # Log download completion for this piece
                    num_pieces = self.peer.bitfield.num_pieces
                    pieces_downloaded = num_pieces - len(self.peer.bitfield.missing())
                    with open(f"../log_peer_{self.peer.peer_id}.log", "a") as log_file:
                        log_file.write(f"{datetime.datetime.now().strftime('%c')}: Peer {self.peer.peer_id} has downloaded the piece {piece_index} from Peer {peer_sending_msg}. Now the number of pieces it has is {pieces_downloaded}.\n")
                    
                    # Send 'have' message to all other connected peers
                    have_payload = piece_index.to_bytes(4, byteorder='big')
                    for other_peer_id, other_socket in self.peer.PeersConnections.items():
                        if other_peer_id != peer_sending_msg:
                            self.sendMessage(other_socket, Message(4, have_payload), other_peer_id)
                    
                    # Check if download is complete
                    if not self.peer.bitfield.missing():
                        print(f"Peer {self.peer.peer_id}: Download complete!")
                        with open(f"../log_peer_{self.peer.peer_id}.log", "a") as log_file:
                            log_file.write(f"{datetime.datetime.now().strftime('%c')}: Peer {self.peer.peer_id} has downloaded the complete file.\n")
                    else:
                        # Request another piece from the same peer if available
                        next_piece = self.peer.selectPieceToRequest(peer_sending_msg)
                        if next_piece is not None:
                            self.peer.neighbor_states[peer_sending_msg]['pending_requests'].add(next_piece)
                            request_payload = next_piece.to_bytes(4, byteorder='big')
                            self.sendMessage(socket_connected, Message(6, request_payload), peer_sending_msg)
                            print(f"Peer {self.peer.peer_id}: Requesting next piece {next_piece} from Peer {peer_sending_msg}")
                        else:
                            print(f"Peer {self.peer.peer_id}: No more pieces to request from Peer {peer_sending_msg}")
                
                except Exception as e:
                    print(f"Peer {self.peer.peer_id}: Error saving piece {piece_index} - {e}")
                
            else:
                print(f"Peer {self.peer.peer_id}: Unknown message type {msg.msg_type} from Peer {peer_sending_msg}")