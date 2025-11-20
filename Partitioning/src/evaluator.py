import numpy as np
from typing import Optional, Dict, Any

def laplacian_indicator_score(L, Y: np.ndarray): #評分器
    if hasattr(L, "dot"):
        LY = L.dot(Y)         
    else:
        LY = L @ Y            

    M = Y.T @ LY              
    score_per_cluster = np.diag(M)
    score_total = float(np.trace(M))
    return score_total, score_per_cluster, M

def count_balance(Y: np.ndarray) -> Dict[str, Any]:
    """
    數量平衡評分器（Hagen–Kahng 版 Y；Y^T Y = I，欄向量在所屬群為 1/sqrt(|A_c|)）
    回傳同前：sizes, mean, std, cv, imbalance, score01
    """
    Y = np.asarray(Y, dtype=float)
    N, k = Y.shape

    # |A_c| = (sum_i Y_{ic})^2 ；其中 sum_i Y_{ic} = sqrt(|A_c|)
    sqrt_sizes = Y.sum(axis=0)
    sizes = (sqrt_sizes ** 2)

    mean_cnt = float(N / k) if k > 0 else 0.0
    std_cnt  = float(np.std(sizes, ddof=0))
    cv_cnt   = float(std_cnt / (mean_cnt + 1e-12)) if mean_cnt > 0 else 0.0
    imb_cnt  = float((sizes.max() - sizes.min()) / (mean_cnt + 1e-12)) if k > 0 else 0.0
    score_cnt = 1.0 / (1.0 + imb_cnt)

    return {
        "sizes": sizes,
        "mean": mean_cnt,
        "std": std_cnt,
        "cv": cv_cnt,
        "imbalance": imb_cnt,
        "score01": score_cnt,
    }

def area_balance(Y: np.ndarray, area: np.ndarray) -> Dict[str, Any]:
    """
    面積平衡評分器（Hagen–Kahng 版 Y）
    area: (N,) 每個節點的面積
    回傳同前，但 sizes 代表各群「面積總和」
    """
    Y = np.asarray(Y, dtype=float)
    area = np.asarray(area, dtype=float).reshape(-1)
    N, k = Y.shape
    assert area.shape[0] == N, "area 長度需等於 Y 的列數 N"

    sqrt_sizes = Y.sum(axis=0)             # sqrt(|A_c|)
    area_over_sqrt = area @ Y              # (sum_{i∈A_c} area_i) / sqrt(|A_c|)
    area_sums = area_over_sqrt * sqrt_sizes  # = sum_{i∈A_c} area_i

    mean_area = float(area.sum() / k) if k > 0 else 0.0
    std_area  = float(np.std(area_sums, ddof=0))
    cv_area   = float(std_area / (mean_area + 1e-12)) if mean_area > 0 else 0.0
    imb_area  = float((area_sums.max() - area_sums.min()) / (mean_area + 1e-12)) if k > 0 else 0.0
    score_area = 1.0 / (1.0 + imb_area)

    return {
        "sizes": area_sums,
        "mean": mean_area,
        "std": std_area,
        "cv": cv_area,
        "imbalance": imb_area,
        "score01": score_area,
    }