import random
import time

#Create a class to simulate information we would receveive during connection with other peers
class SimulatedNeigborPeer:
    def __init__(self, peer_id):
        self.peer_id = peer_id
        self.download_rate = 0
        self.is_interested = False
        self.choked = True

#This class will implement the chocking logic
class ChokingHandler:
    def __init__(self, neighbors, num_preferred_neighbors, unchoking_interval, optimistic_unchoking_interval):
        self.neighbors = neighbors
        self.num_preferred_neighbors = num_preferred_neighbors
        self.unchoking_interval = unchoking_interval
        self.optimistic_unchoking_interval = optimistic_unchoking_interval
        self.time_of_creation = time.time()
        self.optimistically_unchoked_id = None

    def select_preferred_neighbors(self):
        pass  # In progress

    def optimistic_unchoke(self):
        pass  # In progress

    def run_choking_cycle(self):
        pass  # In progress

if __name__ == "__main__":
    #Create some fake neighbors to test logic
    neighbor_1 = SimulatedNeigborPeer(1)
    neighbor_2 = SimulatedNeigborPeer(2)
    neighbor_3 = SimulatedNeigborPeer(3)
    neighbor_4 = SimulatedNeigborPeer(4)
    neighbor_5 = SimulatedNeigborPeer(5)

    neighbors = [neighbor_1, neighbor_2, neighbor_3, neighbor_4, neighbor_5]
    manager = ChokingHandler(neighbors, num_preferred=3, unchoking_interval=5, optimistic_interval=10) #Manually choose some for now

    #Missing logic currently