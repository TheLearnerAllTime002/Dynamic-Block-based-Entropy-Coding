"""
Advanced Benchmarking Module for Research-Grade Results
Includes information-theoretic analysis and matplotlib visualizations.
"""

import time
import psutil
import os
import tempfile
import matplotlib.pyplot as plt
import numpy as np
import math
from pathlib import Path
from typing import Dict, List, Optional
import json
import csv
from src.core.entropy import calculate_entropy

class MemoryProfiler:
    """Memory usage profiler for compression algorithms."""
    def __init__(self):
        self._process = psutil.Process()
        self.reset()
    
    def reset(self):
        self.baseline_memory = self._process.memory_info().rss / 1024 / 1024
        self.peak_memory = self.baseline_memory
    
    def monitor(self):
        current = self._process.memory_info().rss / 1024 / 1024
        self.peak_memory = max(self.peak_memory, current)
        return current
    
    def get_peak_usage(self):
        self.monitor()
        usage = self.peak_memory - self.baseline_memory
        return max(2.0, usage)

def _run_single_benchmark(algorithm: str, input_file: str, block_size: int = 1<<20, threshold: float = 7.5):
    from src.compression.compressor import CompressionEngine
    from src.compression.decompressor import DecompressionEngine
    from src.algorithms.db_hec import DBHECCompressor, DBHECDecompressor
    from src.algorithms.ocec import OCECCompressor, OCECDecompressor
    from src.utils.validation import verify_lossless
    from src.utils.metrics import calculate_compression_ratio, calculate_space_saving
    
    profiler = MemoryProfiler()
    engine = CompressionEngine()
    decompressor = DecompressionEngine()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{algorithm}') as tmp_compressed:
        compressed_path = tmp_compressed.name
    with tempfile.NamedTemporaryFile(delete=False, suffix='_decompressed') as tmp_decompressed:
        decompressed_path = tmp_decompressed.name
        
    try:
        file_size = os.path.getsize(input_file)
        
        # --- COMPRESSION ---
        profiler.reset()
        start_time = time.perf_counter()
        if algorithm == 'hybrid':
            DBHECCompressor.compress_file(input_file, compressed_path, block_size=block_size, epsilon=threshold)
        elif algorithm == 'ocec':
            OCECCompressor().compress_file(input_file, compressed_path)
        else:
            engine.compress_file(input_file, compressed_path, algorithm)
        compress_wall_time = time.perf_counter() - start_time
        compress_peak_memory = profiler.get_peak_usage()
        compressed_size = os.path.getsize(compressed_path)
        
        # --- DECOMPRESSION ---
        profiler.reset()
        start_time = time.perf_counter()
        with open(compressed_path, 'rb') as f:
            magic = f.read(4)
        if magic == b'HYB1':
            DBHECDecompressor.decompress_file(compressed_path, decompressed_path)
        elif magic == b'OCEC':
            OCECDecompressor.decompress_file(compressed_path, decompressed_path)
        else:
            decompressor.decompress_file(compressed_path, decompressed_path)
        decompress_wall_time = time.perf_counter() - start_time
        decompress_peak_memory = profiler.get_peak_usage()
        
        # --- INFORMATION THEORETIC ANALYSIS ---
        is_lossless = verify_lossless(input_file, decompressed_path)
        file_data = np.fromfile(input_file, dtype=np.uint8)
        H = calculate_entropy(file_data)
        L = (compressed_size * 8) / file_size if file_size > 0 else 0
        
        # Metrics
        eta = H / L if L > 0 else 0
        R = (L - H) / H if H > 0 else 0
        
        c_adapt = (compressed_size - (H/L * file_size / 8)) / file_size if file_size > 0 else 0

        return {
            'algorithm': f"{algorithm} (B:{block_size//1024}K, T:{threshold})",
            'algo_base': algorithm,
            'block_size': block_size,
            'threshold': threshold,
            'file_size': file_size,
            'compressed_size': compressed_size,
            'compression_ratio': calculate_compression_ratio(file_size, compressed_size),
            'space_saving_percent': calculate_space_saving(file_size, compressed_size),
            'L': L,
            'H': H,
            'entropy_efficiency_eta': eta,
            'relative_redundancy_R': R,
            'adaptation_cost_C_adapt': c_adapt,
            'compress_wall_time': compress_wall_time,
            'compress_peak_memory': compress_peak_memory,
            'decompress_wall_time': decompress_wall_time,
            'decompress_peak_memory': decompress_peak_memory,
            'compress_throughput': (file_size / 1024 / 1024) / compress_wall_time if compress_wall_time > 0 else 0,
            'decompress_throughput': (file_size / 1024 / 1024) / decompress_wall_time if decompress_wall_time > 0 else 0,
            'lossless': is_lossless
        }
    finally:
        for p in [compressed_path, decompressed_path]:
            if os.path.exists(p):
                try: os.remove(p)
                except: pass

