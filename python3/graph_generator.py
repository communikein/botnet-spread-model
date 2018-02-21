# *** Botnet spread in computer network ***
#
# Project by Maracani Elia
# Matricola: 763734
import scipy as SP
import networkx as NX
import random
import itertools

import simplejson as json
import pickle

from timezonefinder import TimezoneFinder
import pytz
from pytz import timezone
from datetime import datetime

import numpy as np
from numpy import array, float32

from math import sin, cos, sqrt, atan2, radians, log, exp

img_width = 1176
img_height = 489

lat_max = 90
lng_max = 180

random.seed()

tf = TimezoneFinder()
utc = pytz.utc

# approximate radius of earth in km
R = 6373.0


DEBUG = True

# Base probability for link between two random nodes
link_prob_base = 0.1

SUSCEPTIBLE = 0
INFECTED = 1

ROLE_NONE = 3
ROLE_SPREAD = 6

global network

def init(population_size):
    global network, positions

    first = True
    time = 0
    day = 0
    hours = 0
    minutes = 0
    botnet_detected = False
    
    # Generate network
    if DEBUG:
        print('Generating graph...')
    network = generate_network(population_size)
    positions = get_nodes_positions(network)
    if DEBUG:
        print('Graph generated.')
        print('---------------------------------------------')

    # Choose random 'patient zero'
    i = random.randint(0, population_size)
    network.node[i]['state'] = INFECTED
    network.node[i]['role'] = ROLE_SPREAD
    network.node[i]['just_infected'] = True

def get_time_zone_difference(node_a, node_b):
    time_zone_a = min(node_a['time_zone'], node_b['time_zone'])
    time_zone_b = max(node_a['time_zone'], node_b['time_zone'])

    if time_zone_a == time_zone_b:
        return 0

    diff_1 = -1
    diff_2 = -1
    steps = -1
    range_check = range(-12, 14 + 1)
    for i in range_check:
        steps += 1

        if time_zone_a == i:
            diff_1 = 0

        elif time_zone_b == i:
            diff_1 += 1
            diff_2 = len(range_check) - steps - 1

            for j in range_check:
                diff_2 += 1

                if j == time_zone_a:
                    break

            break

        elif diff_1 >= 0:
            diff_1 += 1

    return min(diff_1, diff_2)

def generate_network(n, is_random=False):
    # Create the nodes and populate them with defaults values
    if DEBUG:
        print('Generating ' + str(n) + ' nodes...')

    # Create a non-directed graph
    G = NX.Graph()
    
    # Add n nodes to the graph
    G.add_nodes_from(range(n))
    G = init_nodes(G)
    
    # If the link probability is grater or equal to 0, return a complete graph
    if link_prob_base >= 1:
        return complete_graph(n, create_using=G)

    # Get all the possible links
    if DEBUG:
        print('Generating all the possible egdes...')
    edges = itertools.combinations(range(n), 2)

    # Choose the links to keep either based on the time zones or randomly
    if not is_random:
        if DEBUG:
            print('Choosing the links to keep based on nodes location...')
        for e in edges:
            distance = get_distance(G.node[e[0]], G.node[e[1]])
            if random.random() < link_prob(distance, link_prob_base):
                G.add_edge(*e)
    else:
        if DEBUG:
            print('Choosing the links to keep randomly...')
        for e in edges:
            if random.random() < link_prob_base:
                G.add_edge(*e)

    return G

def choose_latitude():
    rnd = random.uniform(-90, 90)
    return round(rnd, 2)

def choose_longitude():
    rnd = random.uniform(-180, 180)
    return round(rnd, 2)

def init_nodes(graph):
    for i in graph.nodes():
        # Generate valid coordinates
        while True:
            lat = choose_latitude()
            lng = choose_longitude()
            time_zone = get_time_zone(lat, lng)
            if time_zone is not None:
                break

        # Assign values to node
        graph.node[i]['lat'] = lat
        graph.node[i]['lng'] = lng
        graph.node[i]['time_zone'] = time_zone
        graph.node[i]['state'] = SUSCEPTIBLE
        graph.node[i]['role'] = ROLE_NONE
        graph.node[i]['just_infected'] = False

    return graph

def get_time_zone(latitude, longitude):
    today = datetime.now()

    tz_target_name = tf.timezone_at(lat=latitude, lng=longitude)
    if (tz_target_name is None):
        return None

    tz_target = timezone(tz_target_name)
    today_target = tz_target.localize(today)
    today_utc = utc.localize(today)

    return (today_utc - today_target).total_seconds() // (60 * 60)

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

def get_nodes_positions(network):
    positions = dict()

    for i in network.nodes():
        x = (network.node[i]['lng'] + lng_max) / (lng_max * 2) * img_width
        y = (network.node[i]['lat'] + lat_max) / (lat_max * 2) * (img_height + lat_max)
        y = img_height - y + lat_max

        pos = [x, y]

        positions[i] = array(pos, dtype=float32)

    return get_nodes_positions

def saveGraph():
    NX.write_gpickle(network, '../data/graph-data.pickle')

def loadInternetDevicesJson():
    global internet_data

    with open('../data/internet-usage-data-cleaned.json', 'r') as f:
        internet_data = json.load(f)

    with open('../data/internet-usage-data.p', 'wb') as fp:
        pickle.dump(internet_data, fp, protocol=pickle.HIGHEST_PROTOCOL)

def loadPickletInternetData():
    global internet_data

    with open('../data/internet-usage-data.p', 'rb') as fp:
        internet_data = pickle.load(fp)



if __name__ == "__main__":
    loadPickletInternetData()
    print(internet_data)
    init(population_size=5000)
    saveGraph()