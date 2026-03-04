"""
Shannon-Fano Coding Implementation
Top-down tree construction using recursive probability splitting.
"""

from typing import Dict, List, Tuple, Optional


class ShannonFanoNode:
    """Node in Shannon-Fano tree."""
    
    def __init__(self, byte_value: Optional[int] = None):
        self.byte_value = byte_value
        self.left: Optional['ShannonFanoNode'] = None
        self.right: Optional['ShannonFanoNode'] = None
    
    def is_leaf(self) -> bool:
        """Check if this is a leaf node."""
        return self.left is None and self.right is None


class ShannonFanoCoder:
    """
    Shannon-Fano Coding encoder/decoder.
    Builds codes by recursively splitting symbols into balanced probability groups.
    """
    
    def __init__(self):
        self.root: Optional[ShannonFanoNode] = None
        self.code_table: Dict[int, str] = {}
        self.reverse_table: Dict[str, int] = {}
    
    def build_tree(self, frequency_dict: Dict[int, int]) -> ShannonFanoNode:
        """
        Build Shannon-Fano tree using recursive splitting.
        
        Args:
            frequency_dict: Dictionary mapping byte value to frequency
            
        Returns:
            ShannonFanoNode: Root of the tree
        """
        if not frequency_dict:
            raise ValueError("Frequency dictionary cannot be empty")
        
        # Handle single symbol case
        if len(frequency_dict) == 1:
            byte_value = list(frequency_dict.keys())[0]
            self.root = ShannonFanoNode(byte_value=byte_value)
            self.code_table = {byte_value: '0'}
            self.reverse_table = {'0': byte_value}
            return self.root
        
        # Sort symbols by frequency (descending), then by byte value (ascending) for deterministic splitting
        sorted_symbols = sorted(
            frequency_dict.items(),
            key=lambda x: (-x[1], x[0])
        )
        
        # Build tree recursively
        self.root = ShannonFanoNode()
        self._build_recursive(sorted_symbols, self.root, '')
        
        return self.root
    
    def _build_recursive(
        self,
        symbols: List[Tuple[int, int]],
        node: ShannonFanoNode,
        code: str
    ) -> None:
        """
        Recursively build tree by splitting symbol list.
        
        Args:
            symbols: List of (byte_value, frequency) tuples
            node: Current node being built
            code: Binary code accumulated so far
        """
        # Base case: single symbol
        if len(symbols) == 1:
            byte_value, _ = symbols[0]
            node.byte_value = byte_value
            self.code_table[byte_value] = code if code else '0'
            self.reverse_table[code if code else '0'] = byte_value
            return
        
        # Find split point that balances total frequencies
        split_index = self._find_split_point(symbols)
        
        # Split into two groups
        left_symbols = symbols[:split_index]
        right_symbols = symbols[split_index:]
        
        # Create child nodes
        if left_symbols:
            node.left = ShannonFanoNode()
            self._build_recursive(left_symbols, node.left, code + '0')
        
        if right_symbols:
            node.right = ShannonFanoNode()
            self._build_recursive(right_symbols, node.right, code + '1')
    
    def _find_split_point(self, symbols: List[Tuple[int, int]]) -> int:
        """
        Find optimal split point to balance probabilities.
        
        Args:
            symbols: List of (byte_value, frequency) tuples
            
        Returns:
            int: Index to split at (1 to len-1)
        """
        if len(symbols) <= 1:
            return 1
        
        total_freq = sum(freq for _, freq in symbols)
        
        # Try to split so left and right have similar total frequencies
        cumulative = 0
        best_split = 1
        best_diff = float('inf')
        
        for i in range(1, len(symbols)):
            cumulative += symbols[i - 1][1]
            left_freq = cumulative
            right_freq = total_freq - cumulative
            
            diff = abs(left_freq - right_freq)
            if diff < best_diff:
                best_diff = diff
                best_split = i
        
        return best_split
    
    def encode(self, data: bytes) -> str:
        """
        Encode byte data using Shannon-Fano codes.
        
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
        Decode binary string using Shannon-Fano tree.
        
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
            count = len(encoded_bits)
            decoded = [current_node.byte_value] * count
            return bytes(decoded)
        
        # Traverse tree for each bit
        for bit in encoded_bits:
            if bit == '0':
                current_node = current_node.left
            else:
                current_node = current_node.right
            
            if current_node is None:
                raise ValueError("Invalid encoded data: reached None node")
            
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
        Set code table and rebuild tree.
        Used when loading from compressed file header.
        """
        self.code_table = code_table.copy()
        self.reverse_table = {code: byte for byte, code in code_table.items()}
        self._rebuild_tree_from_codes()
    
    def _rebuild_tree_from_codes(self) -> None:
        """Rebuild tree from code table."""
        if not self.code_table:
            return
        
        # Handle single symbol case
        if len(self.code_table) == 1:
            byte_value = list(self.code_table.keys())[0]
            self.root = ShannonFanoNode(byte_value=byte_value)
            return
        
        # Create root
        self.root = ShannonFanoNode()
        
        # Build tree by following each code
        for byte_value, code in self.code_table.items():
            current = self.root
            
            for bit in code:
                if bit == '0':
                    if current.left is None:
                        current.left = ShannonFanoNode()
                    current = current.left
                else:
                    if current.right is None:
                        current.right = ShannonFanoNode()
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
