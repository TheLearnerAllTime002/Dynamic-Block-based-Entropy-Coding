"""
DB-HEC: Dynamic Block-Based Hybrid Entropy Coding (Enhanced Version)
Research-grade optimization with Sparse Frequency Mapping and Delta Transformation.
"""

import os
import struct
import math
import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

from src.core.entropy import calculate_entropy
from src.core.frequency_analyzer import count_frequencies
from src.algorithms.huffman import HuffmanCoder
from src.algorithms.shannon_fano import ShannonFanoCoder
from src.core.dbhec_io import DBHECWriter, DBHECReader

@dataclass
class SegmentMetadata:
    mode_flag: int           # 0=Huff, 1=SF, 2=Raw
    transform_flag: int      # 0=None, 1=Delta
    entropy: float           # Empirical Shannon entropy H(S)
    original_size: int       # Bytes
    expected_length: float   # L_k in bits
    redundancy: float        # L_k - H(S)
    freq_table: bytes        # Serialized frequencies
    bitstream: str           # Encoded bits

def apply_delta(data: bytes) -> bytes:
    """Apply delta encoding (differential pulse-code modulation)."""
    if not data: return data
    arr = np.frombuffer(data, dtype=np.uint8).astype(np.int16)
    delta = np.zeros_like(arr, dtype=np.uint8)
    delta[0] = arr[0]
    delta[1:] = (arr[1:] - arr[:-1]) & 0xFF
    return delta.tobytes()

def undo_delta(data: bytes) -> bytes:
    """Reverse delta encoding."""
    if not data: return data
    delta = np.frombuffer(data, dtype=np.uint8).astype(np.int16)
    restored = np.zeros_like(delta, dtype=np.uint8)
    restored[0] = delta[0]
    current = delta[0]
    for i in range(1, len(delta)):
        current = (current + delta[i]) & 0xFF
        restored[i] = current
    return restored.tobytes()

def serialize_frequencies(freq: Dict[int, int]) -> bytes:
    """Enhanced Sparse Serialization using 32-byte bitmask."""
    mask = 0
    present_symbols = []
    for i in range(256):
        if i in freq and freq[i] > 0:
            mask |= (1 << i)
            present_symbols.append(i)
    data = bytearray(mask.to_bytes(32, byteorder='little'))
    for sym in present_symbols:
        data.extend(struct.pack('>I', freq[sym]))
    return bytes(data)

def deserialize_frequencies(freq_bytes: bytes) -> Dict[int, int]:
    """Reverse sparse serialization."""
    if len(freq_bytes) < 32: return {}
    mask_val = int.from_bytes(freq_bytes[:32], byteorder='little')
    freq = {}
    offset = 32
    for i in range(256):
        if (mask_val >> i) & 1:
            if offset + 4 > len(freq_bytes): break
            count = struct.unpack('>I', freq_bytes[offset:offset+4])[0]
            freq[i] = count
            offset += 4
    return freq

def calculate_empirical_entropy(data: bytes) -> float:
    """Compute empirical Shannon entropy H(B) over the byte alphabet."""
    if not data: return 0.0
    freqs = count_frequencies(data)
    total = len(data)
    entropy = 0.0
    for count in freqs.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy

def estimate_expected_length(coder, freq_dict: Dict[int, int]) -> float:
    """Estimate expected code length L_k = sum p(i) * l_k(i) bits per symbol."""
    if not freq_dict: return 0.0
    code_table = coder.get_code_table()
    total = sum(freq_dict.values())
    expected_bits = 0.0
    for sym, count in freq_dict.items():
        if sym in code_table:
            expected_bits += (count / total) * len(code_table[sym])
    return expected_bits

def analyze_segment(segment_bytes: bytes) -> SegmentMetadata:
    """
    Theoretically grounded segment processor.
    Selects k* = arg min_k (L_k - H) across Raw and Delta models.
    Ensures Zero-Expansion Invariant |C(S)| <= |S| bits.
    """
    # Candidate Models
    raw_data = segment_bytes
    delta_data = apply_delta(segment_bytes)
    
    h_raw = calculate_empirical_entropy(raw_data)
    h_delta = calculate_empirical_entropy(delta_data)
    
    candidates = []
    
    # Model 1: Raw Data candidates
    freq_raw = count_frequencies(raw_data)
    # Huffman
    huff = HuffmanCoder()
    huff.build_tree(freq_raw)
    l_huff_raw = estimate_expected_length(huff, freq_raw)
    candidates.append((0, 0, h_raw, l_huff_raw, huff, raw_data, freq_raw))
    
    # Shannon-Fano
    sf = ShannonFanoCoder()
    sf.build_tree(freq_raw)
    l_sf_raw = estimate_expected_length(sf, freq_raw)
    candidates.append((1, 0, h_raw, l_sf_raw, sf, raw_data, freq_raw))
    
    # Model 2: Delta Data candidates
    freq_delta = count_frequencies(delta_data)
    # Huffman Delta
    huff_d = HuffmanCoder()
    huff_d.build_tree(freq_delta)
    l_huff_delta = estimate_expected_length(huff_d, freq_delta)
    candidates.append((0, 1, h_delta, l_huff_delta, huff_d, delta_data, freq_delta))
    
    # Shannon-Fano Delta
    sf_d = ShannonFanoCoder()
    sf_d.build_tree(freq_delta)
    l_sf_delta = estimate_expected_length(sf_d, freq_delta)
    candidates.append((1, 1, h_delta, l_sf_delta, sf_d, delta_data, freq_delta))
    
    # Selection k* = argmin(L_k - H)
    # We use (L_k - H) * total_symbols to compare total bit redundancy
    best_cand = min(candidates, key=lambda x: x[3] - x[2])
    
    mode, trans, ent, l_k, coder, work_data, freq_dict = best_cand
    
    # Zero-Expansion Check: L_k (bits per symbol) vs 8 bits per symbol (Raw)
    # Formally: Total bits including frequency table overhead
    freq_bytes = serialize_frequencies(freq_dict)
    header_overhead_bits = 8 + 32 + (len(freq_bytes) * 8) + 64 # Flags, Size, Freq, PayloadLen
    total_bits = (l_k * len(segment_bytes)) + header_overhead_bits
    
    if total_bits >= (len(segment_bytes) * 8):
        # Zero-Expansion Fallback to Raw
        return SegmentMetadata(
            mode_flag=2, transform_flag=0, entropy=h_raw,
            original_size=len(segment_bytes), expected_length=8.0,
            redundancy=8.0 - h_raw, freq_table=b'', bitstream=""
        )

    return SegmentMetadata(
        mode_flag=mode, transform_flag=trans, entropy=ent,
        original_size=len(segment_bytes), expected_length=l_k,
        redundancy=l_k - ent, freq_table=freq_bytes,
        bitstream=coder.encode(work_data)
    )

