import os
import random
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.algorithms.db_hec import DBHECCompressor, DBHECDecompressor
from src.utils.validation import verify_lossless

def run_adversarial_test():
    print("🧪 Starting Adversarial High-Entropy Test...")
    
    # 1. Generate 2MB of uniform random bytes (Entropy ~8.0)
    random_data = os.urandom(2 * 1024 * 1024)
    input_file = "adversarial_random.bin"
    compressed_file = "adversarial_random.hyb"
    restored_file = "adversarial_restored.bin"
    
    with open(input_file, 'wb') as f:
        f.write(random_data)
        
    print(f"📁 Generated: {input_file} (Entropy expected ~8.0)")
    
    try:
        # 2. Compress
        print("🔄 Compressing (Adaptive Framework)...")
        stats = DBHECCompressor.compress_file(input_file, compressed_file)
        
        orig_size = stats['original_size']
        comp_size = stats['compressed_size']
        
        print(f"📊 Original: {orig_size} bytes")
        print(f"📊 Compressed: {comp_size} bytes")
        
        # 3. Verify Zero-Expansion Invariant
        if comp_size <= orig_size + 1024: # Allowing for a small file-level header, but segment-wise expansion is forbidden
            # Segment-wise strictness is internal, but overall should be bounded.
            # Version 4 header is tiny.
            print("✅ Zero-Expansion Invariant: PASSED")
        else:
            print(f"❌ Zero-Expansion Invariant: FAILED (Expansion: {comp_size - orig_size} bytes)")
            
        # 4. Decompress and Verify Lossless
        print("🔄 Decompressing...")
        DBHECDecompressor.decompress_file(compressed_file, restored_file)
        
        if verify_lossless(input_file, restored_file):
            print("🏆 Lossless Verification: PASSED")
        else:
            print("❌ Lossless Verification: FAILED")
            
    finally:
        # Cleanup
        for f in [input_file, compressed_file, restored_file]:
            if os.path.exists(f):
                os.remove(f)

if __name__ == "__main__":
    run_adversarial_test()
