"""
Entropy Calculation Module
Implements Shannon entropy for adaptive algorithm selection.
"""

import math
from typing import Dict


def calculate_entropy(byte_array: bytes) -> float:
    """
    Calculate Shannon entropy of byte array in bits per byte.
    
    Formula: H = -Σ(p_i * log2(p_i))
    where p_i is the probability of byte i
    
    Args:
        byte_array: Raw bytes to analyze
        
    Returns:
        float: Entropy in bits/byte (0.0 to 8.0)
        
    Example:
        >>> data = b'\x00' * 100  # All same byte
        >>> calculate_entropy(data)
        0.0
        >>> data = bytes(range(256))  # Uniform distribution
        >>> calculate_entropy(data)
        8.0
    """
    if len(byte_array) == 0:
        return 0.0
    
    # Count frequencies
    from collections import Counter
    frequencies = Counter(byte_array)
    
    # Calculate probabilities
    total = len(byte_array)
    probabilities = [count / total for count in frequencies.values()]
    
    # Calculate entropy
    entropy = 0.0
    for p in probabilities:
        if p > 0:  # Avoid log(0)
            entropy -= p * math.log2(p)
    
    return entropy


def calculate_entropy_from_frequencies(frequency_dict: Dict[int, int]) -> float:
    """
    Calculate Shannon entropy from pre-computed frequency dictionary.
    
    Args:
        frequency_dict: Dictionary mapping byte value to frequency
        
    Returns:
        float: Entropy in bits/byte
    """
    if not frequency_dict:
        return 0.0
    
    total = sum(frequency_dict.values())
    
    entropy = 0.0
    for count in frequency_dict.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    
    return entropy


def estimate_compressibility(entropy: float) -> str:
    """
    Estimate how compressible data is based on entropy.
    
    Args:
        entropy: Entropy value in bits/byte
        
    Returns:
        str: Compressibility assessment
    """
    if entropy < 3.0:
        return "Highly compressible"
    elif entropy < 5.0:
        return "Moderately compressible"
    elif entropy < 7.0:
        return "Poorly compressible"
    elif entropy < 7.5:
        return "Nearly incompressible"
    else:
        return "Incompressible (likely already compressed)"
