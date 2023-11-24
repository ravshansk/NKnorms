
import itertools
import numpy as np
from numpy.typing import NDArray
from numba import njit
from .exceptions import *

def binary_combinations(N,R):
    """Generates all binary vectors with sum R

    Args:
        N (int): Size of a binary vector
        R (int): Sum of elements of a vector

    Returns:
        numpy.ndarray: an (N R)xN numpy array, where
        rows are vectors of size N and sum of elements R
    """

    tmp = []
    idx = itertools.combinations(range(N),R)
    for i in idx:
        A = [0]*N
        for j in i:
            A[j] = 1
        tmp.append(A)
    output = np.reshape(tmp,(-1,N))
    return(output)
    
def random_binary_matrix(N,R,diag=None):
    """Generates a random binary square matrix with a given row/col sum

    Args:
        N (int): Number of rows/cols
        R (int): Sum of rows/cols
        diag (int or None): Fixed value for diagonal. Takes values None (default), 0, 1.

    Returns:
        numpy.ndarray: an NxN numpy array
    """

    if N==R:
        tmp = np.ones((N,R),dtype=int)
        return tmp
    elif N<R:
        print("Incorrect binary matrix. Check parameters.")
        return
    # create a minimal 2d matrix of zeros for easier indexing
    tmp = np.zeros(2*N,dtype=int).reshape(2,N) 
    cl = binary_combinations(N,R)
    for i in range(N):
        colsums = np.sum(tmp,0)
        # remove excess ones
        idx = np.empty(0,dtype=int)
        for j in np.where(colsums>=R)[0]:
            k = np.where(cl[:,j]>0)[0]
            idx = np.union1d(idx,k)
        cl = np.delete(cl,idx,0)
        # remove excess zeros
        inx = np.empty(0,dtype=int)
        for j in np.where(colsums+N-i == R)[0]:
            k = np.where(cl[:,j]==0)[0]
            inx = np.union1d(inx,k)
        cl = np.delete(cl,inx,0)
        # temporarily ignore diagonal 1s or 0s 
        cli = cl.copy()
        if diag is not None:
            ivx = np.where(cl[:,i]==diag)[0]
            cli = cl[ivx,]
            clk = (cli + colsums)[:,i+1:]
            tp = N-i-1 if diag==0 else 0 # tuning parameter
            ikx = np.where(clk+tp==R)[0]
            cli = np.delete(cli,ikx,0)

        ncl = cl.shape[0]
        ncli = cli.shape[0]
        if ncli > 0:
            ind = np.random.choice(ncli)
            tmp = np.vstack((tmp,cli[ind,:]))
        elif ncli==0 and ncl>0:
            print('Error creating non-zero diagonals. Rerun the function')
            return 0
        else:
            print('Incorrect binary matrix. Check the dimensions.')
            return 
    output = np.delete(tmp,[0,1],0) # remove first 2 empty rows created above
    return(output)

@njit
def dec2bin(x: int, sz: int) -> NDArray[np.int8]:
    """Converts decimal integer to binary array
    
    Args:
        x: An input decimal integer
        sz: The desired minimum size of the output

    Returns:
        A numpy array with leading zeros to match size of sz
    """
    output = []

    while x > 0:
        output.insert(0,x%2)
        x = int(x/2)

    if len(output)<sz:
        output = [0]*(sz-len(output)) + output

    return np.array(output, dtype=np.int8)

@njit
def bin2dec(x: NDArray) -> int:
    """Converts binary list to integer
    
    Args:
        x: An input vector with binary values

    Returns:
        A decimal integer equivalent of the binary input
    """
    return sum(x * 2**(np.arange(len(x))[::-1]))

def random_neighbour(vec,myid,n):
    """Generates a random binary vector that is 1-bit away (a unit Hamming distance)

    Args:
        vec (list or numpy.ndarray): An input vector
        myid (int): An id of an agent of interest
        n (int): Number of tasks allocated to a single agent

    Returns:
        list: A vector with one bit flipped for agent myid
    """

    rnd = np.random.choice(range(myid*n,(myid+1)*n))
    vec[rnd] = 1- vec[rnd]
    return vec

def get_1bit_deviations(bstring: NDArray, n: int, id_: int, num: int) -> NDArray:
    """Generates `num` random binary vectors
    that are 1-bit away from a given bit string.

    Args:
        bstring: An input full N*P-sized  bitstring
        n : Number of tasks allocated to a single agent
        id_ : An id of an agent of interest
        num: Number of neighbor bit strings you want

    Returns:
        A numpy array with num rows of size N*P each, for which exactly 1 bit
        corresponding to Agent id_ is flipped.
    """
    if num > n:
        raise InvalidParameterError("Cannot have more 1bit deviations than there are bits.")

    # first, get num copies of an original bit string
    flipped = np.tile(bstring, (num,1))
    # draw num random indices to flip bits
    indices = n*id_ + np.random.choice(n,num,replace=False)
    # flip bits
    rows = np.arange(num)
    flipped[rows, indices] = 1 - flipped[rows, indices]

    return flipped

@njit
def get_index(vec,myid,n):
    """Gets a decimal equivalent for the bitstring for agent myid

    Args:
        vec (list or numpy.ndarray): An input vector
        myid (int): An id of an agent of interest
        n (int): Number of tasks allocated to a single agent

    Returns:
        int: A decimal value of vec for myid
    """

    return bin2dec(vec[myid*n:(myid+1)*n])


def hamming_distance(x,y):
    """Calculates the Hamming distance (count of different bits) between two bitstrings
    
    Args:
        x (list): first list
        y (list): second list

    Returns:
        int: An integer value

    """
    return np.sum(np.abs(np.array(x) - np.array(y)))

def similarbits(x,p,n,nsoc):
    """Calculates the similarity measure of the bitstring

    Args:
        x (list): the bitstring of interest
        p (int): number of agents
        n (int): number of tasks per agent
        nsoc (int): number of imitated tasks per agent

    Returns:
        float: The float between 0 and 1
    """
    if nsoc>n:
        print('Number of social bits exceeds total number of bits')
    tmp = np.reshape(x, (p,n))
    tmp = np.sum(np.array(tmp), axis=0)[(n-nsoc):]
    tmp = np.max((tmp/p, 1-tmp/p), axis=0)
    output = np.mean(tmp)
    return output


def similarity(x,p,n,nsoc):
    """Calculates the similarity measure of the bitstring

    Args:
        x (list): the bitstring of interest
        p (int): number of agents
        n (int): number of tasks per agent
        nsoc (int): number of imitated tasks per agent

    Returns:
        float: The float between 0 and 1
    """
    if p<2:
        raise InvalidParameterError('Need at least 2 agents for similarity measure')
    if nsoc<1:
        raise InvalidParameterError('Please enter non-zero number of social bits')

    tmp = np.reshape(x, (p,n))[:,(n-nsoc):]
    summ = 0
    for i in range(p):
        for j in range(i,p):
            summ += hamming_distance(tmp[i,:],tmp[j,:])

    max_summ = nsoc*(p/2)**2 if p%2==0 else nsoc*((p-1)/2)**2 + (p-1)*(nsoc/2)
    output = 1-summ/max_summ
    return output

def extract_soc(x,myid,n,nsoc):
    """Extracts social bits from a bitstring

    Args:
        x (numpy.ndarray): An input vector
        myid (int): An id of an agent of interest
        n (int): Number of tasks allocated to a single agent
        nsoc (int): Number of social tasks (exogeneous)

    Returns:
        numpy.ndarray: A vector of size nsoc
    """

    return x[(myid+1)*n-nsoc:(myid+1)*n]