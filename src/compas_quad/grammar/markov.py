from random import random

from typing import List
from typing import Mapping
from typing import Optional

import numpy as np

from scipy.stats import bernoulli
from scipy.stats import multinomial


def equilibrium_distribution(p_transition: np.array) -> np.array:
    n_states = p_transition.shape[0]

    A = np.append(arr=p_transition.T - np.eye(n_states),
                  values=np.ones(n_states).reshape(1, -1),
                  axis=0)
    b = np.transpose(np.array([0] * n_states + [1]))
    p_eq = np.linalg.solve(a=np.transpose(A).dot(A), b=np.transpose(A).dot(b))

    return p_eq


def normalize_rows(p_array: np.array) -> np.array:
    """
    Normalize the rows of an array such that their row-wise elements sum to one.
    """
    p_array = np.atleast_2d(p_array)
    return p_array / np.sum(p_array, axis=1, keepdims=True)


def markov_sequence(p_init: np.array,
                    p_transition: np.array,
                    sequence_length: int) -> List[int]:
    """
    Generate a Markov sequence based on p_init and p_transition.
    """
    assert np.allclose(np.sum(p_init), 1.0)
    assert np.allclose(np.sum(p_transition), p_transition.shape[0])

    initial_state = list(multinomial.rvs(1, p_init)).index(1)

    states = [initial_state]
    for _ in range(sequence_length - 1):
        p_tr = p_transition[states[-1]]
        new_state = list(multinomial.rvs(1, p_tr)).index(1)
        states.append(new_state)

    return states


def sequence_to_grammar_string(sequence: List, rules: Mapping[int, str]) -> str:
    """
    Convert a sequence of states to a sequence of grammar rules.
    We a dictionary that maps state indices to grammar rules.
    """
    return ''.join([rules[state] for state in sequence])


def string_generation_markov(characters: str,
                             number: int,
                             length: int,
                             p_init: List[float],
                             p_transition: List[float],
                             seed: int = None) -> str:
    """
    Generate strings of character grammars following a Markov chain approach.
    """
    np.random.seed(seed)

    rules = {i: rule for i, rule in enumerate(characters)}

    p_transition = np.array(p_transition)
    if p_init is None:
        p_init = equilibrium_distribution(p_transition)
    else:
        p_init = np.array(p_init)

    p_init = normalize_rows(p_init).ravel()
    p_transition = normalize_rows(p_transition)

    for _ in range(number):
        sequence = markov_sequence(p_init, p_transition, length)
        yield sequence_to_grammar_string(sequence, rules)


def string_generation_markov_budget(characters: str,
                                    num_sentences: int,
                                    num_words: int,
                                    num_characters: int,
                                    p_init: np.array,
                                    p_transition: np.array,
                                    seed: int) -> str:
    # set random seed
    np.random.seed(seed=seed)

    # create mapping of indices to rules
    rules = {i: rule for i, rule in enumerate(characters)}

    # vectorize inputs
    p_transition = np.array(p_transition)

    # compute p_init from equilibrium distribution
    if p_init is None:
        p_init = equilibrium_distribution(p_transition)
    p_init = np.array(p_init)

    # ensure that the rows of p sum to 1
    p_init = normalize_rows(p_init).ravel()
    p_transition = normalize_rows(p_transition)

    for i in range(num_sentences):

        sentence = ''
        for j in range(num_words):

            sequence = markov_sequence(p_init, p_transition, num_characters)
            word = sequence_to_grammar_string(sequence, rules)

            # sample word type
            # if word type is stop, break
            x = random()
            if x > 0.5 or j == num_words - 1:
                word = 'a' + word[:-2] + 'a'

            sentence += word

        yield sentence


def string_generation_markov_budget_turbo(characters: str,
                                    num_sentences: int,
                                    num_words: int,
                                    num_characters: int,
                                    p_init: np.array,
                                    p_transition: np.array,
                                    seed: int):
    # set random seed
    np.random.seed(seed=seed)

    # create mapping of indices to rules
    rules = {i: rule for i, rule in enumerate(characters)}

    # vectorize inputs
    p_transition = np.array(p_transition)

    # compute p_init from equilibrium distribution
    if p_init is None:
        p_init = equilibrium_distribution(p_transition)
    p_init = np.array(p_init)

    # ensure that the rows of p sum to 1
    p_init = normalize_rows(p_init).ravel()
    p_transition = normalize_rows(p_transition)

    for i in range(num_sentences):

        sentence = ''
        for j in range(num_words):

            # list(multinomial.rvs(1, p_init)).index(1)
            initial_state = bernoulli.rvs(p=p_init)

            # markov chain
            states = [initial_state]
            for _ in range(num_characters - 1):
                p_tr = p_transition[states[-1]]
                new_state = list(multinomial.rvs(1, p_tr)).index(1)
                states.append(new_state)

            word = sequence_to_grammar_string(sequence, rules)

            # sample word type
            # if word type is stop, break
            x = random()
            if x > 0.5 or j == num_words - 1:
                word = 'a' + word[:-2] + 'a'

            sentence += word

        # print()
        # print(sentence)
        yield sentence
