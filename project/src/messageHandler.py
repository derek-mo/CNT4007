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
                self.sendMessage(socket_connected, Message(6, b'Requesting piece'), peer_sending_msg) # Example for now
                with open("../log_peer_{}.log".format(self.peer.peer_id), "a") as log_file:
                        log_file.write("{}: Peer {} is unchoked by Peer {}\n".format(datetime.datetime.now().strftime("%c"), self.peer.peer_id, peer_sending_msg))

            elif msg.msg_type == 2:  # Interested
                # Would need interested logic here deciding whether or not to choke/unchoke
                self.sendMessage(socket_connected, Message(1, b'Unchoking'), peer_sending_msg) # send unchoke message
                with open("../log_peer_{}.log".format(self.peer.peer_id), "a") as log_file:
                        log_file.write("{}: Peer {} received the 'interested' message from Peer {}\n".format(datetime.datetime.now().strftime("%c"), self.peer.peer_id, peer_sending_msg))

            elif msg.msg_type == 3:  # Not Interested
                with open("../log_peer_{}.log".format(self.peer.peer_id), "a") as log_file:
                        log_file.write("{}: Peer {} received the 'uninterested' message from Peer {}\n".format(datetime.datetime.now().strftime("%c"), self.peer.peer_id, peer_sending_msg))

            elif msg.msg_type == 4:  # Have
                with open("../log_peer_{}.log".format(self.peer.peer_id), "a") as log_file:
                        log_file.write("{}: Peer {} received the 'have' message from Peer {}\n".format(datetime.datetime.now().strftime("%c"), self.peer.peer_id, peer_sending_msg))
            
            elif msg.msg_type == 5:  # Bitfield
                # received bitfield message then send our bitfield back
                # temporary logic until bitfield calculation is implemented
                if self.peer.has_file == 0:
                    self.sendMessage(socket_connected, Message(5, b'\x00'), peer_sending_msg)  # Example bitfield message
                if self.peer.has_file == 1:
                    self.sendMessage(socket_connected, Message(5, b'\xFF'), peer_sending_msg)  # Example bitfield message
                

            elif msg.msg_type == 6:  # Request
                print(f"Peer {self.peer.peer_id}: Handling Request message from Peer {peer_sending_msg}")

            elif msg.msg_type == 7:  # Piece
                print(f"Peer {self.peer.peer_id}: Handling Piece message from Peer {peer_sending_msg}")
                
            else:
                print(f"Peer {self.peer.peer_id}: Unknown message type {msg.msg_type} from Peer {peer_sending_msg}")