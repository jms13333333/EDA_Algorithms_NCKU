import numpy as np
import scipy.linalg as la
from scipy.sparse.linalg import LinearOperator, eigsh
from scipy import linalg as sla
from scipy.sparse import csr_matrix, diags, eye
from sklearn.cluster import KMeans
from typing import Tuple, Optional
import sys
import math
import os
import re
from evaluator import laplacian_indicator_score, count_balance, area_balance
from eigen import smallest_eigs_of_L

PAIR = re.compile(r'\(\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*\)')

def parse_width_height_from_tokens(tokens):
    s = " ".join(tokens)  # 接回原行
    xs, ys = [], []
    for m in PAIR.finditer(s):
        x, y = float(m.group(1)), float(m.group(2))
        xs.append(x); ys.append(y)
    if not xs:
        return None
    return max(xs) - min(xs), max(ys) - min(ys)

def parser(benchmark):
    node_file = open(os.path.join(benchmark+".blocks"), "r")
    def read_node_file(fopen):
        node_info = {}
        node_cnt = 0
        for line in fopen.readlines():
            if line.startswith("\t") or line.startswith("\n"):
                continue
            line = line.strip().split()
            if ((line[1] != "softrectangular") and (line[1] != "hardrectilinear")):
                continue
            node_name = line[0]
            if line[1] == "hardrectilinear":
                if int(line[2]) != 4:
                    print("error, cannot handle non rectangular")
                    sys.exit()
                w, h = parse_width_height_from_tokens(line)
                area = float(w * h)
                node_info[node_name] = {"id": node_cnt, "w": w, "h": h, "type": "hard", "area": area}
                node_cnt += 1
            elif line[1] == "softrectangular":
                area = float(line[2])
                node_info[node_name] = {"id": node_cnt, "type": "soft", "area": area}
                node_cnt += 1
        print("len node_info", len(node_info))
        return node_info
    node_info = read_node_file(node_file)
    net_file = open(os.path.join(benchmark+".nets"), "r")
    def read_net_file(fopen, node_info):
        net_info = {}
        net_cnt = 0
        start = False
        for line in fopen.readlines():
            if line.startswith("\n"):
                continue
            line = line.strip().split()
            if line[0] == "NetDegree":
                net_name = 'N'+str(net_cnt)
                net_cnt += 1
                start = True
            elif start == True:
                node_name = line[0]
                if node_name in node_info:
                    if not net_name in net_info:
                        net_info[net_name] = {}
                        net_info[net_name]["nodes"] = {}
                    if not node_name in net_info[net_name]["nodes"]:
                        type = line[-1]
                        net_info[net_name]["nodes"][node_name] = {}
                        net_info[net_name]["nodes"][node_name] = {"type": type}
        for net_name in list(net_info.keys()):
            if len(net_info[net_name]["nodes"]) <= 1:
                net_info.pop(net_name)
        for net_name in net_info:
            net_info[net_name]['id'] = net_cnt
            net_cnt += 1
        print("adjust net size = {}".format(len(net_info)))
        return net_info
    net_info = read_net_file(net_file, node_info)
    return node_info, net_info


def build_hypergraph_matrices(
        node_info, 
        net_info
):
    
    # --- 節點與超邊索引 ---
    # 以 node_info["id"] 當 row index
    name2nid = {name: info["id"] for name, info in node_info.items()}
    N = len(name2nid)  # Node總數

    edge_names = list(net_info.keys())
    E = len(edge_names) # Edge總數
    eid_map = {ename: i for i, ename in enumerate(edge_names)}

    # --- 構建稀疏 I (N x E) ---
    I = np.zeros((N, E), dtype=float)
    for e_name, e_data in net_info.items():
        e_id = eid_map[e_name]
        for node_name in e_data["nodes"]:
            n_id = name2nid[node_name]
            I[n_id, e_id] = 0.7

    # --- 超邊權重 We (E x E) (預設都是1)--- 
    We = np.eye(E, dtype=float)

    # --- 節點度數 Dv（=Dv[v] = sum_e I[v,e] * w_e） (N x N)---
    Dv = np.zeros((N, N), dtype=float)
    # TODO: 填值進Dv
    dv = np.sum(I @ We, axis=1)
    Dv = np.diag(dv)

    # --- 超邊度數 De (E x E）---
    # De[e] = |e| = sum_v I[v,e]
    De = np.zeros((E, E), dtype=float)
    # TODO: 填值進De
    de = np.sum(I, axis=0)
    De = np.diag(de)

    # --- 組 L_HG = 1 - Dv^{-1/2} I We De^{-1} I^T Dv^{-1/2} ---
    # 做好數學上安全處理（避免除以 0）
    def inv_sqrt(vec):
        out = np.zeros_like(vec, dtype=float)
        mask = vec > 0
        out[mask] = 1.0 / np.sqrt(vec[mask])
        return out

    def inv(vec):
        out = np.zeros_like(vec, dtype=float)
        mask = vec > 0
        out[mask] = 1.0 / vec[mask]
        return out
    
    # 算 Dv^{-1/2}
    dv = np.diag(Dv)
    Dv_mhalf = np.diag(inv_sqrt(dv))
    # 算 De^{-1}
    de = np.diag(De)
    De_inv = np.diag(inv(de))

    I_N = eye(N, format="csr", dtype=float)
    # 核心：S = Dv^{-1/2} I We De^{-1} I^T Dv^{-1/2}
    S = Dv_mhalf @ I @ We @ De_inv @ I.T @ Dv_mhalf
    L_hg = np.eye(N) - S

    return {
        "I": I,
        "Dv": Dv,
        "We": We, 
        "De": De, 
        "L": csr_matrix(L_hg)
    }

