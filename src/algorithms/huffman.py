"""
Huffman Coding Implementation
Bottom-up tree construction using priority queue (min-heap).
"""

import heapq
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass(order=True)
class HuffmanNode:
    """Node in Huffman tree. Uses dataclass for automatic comparison."""
    frequency: int
    byte_value: Optional[int] = field(compare=False)
    left: Optional['HuffmanNode'] = field(default=None, compare=False)
    right: Optional['HuffmanNode'] = field(default=None, compare=False)
    
    def is_leaf(self) -> bool:
        """Check if this is a leaf node (represents actual byte)."""
        return self.left is None and self.right is None


class HuffmanCoder:
    """
    Huffman Coding encoder/decoder.
    Builds optimal prefix-free codes based on symbol frequencies.
    """
    
    def __init__(self):
        self.root: Optional[HuffmanNode] = None
        self.code_table: Dict[int, str] = {}
        self.reverse_table: Dict[str, int] = {}
    
    def build_tree(self, frequency_dict: Dict[int, int]) -> HuffmanNode:
        """
        Build Huffman tree using priority queue (min-heap).
        
        Args:
            frequency_dict: Dictionary mapping byte value to frequency
            
        Returns:
            HuffmanNode: Root of the Huffman tree
        """
        if not frequency_dict:
            raise ValueError("Frequency dictionary cannot be empty")
        
        # Handle single symbol case
        if len(frequency_dict) == 1:
            byte_value, freq = list(frequency_dict.items())[0]
            # Create a tree with single node - assign code '0'
            self.root = HuffmanNode(frequency=freq, byte_value=byte_value)
            self.code_table = {byte_value: '0'}
            self.reverse_table = {'0': byte_value}
            return self.root
        
        # Initialize priority queue with leaf nodes
        heap = []
        # Sort by byte_value to ensure deterministic tree construction when frequencies are tied
        sorted_items = sorted(frequency_dict.items())
        for byte_value, frequency in sorted_items:
            node = HuffmanNode(frequency=frequency, byte_value=byte_value)
            heapq.heappush(heap, node)
        
        # Build tree bottom-up
        while len(heap) > 1:
            # Pop two nodes with minimum frequency
            left = heapq.heappop(heap)
            right = heapq.heappop(heap)
            
            # Create parent node
            parent = HuffmanNode(
                frequency=left.frequency + right.frequency,
                byte_value=None,  # Internal nodes don't represent bytes
                left=left,
                right=right
            )
            
            # Push parent back to heap
            heapq.heappush(heap, parent)
        
        # Last remaining node is root
        self.root = heap[0]
        
        # Generate code table
        self._generate_codes(self.root, '')
        
        return self.root
    
    def _generate_codes(self, node: Optional[HuffmanNode], code: str) -> None:
        """
        Recursively generate binary codes for each byte.
        
        Args:
            node: Current node in tree
            code: Binary code string accumulated so far
        """
        if node is None:
            return
        
        # If leaf node, store code
        if node.is_leaf():
            self.code_table[node.byte_value] = code if code else '0'
            self.reverse_table[code if code else '0'] = node.byte_value
            return
        
        # Traverse left (add '0') and right (add '1')
        self._generate_codes(node.left, code + '0')
        self._generate_codes(node.right, code + '1')
    
    def encode(self, data: bytes) -> str:
        """
        Encode byte data using Huffman codes.
        
        Args:
            data: Raw bytes to encode
            
        Returns:
            str: Binary string of encoded data
        """
        if not self.code_table:
            raise ValueError("Code table not built. Call build_tree() first.")
        
        encoded = []
        for byte in data:
            if byte not in self.code_table:
                raise ValueError(f"Byte {byte} not in code table")
            encoded.append(self.code_table[byte])
        
        return ''.join(encoded)
    
    def decode(self, encoded_bits: str, bit_length: Optional[int] = None) -> bytes:
        """
        Decode binary string using Huffman tree.
        
        Args:
            encoded_bits: Binary string to decode
            bit_length: Actual number of bits (excluding padding)
            
        Returns:
            bytes: Decoded data
        """
        if not self.root:
            raise ValueError("Tree not built. Call build_tree() first.")
        
        # Use bit_length if provided to ignore padding
        if bit_length:
            encoded_bits = encoded_bits[:bit_length]
        
        decoded = []
        current_node = self.root
        
        # Handle single symbol case
        if current_node.is_leaf():
            # All bits decode to same symbol
            count = len(encoded_bits)
            decoded = [current_node.byte_value] * count
            return bytes(decoded)
        
        # Traverse tree for each bit
        for bit in encoded_bits:
            if bit == '0':
                current_node = current_node.left
            else:
                current_node = current_node.right
            
            # If leaf reached, output byte and reset to root
            if current_node.is_leaf():
                decoded.append(current_node.byte_value)
                current_node = self.root
        
        return bytes(decoded)
    
    def get_code_table(self) -> Dict[int, str]:
        """Get the code table mapping bytes to binary codes."""
        return self.code_table.copy()
    
    def set_code_table(self, code_table: Dict[int, str]) -> None:
        """
        Set code table and rebuild reverse table.
        Used when loading from compressed file header.
        """
        self.code_table = code_table.copy()
        self.reverse_table = {code: byte for byte, code in code_table.items()}
        
        # Rebuild tree from code table for decoding
        self._rebuild_tree_from_codes()
    
    def _rebuild_tree_from_codes(self) -> None:
        """Rebuild Huffman tree from code table."""
        if not self.code_table:
            return
        
        # Handle single symbol case
        if len(self.code_table) == 1:
            byte_value = list(self.code_table.keys())[0]
            self.root = HuffmanNode(frequency=0, byte_value=byte_value)
            return
        
        # Create root
        self.root = HuffmanNode(frequency=0, byte_value=None)
        
        # Build tree by following each code
        for byte_value, code in self.code_table.items():
            current = self.root
            
            for bit in code:
                if bit == '0':
                    if current.left is None:
                        current.left = HuffmanNode(frequency=0, byte_value=None)
                    current = current.left
                else:
                    if current.right is None:
                        current.right = HuffmanNode(frequency=0, byte_value=None)
                    current = current.right
            
            # Set byte value at leaf
            current.byte_value = byte_value
    
    def calculate_average_code_length(self, frequency_dict: Dict[int, int]) -> float:
        """
        Calculate weighted average code length.
        
        Args:
            frequency_dict: Byte frequencies
            
        Returns:
            float: Average bits per symbol
        """
        if not self.code_table or not frequency_dict:
            return 0.0
        
        total_symbols = sum(frequency_dict.values())
        weighted_sum = sum(
            len(self.code_table[byte]) * freq
            for byte, freq in frequency_dict.items()
            if byte in self.code_table
        )
        
        return weighted_sum / total_symbols if total_symbols > 0 else 0.0
