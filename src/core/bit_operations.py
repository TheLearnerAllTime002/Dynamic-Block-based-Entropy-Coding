"""
Bit-Level Operations Module
Provides BitWriter and BitReader for packing/unpacking variable-length codes.
"""

from typing import Optional


class BitWriter:
    """
    Writes individual bits to a file, packing them into bytes.
    Handles bit-level precision required for variable-length coding.
    """
    
    def __init__(self, filepath: str):
        """
        Initialize BitWriter.
        
        Args:
            filepath: Path to output file
        """
        self.filepath = filepath
        self.file_handle = open(filepath, 'wb')
        self.buffer = 0  # Current byte being built
        self.bit_count = 0  # Number of bits in buffer (0-7)
        self.total_bits_written = 0  # Track total bits for header
    
    def write_bit(self, bit: int) -> None:
        """
        Write a single bit (0 or 1).
        
        Args:
            bit: 0 or 1
        """
        if bit not in (0, 1):
            raise ValueError(f"Bit must be 0 or 1, got {bit}")
        
        # Add bit to buffer (shift left and OR with new bit)
        self.buffer = (self.buffer << 1) | bit
        self.bit_count += 1
        self.total_bits_written += 1
        
        # When buffer is full (8 bits), write byte to file
        if self.bit_count == 8:
            self.file_handle.write(bytes([self.buffer]))
            self.buffer = 0
            self.bit_count = 0
    
    def write_bits(self, bits: str) -> None:
        """
        Write a string of bits (e.g., '10110').
        
        Args:
            bits: String of '0' and '1' characters
        """
        for bit_char in bits:
            self.write_bit(1 if bit_char == '1' else 0)
    
    def write_bytes(self, data: bytes) -> None:
        """
        Write multiple bytes. Optimizes for aligned writing.
        """
        if self.bit_count == 0:
            # Already aligned, use fast write
            self.file_handle.write(data)
            self.total_bits_written += len(data) * 8
        else:
            # Fallback to bit-by-bit
            for byte in data:
                self.write_byte(byte)
    
    def flush(self) -> int:
        """
        Write remaining bits with padding zeros. Same as align().
        
        Returns:
            int: Number of padding bits added (0-7)
        """
        if self.bit_count > 0:
            # Pad remaining bits with zeros
            padding = 8 - self.bit_count
            self.buffer <<= padding
            self.file_handle.write(bytes([self.buffer]))
            self.buffer = 0
            self.bit_count = 0
            return padding
        return 0

    def align(self) -> int:
        """Alias for flush() to clarify intent in mixed bit/byte logic."""
        return self.flush()
    
    def write_byte(self, byte: int) -> None:
        """
        Write a full byte (8 bits).
        
        Args:
            byte: Integer 0-255
        """
        if not 0 <= byte <= 255:
            raise ValueError(f"Byte must be 0-255, got {byte}")
        
        if self.bit_count == 0:
            self.file_handle.write(bytes([byte]))
            self.total_bits_written += 8
        else:
            # Write each bit of the byte (fallback)
            for i in range(7, -1, -1):
                bit = (byte >> i) & 1
                self.write_bit(bit)

    def close(self) -> None:
        """Close the file handle."""
        if self.file_handle:
            self.file_handle.close()
    
    def __enter__(self):
        """Context manager support."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.close()


class BitReader:
    """
    Reads individual bits from a file.
    Handles bit-level precision for decoding variable-length codes.
    """
    
    def __init__(self, filepath: str):
        """
        Initialize BitReader.
        
        Args:
            filepath: Path to input file
        """
        self.filepath = filepath
        self.file_handle = open(filepath, 'rb')
        self.data = self.file_handle.read()  # Read entire file
        self.file_handle.close()
        
        self.byte_position = 0  # Current byte index
        self.bit_position = 0  # Current bit within byte (0-7)
        self.total_bytes = len(self.data)
    
    def read_bit(self) -> Optional[int]:
        """
        Read a single bit.
        
        Returns:
            int: 0 or 1, or None if end of file
        """
        if self.byte_position >= self.total_bytes:
            return None
        
        # Get current byte
        current_byte = self.data[self.byte_position]
        
        # Extract bit at current position (MSB first)
        bit = (current_byte >> (7 - self.bit_position)) & 1
        
        # Move to next bit
        self.bit_position += 1
        if self.bit_position == 8:
            self.bit_position = 0
            self.byte_position += 1
        
        return bit
    
    def read_bits(self, n: int) -> Optional[str]:
        """
        Read n bits and return as string.
        
        Args:
            n: Number of bits to read
            
        Returns:
            str: String of '0' and '1', or None if not enough bits
        """
        bits = []
        for _ in range(n):
            bit = self.read_bit()
            if bit is None:
                return None
            bits.append(str(bit))
        return ''.join(bits)
    
    def read_byte(self) -> Optional[int]:
        """
        Read 8 bits as a byte. Optimizes for alignment.
        """
        if self.bit_position == 0:
            if self.byte_position >= self.total_bytes:
                return None
            byte = self.data[self.byte_position]
            self.byte_position += 1
            return byte
        else:
            # Slow path crossing byte boundaries
            bits = self.read_bits(8)
            if bits is None:
                return None
            return int(bits, 2)
    
    def read_bytes(self, n: int) -> Optional[bytes]:
        """
        Read n bytes. Optimizes for alignment.
        """
        if self.bit_position == 0:
            end = self.byte_position + n
            if end > self.total_bytes:
                return None
            result = self.data[self.byte_position:end]
            self.byte_position = end
            return result
        else:
            result = bytearray()
            for _ in range(n):
                b = self.read_byte()
                if b is None: return None
                result.append(b)
            return bytes(result)

    def align(self) -> int:
        """Skip to next byte boundary (discard padding)."""
        if self.bit_position > 0:
            skipped = 8 - self.bit_position
            self.bit_position = 0
            self.byte_position += 1
            return skipped
        return 0

    def reset(self) -> None:
        """Reset to beginning of file."""
        self.byte_position = 0
        self.bit_position = 0

    def __enter__(self):
        """Context manager support."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        pass
