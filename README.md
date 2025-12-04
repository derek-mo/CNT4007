# CNT4007 Computer Network Fundaments: P2P Project

## Group 41 Members

### Brando Santana

### Edward Kempa

### Derek Mo

## Team Member Contributions

**Brando Santana**

1. Peer Connection Logic
2. Message Logic
3. Request and Piece Logic
4. Choke/Unchoke Logic
5. Testing and Debugging

**Edward Kempa**

1. Choke/Unchoke Logic
2. Peer Termination Logic
3. Testing and Debugging

**Derek Mo**

1. Bitfield Logic
2. Testing and Debugging
3. Documentation

## Completed Work

* Read Common.cfg and PeerInfo.cfg configuration files
* TCP Connection and handshake with other peers
* Sending all message types
* Update peer bitfields to determine next request
* Requests and sends pieces of the file based on bitfield
* Choke/Unchoke logic and optimistically unchoked logic
* Interested/Not Interested logic
* Termination after all peers finish downloads

## How to Run

1. Ensure PeerInfo.cfg and Common.cfg are in the ***project*** directory.
2. Place the file to be shared in the ***root*** directory.
3. Open the terminal and ensure you are in the ***src*** directory (***cd project/src***).
4. run ***python peerProcess.py [peerID]***.
5. Repeat Step 4 for the number of peers.
6. The program will only terminate once the expected number of peers have connected and finished downloading the file.
