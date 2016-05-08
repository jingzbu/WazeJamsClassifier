#!/usr/bin/env python
""" A library of utility functions
"""
from __future__ import absolute_import, division

__author__ = "Jing Zhang"
__email__ = "jingzbu@gmail.com"
__status__ = "Development"

import numpy as np
from numpy import linalg as LA
from math import sqrt, log
from matplotlib.mlab import prctile
import statsmodels.api as sm  # recommended import according to the docs


# Data Storage and Load
# These two functions "zdump" and "zload" were written by Jing Wang
# cf. https://github.com/hbhzwj/GAD/blob/master/gad/util/util.py

try:
    import cPickle as pickle
except ImportError:
    import pickle
import gzip
proto = pickle.HIGHEST_PROTOCOL

def zdump(obj, f_name):
    f = gzip.open(f_name,'wb', proto)
    pickle.dump(obj,f)
    f.close()

def zload(f_name):
    f = gzip.open(f_name,'rb', proto)
    obj = pickle.load(f)
    f.close()
    return obj

def dump(obj, f_name):
    f = open(f_name,'wb', proto)
    pickle.dump(obj,f)
    f.close()

def load(f_name):
    f = open(f_name,'rb', proto)
    obj = pickle.load(f)
    f.close()
    return obj

# Convert startTime to seconds
# e.g., '2016-03-22 01:15:00.000' => 4500.0
def convStartTimeToSec(startTime):
    secVal = float(startTime.split(' ')[1].split(':')[0]) * (60 ** 2) + \
    float(startTime.split(' ')[1].split(':')[1]) * 60 + \
    float(startTime.split(' ')[1].split(':')[2])
    return secVal

def rand_x(p):
    """
    Generate a random variable in 0, 1, ..., (N-1) given a distribution vector p
    N is the dimension of p
    ----------------
    Example
    ----------------
    p = [0.5, 0.5]
    x = []
    for j in range(0, 20):
        x.append(rand_x(p))
    print x
    ----------------

    [1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0]
    """
    p = np.array(p)
    N = p.shape
    #assert(abs(sum(p) - 1) < 1e-5)
    u = np.random.rand(1, 1)
    i = 0
    s = p[0]
    while (u > s).all() and i < N[0]-1:
        i = i + 1
        s = s + p[i]
    index = i

    return index

def chain(mu_0, Q, n):
    """
    Simulate a Markov chain on {0, 1, ..., n-1} given an initial
    distribution and a transition matrix
    ----------------
    The program assumes that the states are labeled 0, 1, ..., N-1
    ----------------
    mu_0: the initial distribution, a 1 x N vector
    Q: the transition matrix, N x N
    ----------------
    n: the number of samples
    N: the total number of states of the chain
    ----------------
    Example
    ----------------
    """
    #assert(abs(sum(mu_0) - 1) < 1e-5)
    Q = np.array(Q)
    N, _ = Q.shape
    assert(N == _)
    x = [0] * n
    x[0] = rand_x(mu_0)
    for i in range(1, n-1):
       x[i+1] = rand_x(Q[x[i], :])

    return x

def mu_adjust(mu):
    """
    adjust mu such that each entry is positive
    mu: N * N
    """
    N, _ = mu.shape
    assert(N == _)
    
    eps = 1e-12
    
    for i in range(N):
        for j in range(N):
            if mu[i, j] < eps:
                mu[i, j] = eps
    sum_ = sum(sum(mu))
    # print(sum_)
    mu = mu / sum_

    return mu

def probability_matrix_Q(dimQ):
    """
    Randomly generate the original transition matrix Q
    dimQ: the row dimension of Q
    Example
    ----------------
    """
    weight = []
    for i in range(0, dimQ):
        t = np.random.randint(1, high=dimQ, size=dimQ)
        weight.append(t)
    Q = np.random.rand(dimQ, dimQ)
    for i in range(0, dimQ):
        Q[i, :] = weight[i] * Q[i, :]
        Q[i, :] = Q[i, :] / (sum(Q[i,:]))
    N, _ = Q.shape
    assert(N == _)

    return Q

