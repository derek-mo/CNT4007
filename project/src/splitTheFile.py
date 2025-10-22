import os
import math

#Read peer info config file to get the host, port, and initial file possetion status
def readPeerInfo():
    peers = {}
    with open("../PeerInfo.cfg", 'r') as peer_info:
        for line in peer_info:
            id, host, port, hasFile = line.strip().split(' ')
            peers[int(id)] = (host, int(port), int(hasFile))
    return peers

#Read common info config file to get general settings for the communication, choaking, and splitting procedures
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

def splitTheFiles():
    #Extract config information
    common_info = readCommonInfo()
    peer_info = readPeerInfo()

    #Define relevant variables for splitting
    piece_size = common_info[5]
    file_size = common_info[4]
    file_name = common_info[3]

    #Calculate expected number of splits
    num_pieces = math.ceil(file_size / piece_size)

    #Identify peers who have the file and where they are at
    locations_to_split = []
    for peer_id in peer_info:
        if peer_info[peer_id][2] == 1:
            locations_to_split.append(f"../peer_{peer_id}/{file_name}")

    #At each file location, go split up the file
    for location in locations_to_split:
        split_up_pieces = [] #Stores pieces as we grab them, will use to write to piece split files

        # Extract all the pieces
        with open(location, 'rb') as f:
            for i in range(num_pieces):
                piece = f.read(piece_size) #This grabs the data in the file at the current location of the pointer
                                            #note that f.read() automatically deals with chunks that are smaller
                                            #than the full_piece size, if we are at the end it will just give what is
                                            #there and no more
                split_up_pieces.append((i, piece)) #Store piece alongside the index for naming purposes of piece file

        # Write them back into the folder for other peers to be able to see
        for index_piece_pair in split_up_pieces:
            path_start = location.rsplit('/', 1)[0]
            piece_file_name =  f"{path_start}/piece_{index_piece_pair[0]}"

            with open(piece_file_name, "wb") as pf:
                pf.write(index_piece_pair[1]) # Write the data to the file we create for each piece

if __name__ == "__main__":
    splitTheFiles()
