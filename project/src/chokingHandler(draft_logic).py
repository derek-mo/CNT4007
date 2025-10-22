import random
import time

#Create a class to simulate information we would receive during connection with other peers
class SimulatedNeigborPeer:
    def __init__(self, peer_id, down_rate):
        self.peer_id = peer_id
        self.download_rate = down_rate
        self.is_interested = True
        self.choked = True

#This class will implement the chocking logic
class ChokingHandler:
    def __init__(self, neighbors, num_preferred_neighbors, unchoking_interval, optimistic_unchoking_interval):
        self.neighbors = neighbors
        self.num_preferred_neighbors = num_preferred_neighbors
        self.unchoking_interval = unchoking_interval #Each peer determines preferred neighbors every p seconds
        self.optimistic_unchoking_interval = optimistic_unchoking_interval #Each peer determines an optimistically

        #Track relationship of peers
        self.unchoked_neighbors = []                                                          # unchoked neighbor every m seconds
        self.interested_but_choked_neighbors = []
        self.optimistically_unchoked_id = None

        self.time_of_creation = time.time()

    def select_preferred_neighbors(self):
        pairs = [] #Stores all interested neighbors
        neighbors_to_unchoke = [] #Stores the id of peers selected to be unchoked
        choked_but_interested = [] #Stores the id of peers who are choked but interested

        #TODO: If peer A has a complete file, it determines preferred neighbors randomly among those
        # that are interested in its data rather than comparing downloading rates.

        #Determine who's still interested
        for peer in self.neighbors:
            if peer.is_interested: #Consider only those who are still interested
                pairs.append((peer.download_rate, peer.peer_id))

        #Select those with highest rates of download
        #TODO, the following could have errors if there are less intersted peers tha num_pref_neigh
        #TODO, tied rates should be broken randomly, i dont think current approach does this exactly
        for i in range(self.num_preferred_neighbors):
            neighbors_to_unchoke.append(sorted(pairs, reverse=True)[i][1]) #Grab the top three in reverse sorted order,
                                                                            # giving highest rates, and track their id

        #One output is that we update the list of currently unchoked neighbors in our handler
        self.unchoked_neighbors = neighbors_to_unchoke
        print(neighbors_to_unchoke) #For development

        #At the same time we want an updated list of neighbors who are still interested but choked
        for pair in pairs:
            if pair[1] not in neighbors_to_unchoke:
                choked_but_interested.append(pair[1])

        #Other output is a list of those interested but choked used next in optimistic unchoking
        self.interested_but_choked_neighbors = choked_but_interested
        print(choked_but_interested)  #For development

    def select_optimistically_unchoked(self):
        #First select the index in the list of choked but interested neighbors
        rand_index = random.randint(0,len(self.interested_but_choked_neighbors)-1)

        #Then extract that id from the list
        selected_id = self.interested_but_choked_neighbors[rand_index]

        #Save this to our class variable, used in the chocking_cycle
        self.optimistically_unchoked_id = selected_id
        print(selected_id)

    def run_choking_cycle(self):
        self.select_preferred_neighbors()
        #TODO: Then it unchokes those
        # preferred neighbors by sending ‘unchoke’ messages and it expects to receive ‘request’
        # messages from them. If a preferred neighbor is already unchoked, then peer A does not
        # have to send ‘unchoke’ message to it. All other neighbors previously unchoked but not
        # selected as preferred neighbors at this time should be choked unless it is an optimistically
        # unchoked neighbor. To choke those neighbors, peer A sends ‘choke’ messages to them
        # and stop sending pieces.

        self.select_optimistically_unchoked()
        #TODO: Then peer A sends ‘unchoke’ message to the selected neighbor and
        # it expects to receive ‘request’ messages from it.

if __name__ == "__main__":
    #Create some fake neighbors to test logic
    neighbor_1 = SimulatedNeigborPeer(1001, 6)
    neighbor_2 = SimulatedNeigborPeer(1002, 4)
    neighbor_3 = SimulatedNeigborPeer(1003, 9)
    neighbor_4 = SimulatedNeigborPeer(1004, 7)
    neighbor_5 = SimulatedNeigborPeer(1005, 2)

    neighbors = [neighbor_1, neighbor_2, neighbor_3, neighbor_4, neighbor_5]
    handler = ChokingHandler(neighbors, num_preferred_neighbors=3, unchoking_interval=5, optimistic_unchoking_interval=10) #Manually choose some for now
    handler.run_choking_cycle()
    # Still in progress