def mu_ini(dim_mu):
    """
    Randomly generate the initial distribution mu
    dim_mu: the dimension of mu
    Example
    ----------------
    """
    weight = []
    for i in range(0, dim_mu):
        t = np.random.randint(1, high=dim_mu, size=1)
        weight.append(t)
    mu = np.random.rand(1, dim_mu)
    for i in range(0, dim_mu):
        mu[0, i] = (weight[i][0]) * mu[0, i]
    mu = mu / (sum(mu[0, :]))
    assert(abs(sum(mu[0, :]) - 1) < 1e-5)

    return mu

def mu_est(x, N):
    """
    Estimate the stationary distribution mu
    x: a sample path of the chain
    N: the obtained mu should be an N x N matrix
    Example
    ----------------
    >>> x = [0, 1, 2, 2, 1, 2, 1,0, 1, 2, 2, 1, 2, 1, 0, 1, 2, 2, 1, 2, 1, 3, 3, 3, 3, 1, 1]
    >>> N = 2
    >>> mu_1 = mu_est(x, N)
    >>> print mu_1
    [[ 0.11111111  0.40740741]
     [ 0.33333333  0.14814815]]
    """
    eps = 1e-8
    gama = [0] * N * N
    for j in range(0, N**2):
        gama[j] = (x.count(j)) / (len(x))
        if gama[j] < eps:
            gama[j] = eps
    for j in range(0, N**2):
        gama[j] = gama[j] / sum(gama)  # Normalize the estimated probability law
    gama = np.array(gama)
    mu = gama.reshape(N, N)

    return mu

def KL_est(x, mu):
    """
    Estimate the relative entropy (K-L divergence)
    x: a sample path of the chain
    mu: the true stationary distribution; an N x N matrix
    """
    mu = np.array(mu)
    N, _ = mu.shape
    assert(N == _)

    # Compute the empirical distribution
    eps = 1e-8
    gama = [0] * N * N
    for j in range(0, N**2):
        gama[j] = (x.count(j)) / (len(x))
        if gama[j] < eps:
            gama[j] = eps
    for j in range(0, N**2):
        gama[j] = gama[j] / sum(gama)  # Normalize the estimated probability law
    gama = np.array(gama)
    gama = np.reshape(gama, (N, N))

    # Compute the relative entropy (K-L divergence)
    d = np.zeros((N, N))
    for i in range(0, N):
        for j in range(0, N):
            d[i, j] = gama[i, j] * (log(gama[i, j] / (sum(gama[i, :]))) - log(mu[i, j] / (sum(mu[i, :]))))
    KL = sum(sum(d))

    return KL

def Q_est(mu):
    """
    Estimate the original transition matrix Q
    Example
    ----------------
    >>> mu = [[0.625,  0.125],  [0.125,  0.125]]
    >>> print Q_est(mu)
    [[ 0.83333333  0.16666667]
     [ 0.5         0.5       ]]
    """

    mu = np.array(mu)
    N, _ = mu.shape
    assert(N == _)

    pi = np.sum(mu, axis=1)

    Q = mu / np.dot( pi.reshape(-1, 1), np.ones((1, N)) )

    return Q

def P_est(Q):
    """
    Estimate the new transition matrix P
    """
    Q = np.array(Q)
    N, _ = Q.shape
    assert(N == _)

    P1 = np.zeros((N, N**2))

    for j in range(0, N):
        for i in range(j * N, (j + 1) * N):
            P1[j, i] = Q[j, i - j * N]

    P = np.tile(P1, (N, 1))

    return P

def G_est(Q):
    """
    Estimate the Gradient
    Example
    ----------------
    # >>> mu = [[0.625,  0.125],  [0.125,  0.125]]
    # >>> print G_est(mu)
    # [[ 0.16666667  0.83333333  0.5         0.5       ]]
    """
    # N, _ = Q.shape
    # assert(N == _)
    # alpha = 1 - Q
    # G = alpha.reshape(1, N**2)
    G = 0

    return G

