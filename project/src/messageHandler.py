

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
    def __init__(self, peerId):
        self.peerId = peerId

    def sendMessage(self, connectedSocket, msg):
        try:
            encoded_msg = msg.encode()
            connectedSocket.sendall(encoded_msg)
            print(f"Peer {self.peerId}: Sent message type {msg.msg_type} with payload: {msg.payload}")
        except Exception as e:
            print(f"Peer {self.peerId}: Error sending message - {e}")
    
    def receiveMessage(self, connectedSocket):
        try:
            length_bytes = connectedSocket.recv(4)
            if not length_bytes:
                return None
            length = int.from_bytes(length_bytes, byteorder='big')
            msg_type_byte = connectedSocket.recv(1)
            payload = connectedSocket.recv(length - 1)  # -1 for the message type byte
            msg = Message.decode(length_bytes + msg_type_byte + payload)
            print(f"Peer {self.peerId}: Received message type {msg.msg_type} with payload: {msg.payload}")
            return msg
        except Exception as e:
            print(f"Peer {self.peerId}: Error receiving message - {e}")
            return None
        
    def handleIncomingMessages(self, connectedSocket):
        while True:
            msg = self.receiveMessage(connectedSocket)
            if msg is None:
                break
            # Process the message based on its type
            if msg.msg_type == 0:
                self.sendMessage(connectedSocket, Message(1, b'Acknowledged, choked message'))  # Example response
            elif msg.msg_type == 1:
                self.sendMessage(connectedSocket, Message(2, b'Acknowledged, unchoked message'))  # Example response
            elif msg.msg_type == 2:
                self.sendMessage(connectedSocket, Message(2, b'Acknowledged, interested message'))  # Example response
            elif msg.msg_type == 3:
                self.sendMessage(connectedSocket, Message(2, b'Acknowledged, not interested message'))  # Example response
            elif msg.msg_type == 4:
                self.sendMessage(connectedSocket, Message(2, b'Acknowledged, have message'))  # Example response
            elif msg.msg_type == 5:
                self.sendMessage(connectedSocket, Message(2, b'Acknowledged, bitfield message'))  # Example response
            elif msg.msg_type == 6:
                self.sendMessage(connectedSocket, Message(2, b'Acknowledged, request message'))  # Example response
            elif msg.msg_type == 7:
                self.sendMessage(connectedSocket, Message(2, b'Acknowledged, piece message'))  # Example response
            else:
                print(f"Peer {self.peerId}: Unknown message type {msg.msg_type}")