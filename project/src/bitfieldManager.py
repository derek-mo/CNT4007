import math
from pathlib import Path

class BitfieldManager:
    def __init__(self, total_size, piece_size, peer_dir, has_complete):
        self.total_size = total_size
        self.piece_size = piece_size
        self.num_pieces = math.ceil(total_size / piece_size)

        # Path object for the peer's folder (e.g., ./peer_1001/)
        self.peer_dir = Path(peer_dir)
        self.peer_dir.mkdir(parents=True, exist_ok=True)

        self.bits = bytearray((self.num_pieces + 7) // 8)

        if has_complete:
            for i in range(self.num_pieces):
                self._set(i)

        self._mask_spare_bits()

    def has(self, index):
        if index < 0 or index >= self.num_pieces:
            raise IndexError(f"Invalid piece index: {index}")

        byte_index = index // 8
        bit_position = 7 - (index % 8)  # high-bit first
        return (self._bits[byte_index] >> bit_position) & 1 == 1


    def set(self, index):
        # Change a bit to have a bit
        byte_index = index // 8
        bit_position = 7 - (index % 8)
        self._bits[byte_index] |= (1 << bit_position)

    def mask_spare_bits(self):
        
        spare_bits = (8 - (self.num_pieces % 8)) % 8
        if spare_bits and self.bits:
            self._bits[-1] &= (0xFF << spare_bits) & 0xFF
