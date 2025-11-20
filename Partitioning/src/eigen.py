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

def smallest_eigs_of_L(A,
                  n_eigens=20,
                  K=None,
                  tol=1e-6,
                  use_shift_invert=True,
                  sigma=0.0,
                  renorm_M=True):
    """
    Solve the k smallest eigenpairs of:
        A x = λ x            (when K is None)      -- standard
        A x = λ K x          (when K is given)     -- generalized (K SPD)

    Parameters
    ----------
    A : (N,N) sparse/dense ndarray or LinearOperator (symmetric)
    K : (N,N) sparse/dense ndarray or LinearOperator, or None
    n_eigens : number of eigenpairs to return (k < N)

    Returns
    -------
    vals : (n_eigens,) ascending eigenvalues
    vecs : (N,n_eigens) corresponding eigenvectors 
    """
    k = n_eigens
    # try to infer N
    N = None
    if hasattr(A, "shape"):
        N = A.shape[0]
    elif isinstance(A, LinearOperator):
        N = A.shape[0]
    else:
        raise TypeError("A must be ndarray/sparse/LinearOperator with .shape")

    if k >= N:
        k = N - 1  # eigsh needs k < N

    # Small dense fallback (get *all* then slice) – handy if k is large
    is_dense_A = hasattr(A, "ndim") and A.ndim == 2 and not isinstance(A, LinearOperator)
    is_dense_M = (K is None) or (hasattr(K, "ndim") and K.ndim == 2 and not isinstance(K, LinearOperator))
    if is_dense_A and is_dense_M and (N <= 512 or k >= N - 2):
        # dense full solve
        if K is None:
            w, V = sla.eigh(A)
        else:
            w, V = sla.eigh(A, K)
        idx = np.argsort(w)[:k]
        return w[idx], V[:, idx]

    # Sparse/iterative path
    if K is None:
        if use_shift_invert:
            vals, vecs = eigsh(A, k=k, which="LM", sigma=sigma, tol=tol)  # standard SI
        else:
            vals, vecs = eigsh(A, k=k, which="SM", tol=tol)
    else:
        if use_shift_invert:
            # shift-invert generalized (buckling mode) tends to be more stable for smallest λ
            vals, vecs = eigsh(A, k=k, M=K, which="LM", sigma=sigma, mode="buckling", tol=tol)
        else:
            vals, vecs = eigsh(A, k=k, M=K, which="SM", tol=tol)

    # sort ascending
    idx = np.argsort(vals)
    vals, vecs = vals[idx], vecs[:, idx]

    # Optional K-orthonormalization: V^T M V -> I
    if K is not None and renorm_M:
        def Mdot(X):
            return (K @ X) if not hasattr(K, "dot") else K.dot(X)
        G = vecs.T @ Mdot(vecs)                  # k x k Gram
        e, U = np.linalg.eigh(G)
        e = np.clip(e, 1e-15, None)
        Gmhalf = U @ (np.diag(1.0/np.sqrt(e)) @ U.T)
        vecs = vecs @ Gmhalf

    return vals, vecs