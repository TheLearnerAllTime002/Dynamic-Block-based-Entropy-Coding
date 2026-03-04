"""
Visualization Module for Entropy Analysis
Creates charts and graphs for academic presentation of compression results.
"""

import json
from typing import Dict, List
from pathlib import Path

class AnalysisVisualizer:
    """Creates text-based visualizations for entropy analysis."""
    
    @staticmethod
    def create_entropy_report(analysis: Dict, output_file: str = None) -> str:
        """Generate comprehensive entropy analysis report."""
        report = []
        
        # Header
        report.append("=" * 80)
        report.append("ENTROPY-EFFICIENCY ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")
        
        # File Information
        report.append("FILE INFORMATION")
        report.append("-" * 40)
        report.append(f"File size: {analysis['file_size']:,} bytes")
        report.append(f"Unique symbols: {analysis['unique_symbols']}/256")
        report.append(f"Shannon entropy (H): {analysis['shannon_entropy']:.4f} bits/byte")
        report.append(f"Theoretical minimum: {analysis['theoretical_minimum_bits']:,.0f} bits")
        report.append(f"Compressibility: {analysis['compressibility_class']}")
        report.append("")
        
        # Algorithm Comparison
        if analysis['algorithms']:
            report.append("ALGORITHM PERFORMANCE ANALYSIS")
            report.append("-" * 80)
            
            # Table header
            report.append(f"{'Algorithm':<15} {'L_avg':<8} {'Eff (%)':<8} {'Ratio':<8} {'Saving':<8} {'Optimality':<10}")
            report.append("-" * 80)
            
            for algo, metrics in analysis['algorithms'].items():
                report.append(
                    f"{algo:<15} "
                    f"{metrics['average_code_length']:<8.3f} "
                    f"{metrics['compression_efficiency']:<8.1f} "
                    f"{metrics['compression_ratio']:<8.3f} "
                    f"{metrics['space_saving']:<8.1f}% "
                    f"{metrics['theoretical_optimality']:<10.3f}"
                )
            
            report.append("")
            
            # Detailed Analysis
            report.append("DETAILED METRICS")
            report.append("-" * 40)
            
            for algo, metrics in analysis['algorithms'].items():
                report.append(f"\n{algo.upper()} Algorithm:")
                report.append(f"  Average Code Length (L_avg): {metrics['average_code_length']:.4f} bits/symbol")
                report.append(f"  Compression Efficiency (Eff): {metrics['compression_efficiency']:.2f}%")
                report.append(f"  Redundancy (L_avg - H): {metrics['redundancy']:.4f} bits/symbol")
                report.append(f"  Theoretical Optimality: {metrics['theoretical_optimality']:.3f}")
                
                # Efficiency classification
                efficiency = metrics['compression_efficiency']
                if efficiency >= 95:
                    classification = "Excellent (Near-optimal)"
                elif efficiency >= 85:
                    classification = "Good"
                elif efficiency >= 70:
                    classification = "Fair"
                else:
                    classification = "Poor"
                report.append(f"  Efficiency Rating: {classification}")
        
        report.append("")
        report.append("=" * 80)
        
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
        
        return report_text
    
    @staticmethod
    def create_block_entropy_report(blocks: List[Dict], output_file: str = None) -> str:
        """Generate block-wise entropy analysis report for hybrid algorithm."""
        report = []
        
        report.append("=" * 80)
        report.append("BLOCK-WISE ENTROPY ANALYSIS (DB-HEC)")
        report.append("=" * 80)
        report.append("")
        
        if not blocks:
            report.append("No block data available.")
            return "\n".join(report)
        
        # Summary statistics
        entropies = [block['entropy'] for block in blocks]
        avg_entropy = sum(entropies) / len(entropies)
        min_entropy = min(entropies)
        max_entropy = max(entropies)
        
        report.append("BLOCK SUMMARY")
        report.append("-" * 40)
        report.append(f"Total blocks: {len(blocks)}")
        report.append(f"Average entropy: {avg_entropy:.4f} bits/byte")
        report.append(f"Minimum entropy: {min_entropy:.4f} bits/byte")
        report.append(f"Maximum entropy: {max_entropy:.4f} bits/byte")
        report.append(f"Entropy variance: {sum((e - avg_entropy)**2 for e in entropies) / len(entropies):.4f}")
        report.append("")
        
        # Block details
        report.append("BLOCK DETAILS")
        report.append("-" * 80)
        report.append(f"{'Block':<6} {'Start':<10} {'End':<10} {'Size':<8} {'Entropy':<8} {'Compressibility'}")
        report.append("-" * 80)
        
        for block in blocks:
            report.append(
                f"{block['block_index']:<6} "
                f"{block['start_byte']:<10} "
                f"{block['end_byte']:<10} "
                f"{block['size']:<8} "
                f"{block['entropy']:<8.3f} "
                f"{block['compressibility']}"
            )
        
        # Algorithm selection analysis
        report.append("")
        report.append("ALGORITHM SELECTION ANALYSIS")
        report.append("-" * 40)
        
        huffman_blocks = sum(1 for block in blocks if block['entropy'] <= 7.5)
        shannon_blocks = len(blocks) - huffman_blocks
        
        report.append(f"Blocks using Huffman (entropy ≤ 7.5): {huffman_blocks}")
        report.append(f"Blocks using Shannon-Fano (entropy > 7.5): {shannon_blocks}")
        report.append(f"Huffman percentage: {(huffman_blocks/len(blocks)*100):.1f}%")
        report.append(f"Shannon-Fano percentage: {(shannon_blocks/len(blocks)*100):.1f}%")
        
        report.append("")
        report.append("=" * 80)
        
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
        
        return report_text
    
    @staticmethod
    def create_comparison_chart(analysis: Dict) -> str:
        """Create ASCII chart comparing algorithm efficiencies."""
        if not analysis['algorithms']:
            return "No algorithm data available for comparison."
        
        chart = []
        chart.append("COMPRESSION EFFICIENCY COMPARISON")
        chart.append("=" * 50)
        
        # Get efficiency values
        algos = list(analysis['algorithms'].keys())
        efficiencies = [analysis['algorithms'][algo]['compression_efficiency'] for algo in algos]
        
        # Create bar chart
        max_efficiency = max(efficiencies) if efficiencies else 100
        scale = 40 / max_efficiency if max_efficiency > 0 else 1
        
        for i, algo in enumerate(algos):
            efficiency = efficiencies[i]
            bar_length = int(efficiency * scale)
            bar = "#" * bar_length
            chart.append(f"{algo:<15} |{bar:<40} {efficiency:.1f}%")
        
        chart.append("=" * 50)
        chart.append(f"Shannon Entropy: {analysis['shannon_entropy']:.3f} bits/byte")
        
        return "\n".join(chart)
    
    @staticmethod
    def export_json_report(analysis: Dict, output_file: str):
        """Export analysis results as JSON for further processing."""
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2)