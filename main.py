#!/usr/bin/env python3
"""
Universal Lossless Data Compression System - Unified Entry Point
Supports both Interactive Menu and CLI workflows.
"""

import sys
import os
import argparse
import time
from pathlib import Path

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.compression.compressor import CompressionEngine
from src.compression.decompressor import DecompressionEngine
from src.algorithms.db_hec import DBHECCompressor, DBHECDecompressor
from src.algorithms.ocec import OCECCompressor, OCECDecompressor
from src.utils.validation import verify_lossless
from src.analysis.research_benchmark import ResearchBenchmark
from src.core.entropy import calculate_entropy, calculate_entropy_from_frequencies, estimate_compressibility
from src.core.binary_reader import read_binary_file
from src.core.frequency_analyzer import count_frequencies

# --- Visual Defaults ---
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_banner():
    print(f"""
{Colors.BLUE}{Colors.BOLD}======================================================================
  UNIVERSAL LOSSLESS DATA COMPRESSION SYSTEM
  OCEC (Novel Invention) | Hybrid | Huffman | Shannon-Fano
======================================================================{Colors.END}""")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

# --- Interactive Mode ---
def interactive_menu():
    while True:
        clear_screen()
        print_banner()
        print(f"\n{Colors.BOLD}MAIN MENU{Colors.END}")
        print("1. Compress a file")
        print("2. Decompress a file")
        print("3. Analyze file entropy")
        print("4. Run Research Benchmark (Compare all)")
        print("5. Verify file integrity (MD5)")
        print("0. Exit")
        
        choice = input(f"\n{Colors.CYAN}Enter choice (0-5): {Colors.END}").strip()
        
        if choice == '1':
            path = input("Enter file path to compress: ").strip()
            if os.path.exists(path):
                print("\nAlgorithms:")
                print("  O. OCEC (Novel Multi-Context Lossless)")
                print("  H. Hybrid DB-HEC (Adaptive Entropy)")
                print("  1. Huffman")
                print("  2. Shannon-Fano")
                algo_choice = input(f"{Colors.CYAN}Select algorithm (O/H/1/2) [O]: {Colors.END}").strip().upper() or 'O'
                
                if algo_choice == 'O':
                    out = path + ".ocec"
                    print(f"[*] Compressing (OCEC Invention)...")
                    stats = OCECCompressor().compress_file(path, out)
                    ext = ".ocec"
                elif algo_choice == 'H':
                    out = path + ".hyb"
                    print(f"[*] Compressing (Hybrid)...")
                    stats = DBHECCompressor.compress_file(path, out)
                    ext = ".hyb"
                elif algo_choice == '1':
                    out = path + ".huf"
                    print(f"[*] Compressing (Huffman)...")
                    stats = CompressionEngine().compress_file(path, out, algorithm='huffman')
                    ext = ".huf"
                elif algo_choice == '2':
                    out = path + ".shf"
                    print(f"[*] Compressing (Shannon-Fano)...")
                    stats = CompressionEngine().compress_file(path, out, algorithm='shannon_fano')
                    ext = ".shf"
                else:
                    print(f"{Colors.RED}Invalid selection.{Colors.END}")
                    input("\nPress Enter...")
                    continue

                print(f"[SUCCESS] Done! Ratio: {stats['compression_ratio']:.3f} (Saved as {out})")
            else: print(f"{Colors.RED}File not found.{Colors.END}")
            input("\nPress Enter...")
            
        elif choice == '2':
            path = input("Enter compressed file path: ").strip()
            if os.path.exists(path):
                out = "restored_" + Path(path).stem
                print(f"[*] Decompressing...")
                with open(path, 'rb') as f:
                    magic = f.read(4)
                    if magic == b'OCEC':
                        OCECDecompressor.decompress_file(path, out)
                    elif magic == b'HYB1':
                        DBHECDecompressor.decompress_file(path, out)
                    else:
                        DecompressionEngine().decompress_file(path, out)
                print(f"[SUCCESS] Restored to: {out}")
            else: print(f"{Colors.RED}File not found.{Colors.END}")
            input("\nPress Enter...")
            
        elif choice == '3':
            path = input("Enter file path to analyze: ").strip()
            if os.path.exists(path):
                data = read_binary_file(path)
                ent = calculate_entropy(data)
                print(f"\n📊 {Colors.BOLD}Analysis:{Colors.END}")
                print(f"   Size:    {len(data):,} bytes")
                print(f"   Entropy: {ent:.4f} bits/byte")
                print(f"   Quality: {estimate_compressibility(ent)}")
            else: print(f"{Colors.RED}File not found.{Colors.END}")
            input("\nPress Enter...")
            
        elif choice == '4':
            path = input("Enter file path to benchmark: ").strip()
            if os.path.exists(path):
                ResearchBenchmark().run_comprehensive_benchmark(path, parallel=True)
            else: print(f"{Colors.RED}File not found.{Colors.END}")
            input("\nPress Enter...")
            
        elif choice == '5':
            orig = input("Enter original file path: ").strip()
            rest = input("Enter restored file path: ").strip()
            if os.path.exists(orig) and os.path.exists(rest):
                ok = verify_lossless(orig, rest)
                if ok: print(f"[SUCCESS] IDENTICAL (100% Lossless)")
                else: print(f"[ERROR] MISMATCH (Data loss detected)")
            else: print(f"{Colors.RED}One or both files missing.{Colors.END}")
            input("\nPress Enter...")
            
        elif choice == '0':
            print("Goodbye!")
            break

