import matplotlib
matplotlib.use('TkAgg')

import pylab as PL
import random as RD
import scipy as SP
import networkx as NX
import random
import itertools

import pickle

SUSCEPTIBLE = 0
INFECTED = 1
IMMUNE = 2

history_path_base = '../data/results/'
simulation_number = 1
history_path = history_path_base + str(simulation_number) + '/history/'

def loadNetworkHistoryFile(step):
    data = dict()

    # Read data from CSV and convert to JSON
    fieldNames = ('infected', 'immune', 'susceptible', 'spread', 'attack', 'control')
    with open(results_path, 'r') as f:
        reader = csv.DictReader(f, fieldNames)
        rows = [row for row in reader]
        # Remove the headers
        del rows[0]
    
    out = json.dumps(rows)
    return json.loads(out)


def draw_botnet_status_map(background_image, network, positions):
    PL.figure(1)
    PL.cla()
    PL.imshow(background_image, cmap='gray')

    # To show also the edges use NX.draw, instead of NX.draw_networkx_nodes. 
    # Also, add the following arguments: width=0.3, edge_color='#333333'
    NX.draw_networkx_nodes(network,
            pos = positions,
            node_color = get_nodes_color(network),
            node_size = 10,
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

def get_nodes_color(network):
    nodes_color = [get_node_color(network.node[i]) for i in network.nodes()]

    return nodes_color


def init():
    global step
    global network

    

    step = 0
    statistics = loadStatisticsFile()

    print(type(statistics))

def draw():
    draw_botnet_status_map(infectedData, immuneData, step)

def step():
    global step
    global infectedData, immuneData

    infectedData.append(int(statistics[step]['infected']))
    immuneData.append(int(statistics[step]['immune']))

    step += 1


import pycxsimulator
pycxsimulator.GUI().start(func=[init,draw,step])