import matplotlib
matplotlib.use('TkAgg')
import matplotlib.image as mpimg

import pylab as PL
import random as RD
import scipy as SP
import networkx as NX
import random
import itertools

import os
import pickle
import numpy as np

SUSCEPTIBLE = 0
INFECTED = 1
IMMUNE = 2

history_path_base = '../data/results/central-server-hybrid/01'
simulation_number = 1
history_path = history_path_base + str(simulation_number) + '/'

def load_network_start():
    graph = NX.read_gpickle('../data/graph-data-hybrid.p')
    return graph

def load_network_history(day, step):
    data = dict()

    history_step_file = history_path + str(day) + '/'
    history_step_file += 'botnet-evolution-' + '0' * (4 - len(str(step))) + str(step) + '.p'

    try:
        with open(history_step_file, 'rb') as origin:
            data = pickle.load(origin)
    except:
        return None

    return data


def draw_botnet_status_map(network):
    positions = [[network.node[i]['position']['x'], network.node[i]['position']['y']] for i in network.nodes()]

    PL.figure(1)
    PL.cla()
    PL.imshow(background_image, cmap='gray')

    # To show also the edges use NX.draw, instead of NX.draw_networkx_nodes. 
    # Also, add the following arguments: width=0.3, edge_color='#333333'
    NX.draw_networkx_nodes(network,
            pos = positions,
            node_color = get_nodes_color(network),
            node_size = 1,
            with_labels = False)

    PL.show()


def get_nodes_color(network):
    nodes_color = [get_node_color(network.node[i]) for i in network.nodes()]

    return nodes_color

def get_node_color(node):
    if is_node_online(node):
        # Assign color red
        if node['state'] == INFECTED:
            return '#cc0000'

        # Assign color green
        elif node['state'] == IMMUNE:
            return '#00cc00'

        # Assign color blue
        elif node['state'] == SUSCEPTIBLE:
            return '#0000cc'
    else:
        # Assign color dark red
        if node['state'] == INFECTED:
            return '#500000'

        # Assign color dark green
        elif node['state'] == IMMUNE:
            return '#005000'

        # Assign color dark blue
        elif node['state'] == SUSCEPTIBLE:
            return '#000050'

def is_node_online(node):
    local_time = hour + node['time_zone']

    if local_time >= 8 and local_time <= 22:
        return True
    else:
        return False

def get_nodes_color(network):
    nodes_color = [get_node_color(network.node[i]) for i in network.nodes()]

    return nodes_color


def init():
    global step
    global network
    global background_image
    global day, hour

    day = hour = step = 0

    background_image = mpimg.imread('world.png')
    network = load_network_start()
    history = load_network_history(0, 0)

def draw():
    if network is not None:
        draw_botnet_status_map(network)

def step():
    global network
    global step, hour, day

    day = (step * 15) / (24 * 60)

    time = (step * 15) - (day * 24 * 60)
    hour = int(time / 60)

    step += 1
    print('STEP: ' + str(step))
    history = load_network_history(day, step)

    for i in history:
        network.node[i]['state'] = history[i]['state']
        network.node[i]['role'] = history[i]['role']
    


import pycxsimulator
pycxsimulator.GUI().start(func=[init,draw,step])