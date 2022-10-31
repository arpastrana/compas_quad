from itertools import product
from random import random


def string_generation_brute(characters, length):
    for letters in product(characters, repeat=length):
        yield ''.join(letters)


def string_generation_random(characters, number, length, ratios=None):
    if not ratios:
        ratios = [1.0 / len(characters)] * len(characters)

    for _ in range(number):
        string = ''
        for _ in range(length):
            x = random()
            for i in range(len(characters)):
                if x < sum(ratios[:i + 1]):
                    string += characters[i]
                    break
        yield string


def string_generation_structured(characters, number, length):

    for _ in range(number):
        string = ''
        polyedge_length = 0  # number of 't' between odd and even pari of 'a'

        for i in range(length):

            # add strip before end of string if polyedge is being collected
            if i == length - 1 and polyedge_length != 0:
                string += 'a'
                polyedge_length = 0
                continue

            x = random()

            # NO polyedge being collected - uniform chances
            if polyedge_length == 0:
                if x < 0.33:
                    string += 't'
                elif x < 0.67:
                    string += 'p'
                else:
                    string += 'a'
                    polyedge_length += 1

            # polyedge being collected - more chances to obtain 't' or 'p'

            # do not add if polyedge has only one vertex
            elif polyedge_length == 1:
                if x < 0.5:
                    string += 't'
                    polyedge_length += 1
                else:
                    string += 'p'

            else:
                if x < 0.4:
                    string += 't'
                    polyedge_length += 1
                elif x < 0.8:
                    string += 'p'
                else:
                    string += 'a'
                    polyedge_length = 0

        yield string


def string_generation_markov(characters, number, length):
    """
    Generate a string of character grammars following a Markov chain approach.
    """
    pass
