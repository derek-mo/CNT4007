import random
import time
import threading
import datetime

class ChokingHandler:
    def __init__(self, peer, num_preferred_neighbors, unchoking_interval, optimistic_unchoking_interval):
        self.peer = peer
        self.num_preferred_neighbors = num_preferred_neighbors
        self.unchoking_interval = unchoking_interval  # Seconds between preferred neighbor selections
        self.optimistic_unchoking_interval = optimistic_unchoking_interval  # Seconds between optimistic unchoke
        
        # Track current unchoked peers
        self.preferred_neighbors = []
        self.optimistically_unchoked_id = None
        
        self.start_time = time.time()

    def select_preferred_neighbors(self):
        interested_neighbors = []
        
        # Get all interested neighbors with their download rates
        for peer_id, state in self.peer.neighbor_states.items():
            if state['interested']:
                interested_neighbors.append((state['download_rate'], peer_id))
        
        # print(f"Peer {self.peer.peer_id}: Selecting preferred neighbors from {len(interested_neighbors)} interested peers")
        
        if not interested_neighbors:
            self.preferred_neighbors = []
            # print(f"Peer {self.peer.peer_id}: No interested neighbors to select")
            return []
            return []
        
        # If we have the complete file, select randomly
        if self.peer.bitfield.missing() == []:
            # print(f"Peer {self.peer.peer_id}: File complete - selecting neighbors randomly")
            random.shuffle(interested_neighbors)
            selected = [peer_id for _, peer_id in interested_neighbors[:self.num_preferred_neighbors]]
        else:
            # print(f"Peer {self.peer.peer_id}: File incomplete - selecting by download rate")
            # Otherwise, select based on highest download rates
            # Sort by download rate (descending), then randomize ties
            grouped_by_rate = {}
            for rate, peer_id in interested_neighbors:
                if rate not in grouped_by_rate:
                    grouped_by_rate[rate] = []
                grouped_by_rate[rate].append(peer_id)
            
            # Randomize within each rate group and sort by rate descending
            sorted_peers = []
            for rate in sorted(grouped_by_rate.keys(), reverse=True):
                peers_with_rate = grouped_by_rate[rate]
                random.shuffle(peers_with_rate)
                sorted_peers.extend(peers_with_rate)
            
            selected = sorted_peers[:self.num_preferred_neighbors]
        
        self.preferred_neighbors = selected
        # print(f"Peer {self.peer.peer_id}: Selected preferred neighbors: {selected}")
        return selected

    def select_optimistically_unchoked(self):
        # Get interested neighbors that are currently choked
        choked_interested = []
        for peer_id, state in self.peer.neighbor_states.items():
            if state['interested'] and state['choked']:
                # Don't include already preferred neighbors
                if peer_id not in self.preferred_neighbors:
                    choked_interested.append(peer_id)
        
        if not choked_interested:
            self.optimistically_unchoked_id = None
            # print(f"Peer {self.peer.peer_id}: No choked interested neighbors for optimistic unchoke")
            return None
        
        # Randomly select one
        self.optimistically_unchoked_id = random.choice(choked_interested)
        # print(f"Peer {self.peer.peer_id}: Selected optimistically unchoked neighbor: {self.optimistically_unchoked_id} from {len(choked_interested)} candidates")
        return self.optimistically_unchoked_id

    def apply_choking_decisions(self, newly_unchoked):
        from messageHandler import Message
        
        all_unchoked = set(newly_unchoked)
        if self.optimistically_unchoked_id:
            all_unchoked.add(self.optimistically_unchoked_id)
        
        # Update choke status and send messages
        for peer_id, state in self.peer.neighbor_states.items():
            socket_conn = self.peer.PeersConnections.get(peer_id)
            if not socket_conn:
                continue
            
            should_be_unchoked = peer_id in all_unchoked
            currently_choked = state['choked']
            
            if should_be_unchoked and currently_choked:
                # Unchoke this peer
                # print(f"Peer {self.peer.peer_id}: UNCHOKING Peer {peer_id}")
                self.peer.msgHandler.sendMessage(socket_conn, Message(1, b''), peer_id)
                state['choked'] = False
                # Reset download rate tracking when unchoking
                state['bytes_received'] = 0
                state['last_rate_calc'] = time.time()
                
            elif not should_be_unchoked and not currently_choked:
                # Choke this peer
                # print(f"Peer {self.peer.peer_id}: CHOKING Peer {peer_id}")
                self.peer.msgHandler.sendMessage(socket_conn, Message(0, b''), peer_id)
                state['choked'] = True

    def run_choking_cycle(self):
        # Main loop for managing choking decisions
        next_preferred_time = self.start_time + self.unchoking_interval
        next_optimistic_time = self.start_time + self.optimistic_unchoking_interval
        
        while not self.peer.shutdown_event.is_set():
            current_time = time.time()
            
            # Check if it's time to select preferred neighbors
            if current_time >= next_preferred_time:
                newly_preferred = self.select_preferred_neighbors()
                
                # Log the change
                if newly_preferred:
                    with open(f"../log_peer_{self.peer.peer_id}.log", "a") as log_file:
                        neighbor_list = ", ".join(map(str, newly_preferred))
                        log_file.write(f"{datetime.datetime.now().strftime('%c')}: Peer {self.peer.peer_id} has the preferred neighbors {neighbor_list}.\n")
                
                # Apply choking decisions
                self.apply_choking_decisions(newly_preferred)
                
                next_preferred_time += self.unchoking_interval
            
            # Check if it's time to select optimistically unchoked neighbor
            if current_time >= next_optimistic_time:
                optimistic_peer = self.select_optimistically_unchoked()
                
                # Log the change
                if optimistic_peer:
                    with open(f"../log_peer_{self.peer.peer_id}.log", "a") as log_file:
                        log_file.write(f"{datetime.datetime.now().strftime('%c')}: Peer {self.peer.peer_id} has the optimistically unchoked neighbor {optimistic_peer}.\n")
                    
                    # Apply the optimistic unchoke
                    self.apply_choking_decisions(self.preferred_neighbors)
                
                next_optimistic_time += self.optimistic_unchoking_interval
            
            # Sleep briefly to avoid busy waiting
            time.sleep(1)
