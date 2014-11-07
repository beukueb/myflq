from operator import mul
import itertools
import collections
from functools import reduce


def PE0Lon(observed_list,nonobserved_list):
    """
    Function calculates the PEL0 for each locus and puts the results in list PE0L_list
    PEL0 is the RMNE value for the locus assuming that exactly 0 drop-outs have occurred.
    The function takes as input 2 list of lists: 
     -list of the frequencies in the population of the observed alleles for each locus 
       ([[freq. of observed alleles in locus 1],[freq. of observed in locus 2],...])
     -list of the frequencies in the population of the nonobserved alleles for each locus (is not actually used in the calculation)
       ([[freq. of nonobserved alleles in locus 1],[freq. of nonobserved in locus 2],...])
     the loci need to be in the same order on both lists of lists
    """
    PE0L_list=[]
    for listperlocus_o,listperlocus_n in zip(observed_list,nonobserved_list):
        PE0L=(sum(listperlocus_o))**2
        if PE0L==0: # when there are no observed alleles, the locus is ignored and PE0L is 1
            PE0L=1
        PE0L_list.append(PE0L)
    return PE0L_list


def PE1Lon(observed,nonobserved):
    """
    Function calculates the PEL0 for each locus and puts the results in list PE1L_list
    PEL1 is the RMNE value for the locus assuming that exactly 1 drop-out has occurred.
    The function takes as input 2 list of lists: 
     -list of the frequencies in the population of the observed alleles for each locus 
       ([[freq. of observed alleles in locus 1],[freq. of observed in locus 2],...])
     -list of the frequencies in the population of the nonobserved alleles for each locus
       ([[freq. of nonobserved alleles in locus 1],[freq. of nonobserved in locus 2],...])
     the loci need to be in the same order on both lists
    """
    PE1L_list=[]
    for listperlocus_o,listperlocus_n in zip(observed,nonobserved):
        PE1L=(sum(listperlocus_o)*sum(listperlocus_n)*2)
        PE1L_list.append(PE1L)
    return PE1L_list


def PE2Lon(observed,nonobserved):
    """
    Function calculates the PEL2 for each locus and puts the results in list PE2L_list
    PEL2 is the RMNE value for the locus assuming that exactly 2 drop-outs have occurred.
    The function takes as input 2 list of lists: 
     -list of the frequencies in the population of the observed alleles for each locus 
       ([[freq. of observed alleles in locus 1],[freq. of observed in locus 2],...])
     -list of the frequencies in the population of the nonobserved alleles for each locus
       ([[freq. of nonobserved alleles in locus 1],[freq. of nonobserved in locus 2],...])
     the loci need to be in the same order on both lists o
    """
    PE2L_list=[]
    for listperlocus_o,listperlocus_n in zip(observed,nonobserved):
        PE2L=(sum(listperlocus_n))**2
        so=sum(listperlocus_o)
        if so==0: # when there are no observed alleles, the locus is ignored and PE2L is 0
            PE2L=0
        PE2L_list.append(PE2L)
    return PE2L_list