class DBHECCompressor:
    @staticmethod
    def compress_file(input_path: str, output_path: str, block_size: int = 1<<20, epsilon: float = 7.5):
        """
        Adaptive segmentation based on entropy stability.
        Merging consecutive blocks if |H(Bi) - H(Bi+1)| <= epsilon.
        (Epsilon here acts as the 'Entropy Sensitivity' threshold)
        """
        with open(input_path, 'rb') as f:
            data = f.read()
        if not data: raise ValueError("Empty file")
        
        # 1. Initial fixed-block entropy analysis
        base_blocks = [data[i:i+block_size] for i in range(0, len(data), block_size)]
        block_entropies = [calculate_empirical_entropy(b) for b in base_blocks]
        
        # 2. Adaptive merging
        segments = []
        if not base_blocks: return {}
        
        current_segment_data = bytearray(base_blocks[0])
        current_h = block_entropies[0]
        
        for i in range(1, len(base_blocks)):
            next_h = block_entropies[i]
            if abs(current_h - next_h) <= epsilon:
                # Merge
                current_segment_data.extend(base_blocks[i])
                # Update current_h (mean entropy of merged segment)
                current_h = calculate_empirical_entropy(bytes(current_segment_data))
            else:
                # Seal segment and start new
                segments.append(bytes(current_segment_data))
                current_segment_data = bytearray(base_blocks[i])
                current_h = next_h
        segments.append(bytes(current_segment_data))
        
        # 3. Process segments
        processed_segments = [analyze_segment(s) for s in segments]
        
        with DBHECWriter(output_path) as writer:
            writer.write_raw_string('HYB1', 4)
            writer.write_byte(0x04) # Version 4 (Theoretical Adaptive)
            writer.write_string(os.path.splitext(input_path)[1])
            writer.write_uint32(len(processed_segments))
            writer.write_uint32(block_size) # Base block size as reference
            
            for i, sd in enumerate(processed_segments):
                writer.align()
                writer.write_byte(sd.mode_flag | (sd.transform_flag << 4))
                writer.write_uint32(sd.original_size)
                
                if sd.mode_flag == 2:
                    writer.write_bytes(segments[i])
                else:
                    writer.write_uint32(len(sd.freq_table))
                    writer.write_bytes(sd.freq_table)
                    writer.write_uint64(len(sd.bitstream))
                    writer.write_bits(sd.bitstream)
            writer.flush()
            
        orig_size = os.path.getsize(input_path)
        comp_size = os.path.getsize(output_path)
        return {
            "original_size": orig_size,
            "compressed_size": comp_size,
            "compression_ratio": orig_size / comp_size if comp_size > 0 else 0,
            "space_saving_percent": (1 - (comp_size / orig_size)) * 100 if orig_size > 0 else 0
        }

class DBHECDecompressor:
    @staticmethod
    def decompress_file(input_path: str, output_path: str):
        with DBHECReader(input_path) as reader:
            magic = reader.read_string(4)
            version = reader.read_byte()
            ext = reader.read_string()
            num_segments = reader.read_uint32()
            base_block_size = reader.read_uint32()
            
            restored = []
            for _ in range(num_segments):
                reader.align()
                flags = reader.read_byte()
                mode = flags & 0x0F
                transform = (flags >> 4) & 0x0F
                orig_size = reader.read_uint32()
                
                if mode == 2:
                    seg_data = reader.read_bytes(orig_size)
                else:
                    f_size = reader.read_uint32()
                    freq = deserialize_frequencies(reader.read_bytes(f_size))
                    payload_bits = reader.read_uint64()
                    
                    coder = HuffmanCoder() if mode == 0 else ShannonFanoCoder()
                    coder.build_tree(freq)
                    seg_data = coder.decode(reader.read_bits(payload_bits))
                
                if transform == 1:
                    seg_data = undo_delta(seg_data)
                restored.append(seg_data)
                
        with open(output_path, 'wb') as f:
            for b in restored: f.write(b)
        return {"output_path": output_path, "decompressed_size": sum(len(b) for b in restored)}
