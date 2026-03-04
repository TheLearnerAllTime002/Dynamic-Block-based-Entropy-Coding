"""
Validation and Metrics Utilities
MD5 verification and performance measurements.
"""

import hashlib
import time
from typing import Optional


def calculate_md5(filepath: str) -> str:
    """
    Calculate MD5 hash of a file.
    
    Args:
        filepath: Path to file
        
    Returns:
        str: MD5 hash as hexadecimal string
    """
    md5_hash = hashlib.md5()
    
    with open(filepath, 'rb') as f:
        # Read in chunks for memory efficiency
        for chunk in iter(lambda: f.read(4096), b''):
            md5_hash.update(chunk)
    
    return md5_hash.hexdigest()


def verify_lossless(original_path: str, decompressed_path: str) -> bool:
    """
    Verify that decompression is lossless by comparing MD5 hashes.
    
    Args:
        original_path: Path to original file
        decompressed_path: Path to decompressed file
        
    Returns:
        bool: True if hashes match (lossless), False otherwise
    """
    print("\nVerifying lossless compression...")
    
    original_md5 = calculate_md5(original_path)
    decompressed_md5 = calculate_md5(decompressed_path)
    
    match = original_md5 == decompressed_md5
    
    print(f"  Original MD5:     {original_md5}")
    print(f"  Decompressed MD5: {decompressed_md5}")
    print(f"  Status: {'OK - MATCH (Lossless)' if match else 'FAIL - MISMATCH (Data loss!)'}")
    
    return match


def calculate_compression_ratio(original_size: int, compressed_size: int) -> float:
    """
    Calculate compression ratio.
    
    Args:
        original_size: Original file size in bytes
        compressed_size: Compressed file size in bytes
        
    Returns:
        float: Compression ratio (original/compressed)
    """
    if compressed_size == 0:
        return 0.0
    
    return original_size / compressed_size


def calculate_space_saving(original_size: int, compressed_size: int) -> float:
    """
    Calculate space saving percentage.
    
    Args:
        original_size: Original file size in bytes
        compressed_size: Compressed file size in bytes
        
    Returns:
        float: Space saving as percentage
    """
    if original_size == 0:
        return 0.0
    
    return ((original_size - compressed_size) / original_size) * 100


def measure_throughput(file_size: int, time_taken: float) -> float:
    """
    Calculate throughput in MB/s.
    
    Args:
        file_size: File size in bytes
        time_taken: Time taken in seconds
        
    Returns:
        float: Throughput in MB/s
    """
    if time_taken == 0:
        return 0.0
    
    mb_size = file_size / (1024 * 1024)
    return mb_size / time_taken


class Timer:
    """Context manager for timing operations."""
    
    def __init__(self, description: str = "Operation"):
        self.description = description
        self.start_time = None
        self.elapsed = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = time.time() - self.start_time
        print(f"{self.description} took {self.elapsed:.3f} seconds")
