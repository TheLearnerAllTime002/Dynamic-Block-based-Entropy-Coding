"""
Decompression Engine
Reads compressed files and restores original data.
"""

import json
import struct
from typing import Dict, Tuple
from pathlib import Path

from ..core.bit_operations import BitReader
from ..algorithms.huffman import HuffmanCoder
from ..algorithms.shannon_fano import ShannonFanoCoder
from .compressor import (
    ALGORITHM_HUFFMAN,
    ALGORITHM_SHANNON_FANO,
    MAGIC_HUFFMAN,
    MAGIC_SHANNON_FANO
)

# Define MAGIC_HYBRID locally to avoid circular import
MAGIC_HYBRID = b'HYB1'


class DecompressionEngine:
    """Main decompression engine."""
    
    def __init__(self):
        self.coder = None
    
    def decompress_file(
        self,
        input_path: str,
        output_path: str = None
    ) -> Dict:
        """
        Decompress a file.
        
        Args:
            input_path: Path to compressed file
            output_path: Path to output file (optional, auto-generated if None)
            
        Returns:
            Dict: Decompression statistics
        """
        print(f"Reading compressed file: {input_path}")
        
        # Check if it's a hybrid file
        with open(input_path, 'rb') as f:
            magic = f.read(4)
        
        if magic == MAGIC_HYBRID:
            raise ValueError("Hybrid DB-HEC files (HYB1) must be decompressed using DBHECDecompressor directly.")
        
        # Read and parse header for standard formats
        metadata = self._read_header(input_path)
        
        algorithm_id = metadata['algorithm_id']
        extension = metadata['extension']
        code_table = metadata['code_table']
        payload_bit_length = metadata['payload_bit_length']
        header_size = metadata['header_size']
        
        # Determine output path
        if output_path is None:
            # Auto-generate output path
            input_file = Path(input_path)
            output_path = str(input_file.parent / f"{input_file.stem}_decompressed{extension}")
        
        # Select decoder
        if algorithm_id == ALGORITHM_HUFFMAN:
            self.coder = HuffmanCoder()
            algorithm_name = 'huffman'
        elif algorithm_id == ALGORITHM_SHANNON_FANO:
            self.coder = ShannonFanoCoder()
            algorithm_name = 'shannon_fano'
        else:
            raise ValueError(f"Unknown algorithm ID: {algorithm_id}")
        
        print(f"Algorithm: {algorithm_name}")
        print(f"Original extension: {extension}")
        
        # Set code table
        self.coder.set_code_table(code_table)
        
        # Read payload
        print("Reading compressed payload...")
        encoded_bits = self._read_payload(input_path, header_size, payload_bit_length)
        
        # Decode
        print("Decoding data...")
        decoded_data = self.coder.decode(encoded_bits, payload_bit_length)
        
        # Write output file
        print(f"Writing decompressed file: {output_path}")
        from ..core.binary_reader import write_binary_file
        write_binary_file(output_path, decoded_data)
        
        # Calculate statistics
        import os
        compressed_size = os.path.getsize(input_path)
        decompressed_size = len(decoded_data)
        
        stats = {
            'algorithm': algorithm_name,
            'compressed_size': compressed_size,
            'decompressed_size': decompressed_size,
            'output_path': output_path
        }
        
        print(f"\n[OK] Decompression complete!")
        print(f"  Compressed size: {compressed_size:,} bytes")
        print(f"  Decompressed size: {decompressed_size:,} bytes")
        print(f"  Output: {output_path}")
        
        return stats
    
    def _read_header(self, filepath: str) -> Dict:
        """
        Read and parse compressed file header.
        
        Returns:
            Dict: Header metadata
        """
        with open(filepath, 'rb') as f:
            # Read magic signature
            magic = f.read(4)
            if magic not in (MAGIC_HUFFMAN, MAGIC_SHANNON_FANO, MAGIC_HYBRID):
                raise ValueError(f"Invalid file format. Magic: {magic}")
            
            # Read algorithm ID
            algorithm_id = struct.unpack('B', f.read(1))[0]
            
            # Read extension
            ext_length = struct.unpack('I', f.read(4))[0]
            extension = f.read(ext_length).decode('utf-8')
            
            # Read code table
            code_table_length = struct.unpack('I', f.read(4))[0]
            code_table_json = f.read(code_table_length).decode('utf-8')
            code_table_str_keys = json.loads(code_table_json)
            
            # Convert string keys back to integers
            code_table = {int(k): v for k, v in code_table_str_keys.items()}
            
            # Read payload bit length
            payload_bit_length = struct.unpack('Q', f.read(8))[0]
            
            # Record header size
            header_size = f.tell()
        
        return {
            'magic': magic,
            'algorithm_id': algorithm_id,
            'extension': extension,
            'code_table': code_table,
            'payload_bit_length': payload_bit_length,
            'header_size': header_size
        }
    
    def _read_payload(
        self,
        filepath: str,
        header_size: int,
        payload_bit_length: int
    ) -> str:
        """
        Read compressed payload as bit string.
        
        Args:
            filepath: Path to compressed file
            header_size: Size of header in bytes
            payload_bit_length: Number of actual payload bits
            
        Returns:
            str: Binary string of payload
        """
        with open(filepath, 'rb') as f:
            # Skip header
            f.seek(header_size)
            
            # Read payload bytes
            payload_bytes = f.read()
        
        # Convert to bit string
        bit_string = ''.join(format(byte, '08b') for byte in payload_bytes)
        
        # Return only the actual payload bits (ignore padding)
        return bit_string[:payload_bit_length]
