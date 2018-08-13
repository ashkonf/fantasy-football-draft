import os
import sys
import re
import bs4
import ntpath
import itertools

import numpy

def levenstein_distance(seq1, seq2):
    size_x = len(seq1) + 1
    size_y = len(seq2) + 1
    matrix = numpy.zeros((size_x, size_y))
    for x in xrange(size_x):
        matrix[x, 0] = x
    for y in xrange(size_y):
        matrix[0, y] = y

    for x in xrange(1, size_x):
        for y in xrange(1, size_y):
            if seq1[x-1] == seq2[y-1]:
                matrix[x,y] = min(
                    matrix[x-1, y] + 1,
                    matrix[x-1, y-1],
                    matrix[x, y-1] + 1
                )
            else:
                matrix[x,y] = min(
                    matrix[x-1,y] + 1,
                    matrix[x-1,y-1] + 1,
                    matrix[x,y-1] + 1
                )
    return (matrix[size_x - 1, size_y - 1])

class ListWrapper(list):
    
    def shuffle(self):
        return random.shuffle(self)
    
    def filter(self, criteria):
        filtered_items = self.__class__()
        for item in self:
            if criteria(item):
                filtered_items.append(item)
        return filtered_items

def concatenate_lists(lists):
    return list(itertools.chain.from_iterable(lists))

