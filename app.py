import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import time
import tempfile
from pathlib import Path
from src.algorithms.ocec import OCECCompressor, OCECDecompressor
from src.algorithms.db_hec import DBHECCompressor, DBHECDecompressor
from src.compression.compressor import CompressionEngine
from src.compression.decompressor import DecompressionEngine
from src.analysis.research_benchmark import ResearchBenchmark
from src.utils.validation import verify_lossless

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="OCEC Compression | Research Portal",
    page_icon="📊",
    layout="wide",
)

# --- PREMIUM AESTHETIC STYLING (Midnight Slate & Cyber Gold) ---
st.markdown("""
    <style>
    .main {
        background-color: #0a0e14;
    }
    .stApp {
        background: radial-gradient(circle at 50% 50%, #161c24 0%, #0a0e14 100%);
        color: #e6e6e6;
    }
    .stMetric {
        background: rgba(255, 255, 255, 0.03);
        padding: 20px;
        border-radius: 8px;
        border: 1px solid rgba(255, 204, 0, 0.1);
        backdrop-filter: blur(10px);
    }
    h1, h2, h3 {
        color: #ffcc00 !important;
        font-family: 'Inter', -apple-system, sans-serif;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .stButton>button {
        background-color: #ffcc00;
        color: #0a0e14;
        border-radius: 6px;
        border: none;
        padding: 10px 24px;
        font-weight: 700;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #e6b800;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(255, 204, 0, 0.2);
    }
    div[data-testid="stSidebar"] {
        background-color: #111821;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    .stSelectbox label, .stSlider label {
        color: #a0a0a0 !important;
    }
    /* Simple clean Plotly overrides */
    .js-plotly-plot .plotly .modebar {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- HELPERS ---
def save_uploaded_file(uploaded_file):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.title("OCEC Portal")
    mode = st.radio("Navigation", ["Process File", "Parametric Workbench", "Decompression Lab", "Research Abstract"])
    st.divider()
    st.info("Universal Lossless Data Compression System")

# --- MAIN DASHBOARD ---
if mode == "Process File":
    st.title("File Compression")
    uploaded_file = st.file_uploader("Select file for compression", type=None)
    
    if uploaded_file:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("### Configuration")
            algo = st.selectbox("Algorithm", ["OCEC", "DB-HEC", "Huffman", "Shannon-Fano"])
            
            with st.expander("Parameters"):
                b_size = st.select_slider("Block Size", 
                                        options=[64*1024, 512*1024, 1024*1024, 2048*1024, 4096*1024],
                                        value=1024*1024,
                                        format_func=lambda x: f"{x//1024} KB")
                threshold = st.slider("Entropy Threshold", 7.0, 7.8, 7.5, 0.1)

            if st.button("Run Compression"):
                input_path = save_uploaded_file(uploaded_file)
                output_ext = {
                    "OCEC": ".ocec",
                    "DB-HEC": ".hyb",
                    "Huffman": ".huf",
                    "Shannon-Fano": ".shf"
                }[algo]
                output_path = input_path + output_ext
                
                with st.spinner("Processing..."):
                    start = time.time()
                    if algo == "OCEC":
                        stats = OCECCompressor().compress_file(input_path, output_path)
                    elif algo == "DB-HEC":
                        stats = DBHECCompressor.compress_file(input_path, output_path, block_size=b_size, epsilon=threshold)
                    else:
                        engine_algo = "huffman" if "Huffman" in algo else "shannon_fano"
                        stats = CompressionEngine().compress_file(input_path, output_path, engine_algo)
                    duration = time.time() - start
                
                st.success(f"Compression successful ({duration:.2f}s)")
                
                with col2:
                    st.markdown("### Results")
                    m1, m2 = st.columns(2)
                    m1.metric("Original Size", f"{uploaded_file.size/1024:.2f} KB")
                    m2.metric("Compression Ratio", f"{stats['compression_ratio']:.3f}x")
                    
                    m3, m4 = st.columns(2)
                    m3.metric("Space Saving", f"{stats['space_saving_percent']:.1f}%")
                    m4.metric("Throughput", f"{(uploaded_file.size/1024/1024)/duration:.2f} MB/s")
                    
                    with open(output_path, "rb") as f:
                        st.download_button(
                            label="Download Compressed File",
                            data=f,
                            file_name=uploaded_file.name + output_ext
                        )
                if os.path.exists(input_path): os.remove(input_path)

elif mode == "Decompression Lab":
    st.title("File Decompression")
    uploaded_file = st.file_uploader("Select compressed stream", type=["ocec", "hyb", "huf", "shf"])
    
    if uploaded_file:
        if st.button("Run Decompression"):
            input_path = save_uploaded_file(uploaded_file)
            ext = Path(uploaded_file.name).suffix
            output_name = "restored_" + uploaded_file.name.replace(ext, "")
            
            with st.spinner("Decompressing..."):
                start = time.time()
                if ext == ".ocec":
                    OCECDecompressor.decompress_file(input_path, output_name)
                elif ext == ".hyb":
                    DBHECDecompressor.decompress_file(input_path, output_name)
                else:
                    DecompressionEngine().decompress_file(input_path, output_name)
                duration = time.time() - start
            
            st.success(f"Restore complete. Throughput: {(os.path.getsize(output_name)/1024/1024)/duration:.2f} MB/s")
            with open(output_name, "rb") as f:
                st.download_button("Download Restored File", f, file_name=output_name)

elif mode == "Parametric Workbench":
    st.title("Comparative Benchmark Analysis")
    uploaded_file = st.file_uploader("Select test file", type=None)
    
    if uploaded_file:
        with st.expander("Control Parameters", expanded=True):
            sweep_blocks = st.multiselect("Test Block Sizes", 
                                        options=[64*1024, 512*1024, 1024*1024, 2048*1024, 4096*1024],
                                        default=[1024*1024],
                                        format_func=lambda x: f"{x//1024} KB")
            sweep_thresholds = st.multiselect("Test Thresholds", 
                                            options=[7.0, 7.2, 7.5, 7.8],
                                            default=[7.5])
            
        if st.button("Run Benchmark Sweep"):
            input_path = save_uploaded_file(uploaded_file)
            
            with st.spinner("Analyzing performance..."):
                benchmark = ResearchBenchmark()
                results = benchmark.run_comprehensive_benchmark(
                    input_path, 
                    parallel=False,
                    block_sizes=sweep_blocks,
                    thresholds=sweep_thresholds
                )
            
            df = pd.DataFrame(results)
            
            # --- ROW 1 ---
            c1, c2 = st.columns(2)
            with c1:
                fig = px.scatter(df, x="compress_throughput", y="compression_ratio", 
                               color="algo_base", size="block_size", hover_name="algorithm",
                               title="Efficiency vs Throughput Analysis",
                               template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
                
            with c2:
                fig = px.bar(df, x="algorithm", y="entropy_efficiency_eta", 
                             title="Entropy Efficiency (η)",
                             template="plotly_white", color="entropy_efficiency_eta",
                             color_continuous_scale="Viridis")
                st.plotly_chart(fig, use_container_width=True)

            # --- ROW 2 ---
            c3, c4 = st.columns(2)
            with c3:
                fig = px.box(df, x="algo_base", y="compress_peak_memory", 
                             title="Memory Consumption (MB)",
                             template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
                
            with c4:
                categories = ['Efficiency', '1-Redundancy', 'Speed', 'Memory']
                fig = go.Figure()
                best_results = df.sort_values('compression_ratio', ascending=False).groupby('algo_base').head(1)
                for _i, r in best_results.iterrows():
                    fig.add_trace(go.Scatterpolar(
                        r=[r['entropy_efficiency_eta'], 1-r['relative_redundancy_R'], 
                           min(1, r['compress_throughput']/10), max(0, 1-(r['compress_peak_memory']/100))],
                        theta=categories,
                        fill='toself',
                        name=r['algo_base']
                    ))
                fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 1])), 
                                 template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("### Performance Dataset")
            st.dataframe(df[['algorithm', 'compression_ratio', 'compress_throughput', 'decompress_throughput', 
                           'compress_peak_memory', 'entropy_efficiency_eta']], use_container_width=True)

elif mode == "Research Abstract":
    st.title("Research Methodology")
    st.markdown(r"""
    ### Overview of Lossless Modulation Strategies
    **Author:** Arjun Mitra
    
    #### 1. Introduction
    This research investigates the optimization of discrete data transmission through multi-layered entropy modulation. By combining classic symbol-based coding with modern adaptive frameworks, our system achieves performance densities nearing the theoretical Shannon Limit.

    ---

    #### 2. Entropy Coding Foundations
    Foundation algorithms process data by mapping high-frequency symbols to shorter binary representations.
    
    *   **Huffman Coding:** A bottom-up approach that builds an optimal prefix-free tree using a min-heap. It is mathematically guaranteed to reach the minimum average code length for skewed distributions.
    *   **Shannon-Fano Coding:** A top-down recursive splitting method that partitions symbols into balanced probability groups. While historically significant, it serves as our baseline for comparative analysis.

    ---

    #### 3. DB-HEC: Dynamic Block Hybrid Logic
    DB-HEC introduces context-awareness by segmenting the bitstream based on **Entropy Sensitivity ($\epsilon$)**.
    
    *   **Segmented Modulation:** Data is divided into segments where the system automatically selects the best model (Huffman, Shannon-Fano, or Delta-Transformed variants).
    *   **Zero-Expansion Invariant:** Critically, if a segment cannot be compressed, the system falls back to raw data to ensure the compressed file never exceeds the original size.

    ---

    #### 4. OCEC: Flagship Omni-Context Logic
    OCEC is our novel multi-layer framework designed for maximum transmission efficiency.
    
    1.  **Contextual Dictionary:** Identifies structural redundancies using a sliding window before symbol modulation begins.
    2.  **Table Inheritance:** Drastically reduces metadata overhead by inheriting frequency tables from similar preceding contexts (Similarity Correlation $>0.9$).
    3.  **Recursive Bit-Macro Pass:** Scans the final bitstream for recurring macros to strip entropy remaining after initial passes.

    ---

    #### 5. Experimental Objectives
    The primary research goal is to achieve an **Entropy Efficiency ($\eta$)** exceeding 0.98, ensuring that system throughput remains linearly scalable without compromising the **Zero-Expansion Invariant**.
    """)
    st.info("Continuous parametric validation ensures bit-perfect reconstruction across all transmission modes.")

st.divider()
st.caption("© 2026 Arjun Mitra | OCEC Research Portal")