# --- CLI Mode ---
def run_cli_workflow(args):
    print_banner()
    path = Path(args.path)
    if not path.exists():
        print(f"{Colors.RED}Error: File not found: {path}{Colors.END}")
        return

    if args.op == 'all' or args.op == 'benchmark':
        ResearchBenchmark().run_comprehensive_benchmark(str(path), parallel=True)
        if args.op == 'benchmark': return

    if args.op == 'all' or args.op == 'compress':
        algo = args.algo or 'hybrid'
        suffix = {'hybrid': '.hyb', 'huffman': '.huf', 'shannon_fano': '.shf'}[algo]
        out = args.out or (str(path) + suffix)
        
        print(f"\n[*] Compressing ({algo}): {path} -> {out}")
        if algo == 'hybrid':
            stats = DBHECCompressor.compress_file(str(path), out)
        else:
            stats = CompressionEngine().compress_file(str(path), out, algorithm=algo)
            
        print(f"[SUCCESS] Ratio: {stats['compression_ratio']:.4f} ({stats['space_saving_percent']:.2f}% saved)")
        if args.op == 'compress': return
        
        # If 'all', also decompress and verify
        restored = f"restored_{path.name}"
        print(f"\n[*] Decompressing and Verifying...")
        with open(out, 'rb') as f:
            magic = f.read(4)
            if magic == b'HYB1':
                DBHECDecompressor.decompress_file(out, restored)
            else:
                DecompressionEngine().decompress_file(out, restored)
                
        if verify_lossless(str(path), restored):
            print(f"[SUCCESS] SUCCESS: 100% Lossless Restoration Verified.")
        else:
            print(f"[ERROR] ERROR: Verification failed!")

    elif args.op == 'decompress':
        out = args.out or ("restored_" + path.name)
        print(f"[*] Decompressing: {path} -> {out}")
        with open(str(path), 'rb') as f:
            if f.read(4) == b'HYB1':
                DBHECDecompressor.decompress_file(str(path), out)
            else:
                DecompressionEngine().decompress_file(str(path), out)
        print(f"[SUCCESS] Decompression complete.")

def main():
    parser = argparse.ArgumentParser(description="Universal Lossless Compression System")
    parser.add_argument("path", nargs="?", help="Path to the file for processing (if empty, starts interactive menu)")
    parser.add_argument("--op", choices=['compress', 'decompress', 'benchmark', 'all'], default='all', help="Operation to perform")
    parser.add_argument("--algo", choices=['hybrid', 'huffman', 'shannon_fano'], default='hybrid', help="Algorithm for compression")
    parser.add_argument("--out", help="Custom output path")
    
    args = parser.parse_args()
    
    try:
        if args.path:
            run_cli_workflow(args)
        else:
            interactive_menu()
    except KeyboardInterrupt:
        print("\nAborted.")
    except Exception as e:
        print(f"\n{Colors.RED}Fatal Error: {e}{Colors.END}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
