"""
Compression Engine
Main compression logic with custom binary file format.
"""

import json
import struct
from typing import Dict, Literal
from pathlib import Path

from ..core.binary_reader import read_binary_file, get_file_extension
from ..core.frequency_analyzer import count_frequencies
from ..core.bit_operations import BitWriter
from ..algorithms.huffman import HuffmanCoder
from ..algorithms.shannon_fano import ShannonFanoCoder


# Algorithm identifiers
ALGORITHM_HUFFMAN = 0
ALGORITHM_SHANNON_FANO = 1

# Magic signatures
MAGIC_HUFFMAN = b'HUF1'
MAGIC_SHANNON_FANO = b'SHF1'


class CompressionEngine:
    """Main compression engine supporting multiple algorithms."""
    
    def __init__(self):
        self.algorithm = None
        self.coder = None
    
    def compress_file(
        self,
        input_path: str,
        output_path: str,
        algorithm: Literal['huffman', 'shannon_fano'] = 'huffman'
    ) -> Dict:
        """
        Compress a file using specified algorithm.
        
        Args:
            input_path: Path to input file
            output_path: Path to output compressed file
            algorithm: 'huffman' or 'shannon_fano'
            
        Returns:
            Dict: Compression statistics
        """
        # Read binary data
        print(f"Reading file: {input_path}")
        data = read_binary_file(input_path)
        original_size = len(data)
        
        if original_size == 0:
            raise ValueError("Cannot compress empty file")
        
        # Count frequencies
        print("Analyzing byte frequencies...")
        frequency_dict = count_frequencies(data)
        
        # Select and build coder
        if algorithm == 'huffman':
            self.coder = HuffmanCoder()
            algorithm_id = ALGORITHM_HUFFMAN
            magic = MAGIC_HUFFMAN
        elif algorithm == 'shannon_fano':
            self.coder = ShannonFanoCoder()
            algorithm_id = ALGORITHM_SHANNON_FANO
            magic = MAGIC_SHANNON_FANO
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        print(f"Building {algorithm} tree...")
        self.coder.build_tree(frequency_dict)
        code_table = self.coder.get_code_table()
        
        # Encode data
        print("Encoding data...")
        encoded_bits = self.coder.encode(data)
        payload_bit_length = len(encoded_bits)
        
        # Get original extension
        extension = get_file_extension(input_path)
        
        # Write compressed file
        print(f"Writing compressed file: {output_path}")
        self._write_compressed_file(
            output_path,
            magic,
            algorithm_id,
            extension,
            code_table,
            encoded_bits,
            payload_bit_length
        )
        
        # Calculate statistics
        from ..utils.metrics import calculate_compression_ratio, calculate_space_saving
        import os
        
        compressed_size = os.path.getsize(output_path)
        compression_ratio = calculate_compression_ratio(original_size, compressed_size)
        space_saving = calculate_space_saving(original_size, compressed_size)
        avg_code_length = self.coder.calculate_average_code_length(frequency_dict)
        
        stats = {
            'algorithm': algorithm,
            'original_size': original_size,
            'compressed_size': compressed_size,
            'compression_ratio': compression_ratio,
            'space_saving_percent': space_saving,
            'payload_bits': payload_bit_length,
            'average_code_length': avg_code_length,
            'unique_bytes': len(frequency_dict)
        }
        
        print(f"\n[OK] Compression complete!")
        print(f"  Original size: {original_size:,} bytes")
        print(f"  Compressed size: {compressed_size:,} bytes")
        print(f"  Compression ratio: {compression_ratio:.3f}")
        print(f"  Space saving: {space_saving:.2f}%")
        
        return stats
    
    def _write_compressed_file(
        self,
        filepath: str,
        magic: bytes,
        algorithm_id: int,
        extension: str,
        code_table: Dict[int, str],
        encoded_bits: str,
        payload_bit_length: int
    ) -> None:
        """
        Write compressed file with custom binary format.
        
        Format:
        [4 bytes] Magic signature
        [1 byte]  Algorithm ID
        [4 bytes] Extension length
        [N bytes] Extension string (UTF-8)
        [4 bytes] Code table JSON length
        [M bytes] Code table JSON
        [8 bytes] Payload bit length
        [Rest]    Compressed payload
        """
        with open(filepath, 'wb') as f:
            # Write magic signature
            f.write(magic)
            
            # Write algorithm ID
            f.write(struct.pack('B', algorithm_id))
            
            # Write extension
            ext_bytes = extension.encode('utf-8')
            f.write(struct.pack('I', len(ext_bytes)))
            f.write(ext_bytes)
            
            # Serialize code table to JSON
            # Convert int keys to strings for JSON
            code_table_json = json.dumps({str(k): v for k, v in code_table.items()})
            code_table_bytes = code_table_json.encode('utf-8')
            
            # Write code table
            f.write(struct.pack('I', len(code_table_bytes)))
            f.write(code_table_bytes)
            
            # Write payload bit length
            f.write(struct.pack('Q', payload_bit_length))
            
            # Get current position for payload
            payload_start = f.tell()
        
        # Write payload using BitWriter
        with BitWriter(filepath + '.tmp') as writer:
            writer.write_bits(encoded_bits)
            padding = writer.flush()
        
        # Append payload to main file
        with open(filepath, 'ab') as f:
            with open(filepath + '.tmp', 'rb') as tmp:
                f.write(tmp.read())
        
        # Clean up temp file
        import os
        os.remove(filepath + '.tmp')
