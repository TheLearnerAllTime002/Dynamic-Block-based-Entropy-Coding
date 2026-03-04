"""
Error Metrics Module for Signal Reconstruction Analysis
"""

import numpy as np
from typing import Dict

def compute_error_metrics(original: np.ndarray, reconstructed: np.ndarray) -> Dict[str, float]:
    """
    Computes standard error metrics between original and reconstructed 1-D signals.
    
    Args:
        original: Original signal array
        reconstructed: Reconstructed signal array
        
    Returns:
        Dictionary containing MSE, MSS, RMSE, and PRE (%)
        
    Raises:
        ValueError: If arrays have different shapes or are not 1-D
    """
    if original.shape != reconstructed.shape:
        raise ValueError(f"Shape mismatch: original {original.shape} vs reconstructed {reconstructed.shape}")
    
    if original.ndim != 1:
        # Flatten if not 1D, but the requirement specified 1-D signals
        original = original.flatten()
        reconstructed = reconstructed.flatten()

    N = len(original)
    if N == 0:
        return {
            "MSE": 0.0,
            "MSS": 0.0,
            "RMSE": 0.0,
            "PRE_percent": 0.0
        }

    # Use float64 to prevent overflow during squared sums
    orig_f = original.astype(np.float64)
    recon_f = reconstructed.astype(np.float64)
    
    diff = orig_f - recon_f
    
    # 1. Mean Squared Error (MSE)
    mse = np.mean(diff**2)
    
    # 2. Mean Signal Strength (MSS)
    mss = np.mean(orig_f**2)
    
    # 3. Root Mean Squared Error (RMSE)
    rmse = np.sqrt(mse)
    
    # 4. Percentage Root Error (PRE)
    # PRE(%) = sqrt(sum((x - x_hat)^2) / sum(x^2)) * 100
    # This is equivalent to sqrt(MSE / MSS) * 100 if we use the means
    if mss > 0:
        pre_percent = np.sqrt(np.sum(diff**2) / np.sum(orig_f**2)) * 100
    else:
        pre_percent = 0.0 if mse == 0 else float('inf')
        
    return {
        "MSE": float(mse),
        "MSS": float(mss),
        "RMSE": float(rmse),
        "PRE_percent": float(pre_percent)
    }

def print_error_report(metrics: Dict[str, float]):
    """Prints a neat console report of reconstruction error metrics."""
    print("\n=== Reconstruction Error Metrics ===")
    print(f"MSE        : {metrics['MSE']:.6f}")
    print(f"MSS        : {metrics['MSS']:.6f}")
    print(f"RMSE       : {metrics['RMSE']:.6f}")
    print(f"PRE (%)    : {metrics['PRE_percent']:.4f}")
    print("====================================\n")
