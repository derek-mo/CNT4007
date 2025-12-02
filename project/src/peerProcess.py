from peers import PeerClass
import sys
from messageHandler import Message

def readPeerInfo():
    peers = {}
    with open("../PeerInfo.cfg", 'r') as peer_info:
        for line in peer_info:
            id, host, port, hasFile = line.strip().split(' ')
            peers[int(id)] = (host, int(port), int(hasFile))
    return peers

def readCommonInfo():
    with open("../Common.cfg", 'r') as common_info:
        lines = common_info.readlines()
        preferredNeighbors = int(lines[0].strip().split(' ')[1])
        UnchockingInterval = int(lines[1].strip().split(' ')[1])
        OptimisticUnchokingInterval = int(lines[2].strip().split(' ')[1])
        FileName = lines[3].strip().split(' ')[1]
        FileSize = int(lines[4].strip().split(' ')[1])
        PieceSize = int(lines[5].strip().split(' ')[1])
        return (preferredNeighbors, UnchockingInterval, OptimisticUnchokingInterval, FileName, FileSize, PieceSize)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Please use this in terminal: python peerProcess.py <peer_id>")
        sys.exit(1)

    peerId = int(sys.argv[1])
    commonInfo = readCommonInfo()
    peerInfo = readPeerInfo()
    host, port, hasFile = peerInfo[peerId]
    peer = PeerClass(peerId, host, port, hasFile, peerInfo, commonInfo[3], commonInfo[4], commonInfo[5])
    peer.startPeer()
