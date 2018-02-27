# *** Botnet spread in computer network ***
#
# Project by Maracani Elia
# Matricola: 763734

import networkx as NX
import itertools
import random

import pickle

from numpy import array, float32
from math import sin, cos, sqrt, atan2, radians, log, exp

from botnetspread import SUSCEPTIBLE, SUSCEPTIBLE, ROLE_NONE, ROLE_SPREAD

random.seed()

# approximate radius of earth in km
R = 6373.0
DEBUG = True

# Base probability for link between two random nodes
link_prob_base = 0.1


def finalize_graph(graph):
    first = True
    time = 0
    day = 0
    hours = 0
    minutes = 0
    botnet_detected = False
    
    # Generate network
    if DEBUG:
        print('Loading graph...')
    graph = compute_graph_links(graph)
    population_size = len(graph.nodes())
    if DEBUG:
        print('Graph loaded. - ')
        print('---------------------------------------------')

    # Choose random 'patient zero'
    i = random.randint(0, population_size)
    graph.node[i]['state'] = INFECTED
    graph.node[i]['role'] = ROLE_SPREAD
    graph.node[i]['just_infected'] = True

    return graph

def compute_graph_links(graph):
    population_size = len(graph.nodes())

    # Get all the possible links
    if DEBUG:
        print('Generating all the possible egdes...')
    edges = itertools.combinations(range(population_size), 2)

    # Choose the links to keep based on the time zones
    if DEBUG:
        print('Choosing the links to keep based on nodes location...')
    for e in edges:
        distance = get_distance(graph.node[e[0]], graph.node[e[1]])
        if random.random() < link_prob(distance, link_prob_base):
            graph.add_edge(*e)

    return graph

def get_distance(node_a, node_b):
    dlon = node_b['lng'] - node_a['lng']
    dlat = node_b['lat'] - node_a['lat']

    a = sin(dlat / 2)**2 + cos(node_a['lat']) * cos(node_b['lat']) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c

def link_prob(distance, base_prob):
    min_prob = 0.000039
    max_prob = 0.999961

    b = log(max_prob / min_prob) / (max_prob - min_prob)
    #print('B: ' + str(b))

    a = min_prob / exp(b * min_prob)
    #print('A: ' + str(a))

    prob = 1 - (distance / 20040.0)

    exp_prob = a * exp(prob * b)

    return base_prob * exp_prob


if __name__ == "__main__":
    graph = NX.read_gpickle('../data/graph-data.p')
    graph = finalize_graph(graph)
    
    NX.write_gpickle(graph, '../data/graph-data-complete.p')