class ResearchBenchmark:
    """Research-grade benchmarking with information-theoretic metrics."""
    def __init__(self):
        self.results = []
    
    def run_comprehensive_benchmark(self, input_file: str, output_dir: str = None, 
                                 parallel: bool = True, block_sizes: List[int] = None, 
                                 thresholds: List[float] = None):
        if output_dir is None:
            output_dir = str(Path(input_file).parent / "benchmark_results")
        os.makedirs(output_dir, exist_ok=True)
        
        # Defaults if not provided
        if not block_sizes: block_sizes = [1<<20]
        if not thresholds: thresholds = [7.5]
        
        algorithms = ['huffman', 'shannon_fano', 'hybrid', 'ocec']
        print(f"\n[BENCHMARK] Running Parametric Research Sweep...")
        
        results = []
        for b_size in block_sizes:
            for t_val in thresholds:
                for algo in algorithms:
                    print(f"[TEST] {algo} | Block: {b_size//1024}KB | Threshold: {t_val}")
                    results.append(_run_single_benchmark(algo, input_file, block_size=b_size, threshold=t_val))
        
        self.create_publication_plots(results, output_dir)
        self.display_terminal_results(results)
        self.export_results(results, output_dir, input_file)
        return results

    def create_publication_plots(self, results: List[Dict], output_dir: str):
        plt.style.use('seaborn-v0_8')
        algorithms = [r['algorithm'] for r in results]
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        ax4.remove()
        ax4 = fig.add_subplot(2, 2, 4, projection='polar')
        
        # 1. Entropy Efficiency (eta)
        etas = [r['entropy_efficiency_eta'] for r in results]
        ax1.bar(algorithms, etas, color=['#2E86AB', '#A23B72', '#F18F01'], alpha=0.8)
        ax1.set_title('Entropy Efficiency ($\eta = H/L$)', fontweight='bold')
        ax1.set_ylim(0, 1.1)
        
        # 2. Relative Redundancy (R)
        redundancies = [r['relative_redundancy_R'] for r in results]
        ax2.bar(algorithms, redundancies, color=['#2E86AB', '#A23B72', '#F18F01'], alpha=0.8)
        ax2.set_title('Relative Redundancy ($R = (L-H)/H$)', fontweight='bold')
        
        # 3. Adaptation Cost (C_adapt)
        costs = [r['adaptation_cost_C_adapt'] for r in results]
        ax3.bar(algorithms, costs, color=['#2E86AB', '#A23B72', '#F18F01'], alpha=0.8)
        ax3.set_title('Normalized Adaptation Cost ($C_{adapt}$)', fontweight='bold')
        
        # 4. Overall Informational Profile (Radar)
        metrics = ['$\eta$', '1-R', '1-C_adapt', 'Speed']
        angles = np.linspace(0, 2*np.pi, len(metrics), endpoint=False).tolist()
        angles += angles[:1]
        ax4.set_thetagrids(np.degrees(angles[:-1]), metrics)
        
        for i, r in enumerate(results):
            data = [
                r['entropy_efficiency_eta'],
                max(0, 1 - r['relative_redundancy_R']),
                max(0, 1 - r['adaptation_cost_C_adapt'] * 100), # scaled for visual
                min(1.0, r['compress_throughput']/100.0)
            ]
            data += data[:1]
            ax4.plot(angles, data, 'o-', linewidth=2, label=r['algorithm'])
            ax4.fill(angles, data, alpha=0.1)
        
        ax4.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
        plt.tight_layout()
        plt.savefig(f"{output_dir}/info_theory_report.png", dpi=300)
        plt.close()

    def display_terminal_results(self, results: List[Dict]):
        print("\n" + "=" * 100)
        print("RESULTS-REPORT: INFORMATION-THEORETIC BENCHMARK RESULTS")
        print("=" * 100)
        print(f"{'Algorithm':<15} {'H':<8} {'L':<8} {'Efficiency (η)':<15} {'Redundancy (R)':<15} {'C_adapt':<12}")
        print("-" * 100)
        for r in results:
            print(f"{r['algorithm']:<15} {r['H']:<8.4f} {r['L']:<8.4f} "
                  f"{r['entropy_efficiency_eta']:<15.4f} {r['relative_redundancy_R']:<15.4f} {r['adaptation_cost_C_adapt']:<12.6f}")
        print("-" * 100)

    def export_results(self, results: List[Dict], output_dir: str, input_file: str):
        data = {'file': input_file, 'timestamp': time.ctime(), 'results': results}
        with open(f"{output_dir}/info_results.json", 'w') as f:
            json.dump(data, f, indent=2)
        with open(f"{output_dir}/info_results.csv", 'w', newline='') as f:
            if results:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)