def calculate_combinations(combination,PE0Ls,PE1Ls,PE2Ls,PE0Lsreduced):
    """
    Calculate the RMNE value based on the observed and nonobserved alleles and a certain combination of drop-outs
    
    This function takes as input:
     - A combination consisting of a list of loci where drop-outs have occurred.
       When multiple drop-outs have occurred in the same locus, the number of the locus is multiple times in this list
     - A list with the PE0Ls from each locus
     - A list with the PE1Ls from each locus
     - A list with the PE2Ls from each locus
     - PE0Lsreduced: the RMNE calculation as if there are no drop-outs 
    
    """
    
    loci_with_2dropouts=[] # list of loci where exact 2 drop-outs have occurred considering the combination
    loci_with_1dropout=[] # list of loci where exact 2 drop-outs have occurred considering the combination
    
    for x, y in collections.Counter(combination).items(): # for each locus with at least a drop-out, determine how many drop-outs are in the locus
        if y==2: # when there are exact 2 drop-outs in a locus, put this locus in the loci_with_2dropouts list
            loci_with_2dropouts.append(x)
        elif y==1: # when there are exact 1 drop-outs in a locus, put this locus in the loci_with_1dropout list
            loci_with_1dropout.append(x)
    
    # in stead of calculating the RMNE value for the profile and the drop-outs in the combination, 
    # the RMNE value with no drop-outs is used as a basis value which is corrected for each locus with one or 2 drop-outs
    PEc=PE0Lsreduced
    for c in loci_with_1dropout:
            PEc=(PEc/PE0Ls[int(c)])*PE1Ls[int(c)]
    for c in loci_with_2dropouts: 
            PEc=(PEc/PE0Ls[int(c)])*PE2Ls[int(c)]
    return(PEc)


def PE(PE0Ls,PE1Ls,PE2Ls,DO):
    """
    Function calculates the RMNE value of the profile assuming an exact number of drop-outs DO.
    Generate all possible combinations of exactly DO drop-outs in the number of loci. 
    The number of loci is determined based on the length of the PE0Ls list, which contains the PE0Ls from each locus.
        
    This function takes as input:
     - A list with the PE0Ls from each locus
     - A list with the PE1Ls from each locus
     - A list with the PE2Ls from each locus
     The loci need to be in the same order in the lists 
     - The number of drop-outs
    """
    
    loci=list(range(0,len(PE0Ls))) # make a list with a number for each locus in the analysis based on the length of the PE0Ls list
    n_loci=[val for val in loci for _ in (0, 1)] # make list containing each locus number 2 times. e.g. [1,1,2,2,...]
    PE0Lsreduced=reduce(mul, PE0Ls, 1) # Caculate the RMNE value with 0 drop-outs
    
    
    if DO==0: 
        return (DO,PE0Lsreduced) # when there are no drop-outs, return the RMNE value for 0 drop-outs
    else: 
        # When there are drop-outs, make all combinations of DO drop-outs in the number of loci. 
        # All combinations are generated of DO elements from n_loci elements. 
        # Each element in the list can be used one time in a combination.
        # Each locus is 2 times in the n_loci list and thus
        # each locus can be 2 times in the combination.
        combinations=itertools.combinations(n_loci,DO)
    
    PE=0
    # Generating the combinations as stated above, creates doubles. With set, a list of unique combinations is created.
    for combination in set(combinations):
        # For each combination: calculate the PE value of that combination. The final PE value is the sum of PE values from all these combinations
        PE+=calculate_combinations(combination,PE0Ls,PE1Ls,PE2Ls,PE0Lsreduced)
    return (DO,PE)


def PElist(PE0Ls,PE1Ls,PE2Ls,allowedDO):
    """
    This function calculates the PE (see PE function) for a range of drop-outs starting from 0 to the number of allowedDO
    Returns a list of tuples with the number of drop-outs and the corresponding PE value
    """
    values=[]
    for i in range(0,allowedDO+1):
        values.append(PE(PE0Ls,PE1Ls,PE2Ls,i))
    return (values)


def PE_star(x):
    return PE(*x)


def PElist_multi_proc(PE0Ls,PE1Ls,PE2Ls,allowedDO):
    from multiprocessing import Pool
    """
    This function calculates the PE (see PE function) for a range of drop-outs starting from 0 to the number of allowedDO
    Returns a list of tuples with the number of drop-outs and the corresponding PE value.
    Each PE is caclulated in a separate process.
    """
    PE_list=[]
    pool = Pool()
    changing_arg=range(0,allowedDO+1)
    values=pool.map(PE_star, zip(itertools.repeat(PE0Ls),itertools.repeat(PE1Ls),itertools.repeat(PE2Ls),changing_arg))
    pool.close()
    pool.join()
    return (values)
