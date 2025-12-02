import math
from pathlib import Path

class BitfieldManager:
  def __init__(self, total_size, piece_size, peer_dir, has_complete):
      self.total_size = total_size
      self.piece_size = piece_size
      self.num_pieces = math.ceil(total_size / piece_size)
      self.peer_dir = Path(peer_dir) if peer_dir is not None else None

      self.bits = bytearray((self.num_pieces + 7) // 8)

      if has_complete:
          for i in range(self.num_pieces):
              self.set_bit(i)

      self.cleanup_spare_bits()

  # Returns true if the bit is a 1
  def has(self, index):
      self.check_index(index)
      byte_index = index // 8
      bit_position = 7 - (index % 8)

      byte_value = self.bits[byte_index]
      shifted_byte = byte_value >> bit_position

      return shifted_byte & 1 == 1
  
  # Marks an index with a 1 now that the peer has it
  def mark_have(self, index):
      byte_index = index // 8
      bit_position = 7 - (index % 8)

      byte_value = self.bits[byte_index]
      bit_mask = (1 << bit_position)
      new_byte_value = byte_value | bit_mask
      self.bits[byte_index] = new_byte_value

  # Shows us what indices this peer is missing
  def missing(self):
      missing = []

      for i in range(self.num_pieces):
          if not self.has(i):
              missing.append(i)

      return missing
  
  def check_index(self, index):
    if index < 0 or index >= self.num_pieces:
        raise IndexError(f"Piece index {index} out of range 0..{self.num_pieces - 1}")

  # Convert bitfield to bytes for TCP
  def to_bytes(self):
      return bytes(self.bits)

  # Convert given bitfield information that is in bytes to bits
  def from_bytes(self, data):
      if not isinstance(data, (bytes, bytearray)):
          raise TypeError("data must be bytes or bytearray")

      expected_len = (self.num_pieces + 7) // 8
      if len(data) != expected_len:
          raise ValueError(f"Expected {expected_len} bytes, got {len(data)}")

      self.bits = bytearray(data)
      self.cleanup_spare_bits()

  def set_bit(self, index):
      self.check_index(index)
      byte_index = index // 8
      bit_position = 7 - (index % 8)
      self.bits[byte_index] |= (1 << bit_position)

  def cleanup_spare_bits(self):
      # Final bits should be 0
      spare_bits = (8 - (self.num_pieces % 8)) % 8
      if spare_bits and len(self.bits) > 0:
          mask = (0xFF << spare_bits) & 0xFF
          self.bits[-1] &= mask
