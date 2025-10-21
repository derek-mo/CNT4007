from peers import PeerClass
import sys


def readPeerInfo():
    peers = {}
    with open("../PeerInfo.cfg", 'r') as peer_info:
        for line in peer_info:
            id, host, port, hasFile = line.strip().split(' ')
            peers[int(id)] = (host, int(port), int(hasFile))
    return peers



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Please use this in terminal: python peerProcess.py <peer_id>")
        sys.exit(1)

    peerId = int(sys.argv[1])
    peerInfo = readPeerInfo()
    host, port, hasFile = peerInfo[peerId]
    peer = PeerClass(peerId, host, port, hasFile, peerInfo)
    peer.startPeer()
