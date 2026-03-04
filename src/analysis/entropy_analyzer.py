"""
Entropy-Efficiency Analysis Module
Provides academic-grade analysis for compression algorithms including:
- Shannon entropy calculation
- Average code length analysis  
- Compression efficiency metrics
- Block-wise entropy analysis for hybrid algorithm
"""

import math
from typing import Dict, List, Tuple
from collections import Counter

class EntropyAnalyzer:
    """Advanced entropy and efficiency analysis for compression algorithms."""
    
    @staticmethod
    def calculate_shannon_entropy(data: bytes) -> float:
        """Calculate Shannon entropy H(X) in bits per byte."""
        from src.core.entropy import calculate_entropy
        return calculate_entropy(data)
    
    @staticmethod
    def calculate_average_code_length(code_table: Dict[int, str], frequencies: Dict[int, int]) -> float:
        """Calculate average code length L_avg in bits per symbol."""
        if not code_table or not frequencies:
            return 0.0
        
        total_symbols = sum(frequencies.values())
        weighted_length = 0.0
        
        for symbol, frequency in frequencies.items():
            if symbol in code_table:
                code_length = len(code_table[symbol])
                weighted_length += (frequency / total_symbols) * code_length
        
        return weighted_length
    
    @staticmethod
    def calculate_compression_efficiency(entropy: float, avg_code_length: float) -> float:
        """Calculate compression efficiency η = H/L_avg × 100%."""
        if avg_code_length == 0:
            return 0.0
        return (entropy / avg_code_length) * 100.0
    
    @staticmethod
    def analyze_block_entropy(data: bytes, block_size: int = 1024*1024) -> List[Dict]:
        """Analyze entropy per block for hybrid algorithm evaluation."""
        blocks = []
        
        for i in range(0, len(data), block_size):
            block_data = data[i:i + block_size]
            if len(block_data) == 0:
                continue
                
            entropy = EntropyAnalyzer.calculate_shannon_entropy(block_data)
            blocks.append({
                'block_index': i // block_size,
                'start_byte': i,
                'end_byte': min(i + block_size, len(data)),
                'size': len(block_data),
                'entropy': entropy,
                'compressibility': EntropyAnalyzer._classify_compressibility(entropy)
            })
        
        return blocks
    
    @staticmethod
    def _classify_compressibility(entropy: float) -> str:
        """Classify data compressibility based on entropy."""
        from src.core.entropy import estimate_compressibility
        return estimate_compressibility(entropy)
    
    @staticmethod
    def comprehensive_analysis(data: bytes, algorithm_results: Dict) -> Dict:
        """Perform comprehensive entropy-efficiency analysis."""
        # Calculate base metrics
        entropy = EntropyAnalyzer.calculate_shannon_entropy(data)
        frequencies = Counter(data)
        
        analysis = {
            'file_size': len(data),
            'unique_symbols': len(frequencies),
            'shannon_entropy': entropy,
            'theoretical_minimum_bits': entropy * len(data),
            'compressibility_class': EntropyAnalyzer._classify_compressibility(entropy),
            'algorithms': {}
        }
        
        # Analyze each algorithm
        for algo_name, result in algorithm_results.items():
            
            # Use average_code_length if provided (best), otherwise estimate from ratio
            if 'average_code_length' in result:
                avg_length = result['average_code_length']
            else:
                # ratio = original_size / compressed_size
                # bits_per_symbol = (compressed_size * 8) / original_size = 8 / ratio
                ratio = result.get('compression_ratio', 1.0)
                avg_length = 8.0 / ratio if ratio > 0 else 8.0
            
            efficiency = EntropyAnalyzer.calculate_compression_efficiency(
                entropy, avg_length
            )
            
            analysis['algorithms'][algo_name] = {
                'average_code_length': avg_length,
                'compression_efficiency': efficiency,
                'compression_ratio': result.get('compression_ratio', 1.0),
                'space_saving': result.get('space_saving_percent', 0),
                'redundancy': max(0, avg_length - entropy),
                'theoretical_optimality': (entropy / avg_length) if avg_length > 0 else 0
            }
        
        return analysis