def H_est(mu):
    """
    Estimate the Hessian
    Example
    ----------------
    # >>> mu = [[0.625,  0.125],  [0.125,  0.125]]
    # >>> print H_est(mu)
    # [[ 0.04444444 -0.22222222  0.          0.        ]
    #  [-1.11111111  5.55555556  0.          0.        ]
    #  [ 0.          0.          2.         -2.        ]
    #  [ 0.          0.         -2.          2.        ]]
    """
    mu = np.array(mu)
    N, _ = mu.shape
    assert(N == _)

    H = np.zeros((N, N, N, N))

    for i in range(0, N):
        for j in range(0, N):
            for k in range(0, N):
                for l in range(0, N):
                    if k != i:
                        H[i, j, k, l] = 0
                    elif l == j:
                        H[i, j, k, l] = 1 / mu[i, j] - 1 / (sum(mu[i, :]))
                    else:
                        H[i, j, k, l] = - 1 / (sum(mu[i, :]))

    H = np.reshape(H, (N**2, N**2))

    return H

def Sigma_est(P, mu):
    """
    Estimate the covariance matrix of the empirical measure
    Example
    ----------------
    >>> mu = [[0.625,  0.125],  [0.125,  0.125]]
    >>> print Sigma_est(mu)
    [[ 0.625   -0.15625 -0.15625 -0.3125 ]
     [-0.15625  0.0625   0.0625   0.03125]
     [-0.15625  0.0625   0.0625   0.03125]
     [-0.3125   0.03125  0.03125  0.25   ]]
    """
    mu = np.array(mu)
    N, _ = mu.shape
    assert(N == _)

    muVec = np.reshape(mu, (1, N**2))

    I = np.matrix(np.identity(N**2))

    M = 1000

    PP = np.zeros((M, N**2, N**2))
    for m in range(1, M):
        PP[m] = LA.matrix_power(P, m)

    series = np.zeros((1, M))

    Sigma = np.zeros((N**2, N**2))
    for i in range(0, N**2):
        for j in range(0, N**2):
            for m in range(1, M):
                series[0, m] = muVec[0, i] * (PP[m][i, j] - muVec[0, j]) + \
                                muVec[0, j] * (PP[m][j, i] - muVec[0, i])
            Sigma[i, j] = muVec[0, i] * (I[i, j] - muVec[0, j]) + \
                            sum(series[0, :])

    # Ensure Sigma to be symmetric
    Sigma = (1.0 / 2) * (Sigma + np.transpose(Sigma))

    # Ensure Sigma to be positive semi-definite
    D, V = LA.eig(Sigma)
    D = np.diag(D)
    Q, R = LA.qr(V)
    for i in range(0, N**2):
        if D[i, i] < 1e-20:
            D[i, i] = 1e-20
    Sigma = np.dot(np.dot(Q, D), LA.inv(Q))
    return Sigma

def U_est(Sigma, SampNum):
    """
    Generate samples of the Gaussian random vector U
    ----------------
    Sigma: the covariance matrix; an N x N matrix
    SampNum: the length of the sample path
    """
    N, _ = Sigma.shape
    assert(N == _)
    U_mean = np.zeros((1, N))
    U = np.random.multivariate_normal(U_mean[0, :], Sigma, (1, SampNum))

    return U

def HoeffdingRuleMarkov(beta, G, H, U, FlowNum):
    """
    Estimate the K-L divergence and the threshold by use of weak convergence
    ----------------
    beta: the false alarm rate
    G: the gradient
    H: the Hessian
    U: a sample path of the Gaussian empirical measure
    FlowNum: the number of flows
    ----------------
    """
    _, SampNum, _ = U.shape

    # Estimate K-L divergence using 2nd-order Taylor expansion
    KL = []
    for j in range(0, SampNum):
        t = (1.0 / sqrt(FlowNum)) * np.dot(G, U[0, j, :]) + \
                (1.0 / 2) * (1.0 / FlowNum) * \
                    np.dot(np.dot(U[0, j, :], H), U[0, j, :])
        # print t.tolist()
        # break
        KL.append(np.array(t.real)[0])
    eta = prctile(KL, 100 * (1 - beta))
    # print(KL)
    # assert(1 == 2)
    return eta