def kmeans(eigvecs: np.ndarray,
                         n_clusters: int,
                         normalize_rows: bool = True,
                         n_init: int = 10,
                         random_state: int = 0,):
    """
    eigvecs: (N, r)  前 r 個 eigenvectors（每一列對應一個 node）
    回傳:
      labels: (N,)    叢集標籤 0..k-1
      Y:      (N, k)  one-hot indicator matrix
    """
    X = np.asarray(eigvecs, dtype=float)
    if normalize_rows:
        nn = np.linalg.norm(X, axis=1, keepdims=True) + 1e-12
        X = X / nn
    km = KMeans(n_clusters=n_clusters, n_init=n_init, random_state=random_state)
    labels = km.fit_predict(X)
    return labels

def build_indicator(labels: np.ndarray,
                       n_clusters: Optional[int] = None,
                       dtype=float) -> Tuple[np.ndarray, np.ndarray]:
    labels = np.asarray(labels)
    N = labels.shape[0]
    k = int(labels.max()) + 1 if n_clusters is None else int(n_clusters)

    sizes = np.bincount(labels, minlength=k).astype(float)  # |A_c|
    Y = np.zeros((N, k), dtype=dtype)

    # 為避免空群除零，僅對 size>0 的群填入 1/sqrt(size)
    for c in range(k):
        sc = sizes[c]
        if sc > 0:
            Y[labels == c, c] = 1.0 / np.sqrt(sc)
        # 若 sc==0，該欄全 0；此時 Y^T Y 在該軸不是 1（代表空群）

    return Y, sizes

n_clusters = 15
n_eigens = 10

# 在這邊調所要跑的case
print(f'Case: {sys.argv[1]}')
benchmark = './IBMHB+/' + sys.argv[1] + '/' + sys.argv[1]
node_info, net_info = parser(benchmark)

mats = build_hypergraph_matrices(node_info, net_info,) 
L = mats["L"]   # 這就是超圖拉普拉斯 (稀疏矩陣)
vals, vecs = smallest_eigs_of_L(L, K=None, n_eigens=n_eigens)
vecs = vecs[:, 1:-1] # 拿掉trivial解
labels = kmeans(vecs, n_clusters=n_clusters, normalize_rows=True)
Y, _ = build_indicator(labels, n_clusters)
score_total, score_each, _ = laplacian_indicator_score(L, Y)
count_report = count_balance(Y)
count_score = count_report["score01"]
print("Total trace(Y^T L Y) =", score_total) #總cluster混亂程度
print("Per-cluster diag =", score_each) #每個cluster與外界的cut size

# 創立一個constrained項，去做generalized eigen問題
# TODO: 得到laplacian K
areas = np.array([info["area"] for info in node_info.values()])
areas[areas == 0] = 1e-6 #避免除零
K = diags(areas, 0, format="csr")

vals, vecs = smallest_eigs_of_L(L, K=K, n_eigens=n_eigens)
vecs = vecs[:, 1:-1] # 拿掉trivial解
labels = kmeans(vecs, n_clusters=n_clusters, normalize_rows=True)
Y, _ = build_indicator(labels, n_clusters)
score_total, score_each, _ = laplacian_indicator_score(L, Y)
count_report = count_balance(Y)
count_score = count_report["score01"]
print("Total trace(Y^T L Y) =", score_total) #總cluster混亂程度
print("Per-cluster diag =", score_each) #每個cluster與外界的cut size
print("Area balance score(1 is the best, 0 is the worst) = ", count_score)