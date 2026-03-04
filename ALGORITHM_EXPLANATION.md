# OCEC Research: Technical Documentation of Compression Algorithms

This document provides a research-grade explanation of the four primary compression algorithms implemented in the OCEC Lossless Transmission Suite.

---

## 1. Traditional Entropy Coders

These algorithms form the foundation of our entropy-modulated system. They operate by replacing high-frequency symbols with shorter bit-patterns.

### A. Shannon-Fano Coding
**Strategy:** Top-Down Recursive Splitting
1. **Symbol Sorting:** Symbols are sorted by their empirical probability.
2. **Recursive Partitioning:** The symbol list is divided into two parts such that the sum of probabilities in each part is as balanced as possible.
3. **Bit Allocation:** Symbols in the first half receive a '0' bit, while the second half receives a '1' bit. This repeats until only one symbol remains in each leaf.
*Note: While historically significant, Shannon-Fano does not always achieve the optimal prefix code, which led to the development of Huffman Coding.*

### B. Huffman Coding
**Strategy:** Bottom-Up Tree Construction
1. **Frequency Mapping:** A frequency table is generated for the entire bitstream.
2. **Priority Queue Build:** Every unique symbol is treated as a leaf node and placed in a Min-Heap (Priority Queue) based on frequency.
3. **Iterative Merging:** The two nodes with the lowest frequencies are popped and merged into a parent node whose frequency is the sum of its children. This continues until a single root node remains.
*Note: Huffman Coding is mathematically proven to generate the optimal prefix-free code for a given discrete probability distribution.*

---

## 2. Advanced Adaptive Frameworks

These frameworks enhance basic entropy coding by introducing context-awareness and segmented modulation.

### C. DB-HEC (Dynamic Block-Based Hybrid Entropy Coding)
**Category:** Segmented Adaptive Hybrid
DB-HEC treats the file not as a static entity, but as a series of evolving contexts.

- **Entropy Sensitivity ($\epsilon$):** The system analyzes blocks of data and calculates their Shannon Entropy. If the difference in entropy between two consecutive blocks exceeds $\epsilon$, the system forces a segment break.
- **Model Selection:** For each segment, DB-HEC tests four candidate models:
  - Huffman (Raw)
  - Huffman (Delta-Transformed)
  - Shannon-Fano (Raw)
  - Shannon-Fano (Delta-Transformed)
- **Zero-Expansion Invariant:** If no model can compress a segment without increasing its size (due to header overhead), the system falls back to a "Raw" mode, ensuring the compressed file never exceeds the original size.

### D. OCEC (Omni-Context Entropy Coding)
**Category:** Invention / High-Efficiency Multi-Layer
OCEC is the flagship research algorithm that introduces "Context-Shift" logic and recursive analysis.

1. **Layer 1: Contextual Dictionary Modeling**  
   Before symbol encoding, OCEC runs a sliding-window analysis (similar to LZ-variants) to identify long repeating strings. These are replaced with (offset, length) pointers, significantly stripping redundancy from structured data.

2. **Layer 2: Table Inheritance Logic**  
   Unlike DB-HEC, which stores frequency tables for every segment, OCEC calculates a "Similarity Correlation" between tables. If a new segment's distribution is $>90\%$ similar to the previous one, it **inherits** the table, eliminating the metadata overhead and increasing net efficiency ($\eta$).

3. **Layer 3: Recursive Bit-Macro Pass**  
   The final bitstream is treated as raw input. OCEC scans for recurring 8-bit sequences (Macros) within the *already compressed* bits and performs a secondary substitution. This permits the compression of high-entropy noise that survives Layers 1 and 2.

---

## Summary Comparison Table

| Algorithm | Model Construction | Context Awareness | Overhead Strategy | Primary Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **Huffman** | Bottom-Up | Low (Global) | Minimal | Static, balanced data |
| **Shannon-Fano** | Top-Down | Low (Global) | Minimal | Theoretical research |
| **DB-HEC** | Hybrid Adaptive | Medium (Local) | Sparse Mapping | Heterogeneous streams |
| **OCEC** | Multi-Layer | High (Structural) | Table Inheritance | Flagship research target |

---
**Author:** Arjun Mitra  
**Project:** OCEC Lossless Transmission Portal (2026)