def HoeffdingRuleMarkovRobust(beta, G_1, H_1, U_1, G_2, H_2, U_2, G_3, H_3, U_3, FlowNum):
    """
    Estimate the K-L divergence and the threshold by use of weak convergence
    ----------------
    beta: the false alarm rate
    G: the gradient
    H: the Hessian
    U: a sample path of the Gaussian empirical measure
    FlowNum: the number of flows
    ----------------
    """
    _, SampNum, _ = U_1.shape

    # Estimate K-L divergence using 2nd-order Taylor expansion
    KL = []
    for j in range(0, SampNum):
        t_1 = (1.0 / sqrt(FlowNum)) * np.dot(G_1, U_1[0, j, :]) + \
                (1.0 / 2) * (1.0 / FlowNum) * \
                    np.dot(np.dot(U_1[0, j, :], H_1), U_1[0, j, :])
        t_2 = (1.0 / sqrt(FlowNum)) * np.dot(G_2, U_2[0, j, :]) + \
                (1.0 / 2) * (1.0 / FlowNum) * \
                    np.dot(np.dot(U_2[0, j, :], H_2), U_2[0, j, :])
        t_3 = (1.0 / sqrt(FlowNum)) * np.dot(G_3, U_3[0, j, :]) + \
                (1.0 / 2) * (1.0 / FlowNum) * \
                    np.dot(np.dot(U_3[0, j, :], H_3), U_3[0, j, :])
	t1 = np.array(t_1.real)[0]
	t2 = np.array(t_2.real)[0]
	t3 = np.array(t_3.real)[0]
        # print t.tolist()
        # break
        KL.append(min([t1, t2, t3]))
    eta = prctile(KL, 100 * (1 - beta))
    # print(KL)
    # assert(1 == 2)
    return eta

def HoeffdingRuleMarkovRobust_(beta, G_list, H_list, U_list, FlowNum):
    """
    Estimate the K-L divergence and the threshold by use of weak convergence
    ----------------
    beta: the false alarm rate
    G: the gradient
    H: the Hessian
    U: a sample path of the Gaussian empirical measure
    FlowNum: the number of flows
    ----------------
    """
    _, SampNum, _ = U_list[0].shape
    # print(SampNum)
    # assert(1 == 2)

    # Estimate K-L divergence using 2nd-order Taylor expansion
    KL = []
    for j in range(0, SampNum):
	KL_est_list = []
        for G, H, U in zip(G_list, H_list, U_list):
            KL_est = (1.0 / sqrt(FlowNum)) * np.dot(G, U[0, j, :]) + \
                     (1.0 / 2) * (1.0 / FlowNum) * \
                      np.dot(np.dot(U[0, j, :], H), U[0, j, :])
            KL_est = np.array(KL_est.real)[0]
            KL_est_list.append(KL_est)
        KL.append(min(KL_est_list))
    eta = prctile(KL, 100 * (1 - beta))

    return eta

def ChainGen(N):
    # Get the initial distribution mu_0
    mu_0 = mu_ini(N**2)

    # Get the original transition matrix Q
    Q = probability_matrix_Q(N)

    # Get the new transition matrix P
    P = P_est(Q)

    # Get the actual stationary distribution mu; 1 x (N**2)
    PP = LA.matrix_power(P, 1000)
    mu = PP[0, :]

    # Get a sample path of the Markov chain with length n_1; this path is used to estimate the stationary distribution
    n_1 = 1000 * N * N  # the length of a sample path
    x_1 = chain(mu_0, P, n_1)

    # Get the estimated stationary distribution mu_1
    mu_1 = mu_est(x_1, N)

    # Get the estimate of Q
    Q_1 = Q_est(mu_1)

    # Get the estimate of P
    P_1 = P_est(Q_1)

    # Get the estimate of the gradient
    G_1 = G_est(Q_1)

    # Get the estimate of the Hessian
    H_1 = H_est(mu_1)

    # Get the estimate of the covariance matrix
    Sigma_1 = Sigma_est(P_1, mu_1)

    # Get an estimated sample path of U
    SampNum = 1000
    U_1 = U_est(Sigma_1, SampNum)

    return mu_0, mu, mu_1, P, G_1, H_1, U_1

