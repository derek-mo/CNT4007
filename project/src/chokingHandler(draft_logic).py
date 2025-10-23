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
                                                                            # unchoked neighbor every m seconds

        #Track relationship of peers
        self.unchoked_neighbors = []
        self.interested_but_choked_neighbors = []
        self.optimistically_unchoked_id = None

        #Track if we now have the full file
        self.i_have_the_file = False

        #Keep track of the start time, will loop continously and keep selecting new neighbors
        self.time_of_creation = time.time()

    def select_preferred_neighbors(self):
        #TODO: Currently we aren't selecting from only the previously unchoked + optimistic, but all neighbors
        # need to modify this to only pick from people that were just unchoked in the last cycle

        pairs = [] #Stores all interested neighbors
        neighbors_to_unchoke = [] #Stores the id of peers selected to be unchoked
        choked_but_interested = [] #Stores the id of peers who are choked but interested

        # Determine who's still interested
        for peer in self.neighbors:
            if peer.is_interested:  # Consider only those who are still interested
                pairs.append((peer.download_rate, peer.peer_id))

        #If peer A has a complete file, it determines preferred neighbors randomly
        if self.i_have_the_file:
            random.shuffle(pairs)  # Shuffle order

        #If not, we want to prioritize peers with higher download rates, and break ties with random
        sorted_pairs = []

        if not self.i_have_the_file: #Just else
            while len(pairs) != 0:
                #Start by identifying the peer(s) with highest rate(s)
                highest_rate_or_tied = []
                highest_rate_or_tied.append(max(pairs))

                #Take that one out of consideration
                pairs.remove(max(pairs))

                #Now grab any other who have the same rate
                while len(pairs) > 0 and highest_rate_or_tied[0][0] == max(pairs)[0]:
                    highest_rate_or_tied.append(max(pairs))

                    # Take that one out of consideration
                    pairs.remove(max(pairs))

                #Once we have all the
                random.shuffle(highest_rate_or_tied)
                sorted_pairs += highest_rate_or_tied #Glue that list to the end of the bigger sorted list

            #Now we kinda deleted the original pairs, so we put in the sorted values
            pairs = sorted_pairs

        # Select those with highest rates of download
        # TODO, tied rates should be broken randomly, i dont think current approach does this exactly
        for i in range(min(self.num_preferred_neighbors, len(pairs))):
            neighbors_to_unchoke.append(pairs[i][1])  # Grab the top peers up to the num preferred neighbors


        # One output is that we update the list of currently unchoked neighbors in our handler
        self.unchoked_neighbors = neighbors_to_unchoke
        print(neighbors_to_unchoke)  # For development

        # At the same time we want an updated list of neighbors who are still interested but choked
        for pair in pairs:
            if pair[1] not in neighbors_to_unchoke:
                choked_but_interested.append(pair[1])

        # Other output is a list of those interested but choked used next in optimistic unchoking
        self.interested_but_choked_neighbors = choked_but_interested
        print(choked_but_interested)  # For development


    def select_optimistically_unchoked(self):
        #First select the index in the list of choked but interested neighbors
        rand_index = random.randint(0,len(self.interested_but_choked_neighbors)-1)

        #Then extract that id from the list
        selected_id = self.interested_but_choked_neighbors[rand_index]

        #Save this to our class variable, used in the chocking_cycle
        self.optimistically_unchoked_id = selected_id
        print(selected_id)

    def run_choking_cycle(self):

        #Initialize timestamps for choking
        choke_time = handler.time_of_creation + self.unchoking_interval
        optimistic_unchoke_time = handler.time_of_creation + self.optimistic_unchoking_interval

        while time.time() < handler.time_of_creation + 30:
            #Prints to see the flow of the code in real time
            print(f"time: {time.time() - self.time_of_creation}")
            print(f"choke time: {choke_time - self.time_of_creation}")
            print(f"op unchoke time: {optimistic_unchoke_time - self.time_of_creation}")

            #If the interval time passes
            if time.time() > choke_time:
                #Pick out new ids to unchoke
                new_unchoked_ids = self.select_preferred_neighbors()

                #TODO: Then it unchokes those
                # preferred neighbors by sending ‘unchoke’ messages and it expects to receive ‘request’
                # messages from them. If a preferred neighbor is already unchoked, then peer A does not
                # have to send ‘unchoke’ message to it. All other neighbors previously unchoked but not
                # selected as preferred neighbors at this time should be choked unless it is an optimistically
                # unchoked neighbor. To choke those neighbors, peer A sends ‘choke’ messages to them
                # and stop sending pieces.

                #Update timestamp for next unchoking/choking
                choke_time += self.unchoking_interval

            #If the interval time passes
            if time.time() > optimistic_unchoke_time:
                # Pick out new id to optimistically unchoke
                self.select_optimistically_unchoked()

                #TODO: Then peer A sends ‘unchoke’ message to the selected neighbor and
                # it expects to receive ‘request’ messages from it.

                # Update timestamp for next optimistic unchoking
                optimistic_unchoke_time += self.optimistic_unchoking_interval

            #Let's randomize the download rates of our peers to evaluate the dynamic nature of it
            for peer in neighbors:
                peer.download_rate = random.randint(1,10) #Pick a number 0-9

            #Intervals are kinda slow we dont want to clutter the console even during development
            time.sleep(2)

if __name__ == "__main__":
    # Create some fake neighbors to test logic
    neighbor_1 = SimulatedNeigborPeer(1001, 6)
    neighbor_2 = SimulatedNeigborPeer(1002, 4)
    neighbor_3 = SimulatedNeigborPeer(1003, 9)
    neighbor_4 = SimulatedNeigborPeer(1004, 6)
    neighbor_5 = SimulatedNeigborPeer(1005, 2)

    neighbors = [neighbor_1, neighbor_2, neighbor_3, neighbor_4, neighbor_5]
    handler = ChokingHandler(neighbors, num_preferred_neighbors=3, unchoking_interval=5,
                             optimistic_unchoking_interval=10)  # Manually choose some for now
    handler.run_choking_cycle()
    # Still in progress