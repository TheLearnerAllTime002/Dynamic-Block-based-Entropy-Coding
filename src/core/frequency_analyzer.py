"""
Frequency Analysis Module
Counts byte occurrences for building compression trees.
"""

from typing import Dict
from collections import Counter


def count_frequencies(byte_array: bytes) -> Dict[int, int]:
    """
    Count the frequency of each byte value (0-255) in the input data.
    
    Args:
        byte_array: Raw bytes to analyze
        
    Returns:
        Dict[int, int]: Dictionary mapping byte value to frequency count
        
    Example:
        >>> data = b'hello'
        >>> freqs = count_frequencies(data)
        >>> freqs[ord('l')]
        2
    """
    if len(byte_array) == 0:
        return {}
    
    # Use Counter for efficient frequency counting
    frequency_dict = Counter(byte_array)
    
    # Ensure all values are integers (byte values 0-255)
    return {int(byte): int(count) for byte, count in frequency_dict.items()}


def calculate_probabilities(frequency_dict: Dict[int, int]) -> Dict[int, float]:
    """
    Convert frequency counts to probabilities.
    
    Args:
        frequency_dict: Dictionary of byte frequencies
        
    Returns:
        Dict[int, float]: Dictionary mapping byte value to probability
    """
    if not frequency_dict:
        return {}
    
    total = sum(frequency_dict.values())
    
    return {byte: count / total for byte, count in frequency_dict.items()}


def get_sorted_symbols(frequency_dict: Dict[int, int], reverse: bool = True) -> list:
    """
    Get symbols sorted by frequency.
    
    Args:
        frequency_dict: Dictionary of byte frequencies
        reverse: If True, sort descending (most frequent first)
        
    Returns:
        list: List of (byte, frequency) tuples sorted by frequency
    """
    return sorted(frequency_dict.items(), key=lambda x: x[1], reverse=reverse)