def ChainGen_(mu_inp):
    
    N, _ = np.shape(mu_inp)
    assert(N == _)
    
    # Get the initial distribution mu_0
    mu_0 = np.reshape(mu_inp, N**2)

    # Get the original transition matrix Q
    Q = Q_est(mu_inp)

    # Get the new transition matrix P
    P = P_est(Q)

    # Get the actual stationary distribution mu; 1 x (N**2)
    PP = LA.matrix_power(P, 1000)
    mu = PP[0, :]

    # Get a sample path of the Markov chain with length n_1; this path is used to estimate the stationary distribution
    n_1 = 1000 * N * N  # the length of a sample path
    x_1 = chain(mu_0, P, n_1)

    # Get the estimated stationary distribution mu_1
    mu_1 = mu_est(x_1, N)

    # Get the estimate of Q
    Q_1 = Q_est(mu_1)

    # Get the estimate of P
    P_1 = P_est(Q_1)

    # Get the estimate of the gradient
    G_1 = G_est(Q_1)

    # Get the estimate of the Hessian
    H_1 = H_est(mu_1)

    # Get the estimate of the covariance matrix
    Sigma_1 = Sigma_est(P_1, mu_1)

    # Get an estimated sample path of U
    SampNum = 1000
    U_1 = U_est(Sigma_1, SampNum)

    return mu_0, mu, mu_1, P, G_1, H_1, U_1

class ThresBase(object):
    def __init__(self, N, beta, n, mu_0, mu, mu_1, P, G_1, H_1, U_1):
        self.N = N  # N is the row dimension of the original transition matrix Q
        self.beta = beta  # beta is the false alarm rate
        self.n = n  # n is the number of samples
        self.mu_0 = mu_0
        self.mu = mu
        self.mu_1 = mu_1
        self.P = P
        self.G_1 = G_1
        self.H_1 = H_1
        self.U_1 = U_1

class ThresActual(ThresBase):
    """ Computing the actual (theoretical) K-L divergence and threshold
    """
    def ThresCal(self):
        SampNum = 1000
        KL = []
        for i in range(0, SampNum):
            x = chain(self.mu_0, self.P, self.n)
            mu = np.reshape(self.mu, (self.N, self.N))
            KL.append(KL_est(x, mu))  # Get the actual relative entropy (K-L divergence)
        eta = prctile(self.KL, 100 * (1 - self.beta))
        return eta

class ThresWeakConv(ThresBase):
    """ Estimating the K-L divergence and threshold by use of weak convergence
    """
    def ThresCal(self):
        eta = HoeffdingRuleMarkov(self.beta, self.G_1, self.H_1, self.U_1, self.n)
        return eta

class ThresSanov(ThresBase):
    """ Estimating the threshold by use of Sanov's theorem
    """
    def ThresCal(self):
        eta = - log(self.beta) / self.n
        return eta

class ThresBaseRobust(object):
    def __init__(self, N, beta, n, mu_01, mu_1, mu_11, P_11, G_11, \
		       H_11, U_11, mu_02, mu_2, mu_12, P_12, G_12, \
		       H_12, U_12, mu_03, mu_3, mu_13, P_13, G_13, \
		       H_13, U_13):
        self.N = N  # N is the row dimension of the original transition matrix Q
        self.beta = beta  # beta is the false alarm rate
        self.n = n  # n is the number of samples
        self.mu_01 = mu_01
        self.mu_1 = mu_1
	self.mu_11 = mu_11
	self.P_11 = P_11
	self.G_11 = G_11
	self.H_11 = H_11
	self.U_11 = U_11
	self.mu_02 = mu_02
	self.mu_2 = mu_2
	self.mu_12 = mu_12
	self.P_12 = P_12
	self.G_12 = G_12
	self.H_12 = H_12
	self.U_12 = U_12
	self.mu_03 = mu_03
	self.mu_3 = mu_3
	self.mu_13 = mu_13
	self.P_13 = P_13
	self.G_13 = G_13
	self.H_13 = H_13
	self.U_13 = U_13

class ThresWeakConvRobust(ThresBaseRobust):
    """ Estimating the K-L divergence and threshold by use of weak convergence
    """
    def ThresCal(self):
        eta = HoeffdingRuleMarkovRobust(self.beta, self.G_11, self.H_11, self.U_11, self.G_12, self.H_12, self.U_12, self.G_13, self.H_13, self.U_13, self.n)
        return eta
