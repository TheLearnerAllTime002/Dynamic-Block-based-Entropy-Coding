"""
DB-HEC I/O Module
Handles reading and writing of hybrid compressed file format.
"""

import struct
from typing import BinaryIO

class DBHECWriter:
    """Writer for DB-HEC hybrid compressed files with bitwise optimization."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.file: BinaryIO = None
        self.bit_buffer = 0
        self.bit_count = 0
        self.total_bits_written = 0
    
    def __enter__(self):
        self.file = open(self.filepath, 'wb')
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.flush()
            self.file.close()
    
    def write_raw_string(self, data: str, length: int):
        """Write raw string data."""
        self.file.write(data.encode('ascii')[:length].ljust(length, b'\x00'))
    
    def write_byte(self, value: int):
        """Write single byte."""
        self.file.write(struct.pack('B', value))
    
    def write_uint32(self, value: int):
        """Write 32-bit unsigned integer."""
        self.file.write(struct.pack('>I', value))
    
    def write_uint64(self, value: int):
        """Write 64-bit unsigned integer."""
        self.file.write(struct.pack('>Q', value))
    
    def write_double(self, value: float):
        """Write double precision float."""
        self.file.write(struct.pack('>d', value))
    
    def write_string(self, text: str):
        """Write length-prefixed string."""
        encoded = text.encode('utf-8')
        self.write_uint32(len(encoded))
        self.file.write(encoded)
    
    def write_bytes(self, data: bytes):
        """Write raw bytes."""
        self.file.write(data)
    
    def write_bits(self, bit_string: str):
        """Write bit string as packed bytes using bitwise operations."""
        for bit in bit_string:
            if bit == '1':
                self.bit_buffer = (self.bit_buffer << 1) | 1
            else:
                self.bit_buffer = (self.bit_buffer << 1)
            
            self.bit_count += 1
            if self.bit_count == 8:
                self.file.write(struct.pack('B', self.bit_buffer))
                self.bit_buffer = 0
                self.bit_count = 0
        self.total_bits_written += len(bit_string)
    
    def align(self):
        """Align to byte boundary."""
        if self.bit_count > 0:
            self.flush()
    
    def flush(self):
        """Flush any remaining bits with zero padding."""
        if self.bit_count > 0:
            padding = 8 - self.bit_count
            self.bit_buffer <<= padding
            self.file.write(struct.pack('B', self.bit_buffer))
            self.bit_buffer = 0
            self.bit_count = 0


class DBHECReader:
    """Reader for DB-HEC hybrid compressed files."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.file: BinaryIO = None
        self.bit_buffer = 0
        self.bits_left = 0
    
    def __enter__(self):
        self.file = open(self.filepath, 'rb')
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()
    
    def read_string(self, length: int = None) -> str:
        """Read string data."""
        if length is None:
            length = self.read_uint32()
        
        data = self.file.read(length)
        if len(data) < length:
            raise EOFError("Unexpected end of file")
        
        return data.decode('utf-8').rstrip('\x00')
    
    def read_byte(self) -> int:
        """Read single byte."""
        data = self.file.read(1)
        if len(data) < 1:
            raise EOFError("Unexpected end of file")
        return struct.unpack('B', data)[0]
    
    def read_uint32(self) -> int:
        """Read 32-bit unsigned integer."""
        data = self.file.read(4)
        if len(data) < 4:
            raise EOFError("Unexpected end of file")
        return struct.unpack('>I', data)[0]
    
    def read_uint64(self) -> int:
        """Read 64-bit unsigned integer."""
        data = self.file.read(8)
        if len(data) < 8:
            raise EOFError("Unexpected end of file")
        return struct.unpack('>Q', data)[0]
    
    def read_double(self) -> float:
        """Read double precision float."""
        data = self.file.read(8)
        if len(data) < 8:
            raise EOFError("Unexpected end of file")
        return struct.unpack('>d', data)[0]
    
    def read_bytes(self, length: int) -> bytes:
        """Read raw bytes."""
        data = self.file.read(length)
        if len(data) < length:
            raise EOFError("Unexpected end of file")
        return data
    
    def read_bits(self, bit_count: int) -> str:
        """Read bits and return as bit string efficiently."""
        result = []
        for _ in range(bit_count):
            if self.bits_left == 0:
                self.bit_buffer = self.read_byte()
                self.bits_left = 8
            
            bit = (self.bit_buffer >> (self.bits_left - 1)) & 1
            result.append('1' if bit else '0')
            self.bits_left -= 1
        
        return "".join(result)
    
    def align(self):
        """Align to byte boundary (discard bits left in buffer)."""
        self.bits_left = 0
        self.bit_buffer = 0