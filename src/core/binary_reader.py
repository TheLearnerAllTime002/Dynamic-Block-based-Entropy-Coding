"""
Binary File Reader Module
Handles reading files as raw byte streams (0-255) for universal compression.
"""

from typing import Optional
import os


def read_binary_file(filepath: str, chunk_size: Optional[int] = None) -> bytes:
    """
    Read a file in binary mode and return as bytes.
    
    Args:
        filepath: Path to the file to read
        chunk_size: If specified, read file in chunks (for large files)
        
    Returns:
        bytes: Raw byte array (uint8 values 0-255)
        
    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    file_size = os.path.getsize(filepath)
    
    # For files larger than 1GB, recommend chunked reading
    if file_size > 1_000_000_000 and chunk_size is None:
        print(f"Warning: Large file ({file_size / 1e9:.2f} GB). Consider using chunk_size parameter.")
    
    try:
        with open(filepath, 'rb') as f:
            if chunk_size:
                # Read in chunks for memory efficiency
                data = bytearray()
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    data.extend(chunk)
                return bytes(data)
            else:
                # Read entire file at once
                return f.read()
    except IOError as e:
        raise IOError(f"Error reading file {filepath}: {e}")


def write_binary_file(filepath: str, data: bytes) -> None:
    """
    Write binary data to a file.
    
    Args:
        filepath: Path to output file
        data: Binary data to write
        
    Raises:
        IOError: If file cannot be written
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        
        with open(filepath, 'wb') as f:
            f.write(data)
    except IOError as e:
        raise IOError(f"Error writing file {filepath}: {e}")


def get_file_extension(filepath: str) -> str:
    """
    Extract file extension from filepath.
    
    Args:
        filepath: Path to file
        
    Returns:
        str: File extension including dot (e.g., '.mp4')
    """
    return os.path.splitext(filepath)[1]


def get_file_size(filepath: str) -> int:
    """
    Get file size in bytes.
    
    Args:
        filepath: Path to file
        
    Returns:
        int: File size in bytes
    """
    return os.path.getsize(filepath)
