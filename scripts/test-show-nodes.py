import matplotlib
matplotlib.use('TkAgg')
import matplotlib.image as mpimg
from PIL import Image

import pycxsimulator

import pylab as PL
import random as RD
import scipy as SP
import networkx as NX
import random
import itertools

import sys
import os
import pickle
import numpy as np

world_image_path = '.\\world.jpg'
img_width = -1
img_height = -1

lat_max = 90.0
lng_max = 180.0


def load_network_start():
    graph = NX.read_gpickle('../data/graph-data.p')
    return graph


def draw_botnet_status_map(network):
    positions = [[network.node[i]['position']['x'], network.node[i]['position']['y']] for i in network.nodes()]

    PL.figure(1)
    PL.cla()
    PL.imshow(background_image, cmap='gray')

    NX.draw_networkx_nodes(network,
            pos = positions,
            node_color = '#0000cc',
            node_size = 1,
            with_labels = False)

    PL.show()

def init():
    global step
    global network
    global background_image
    global day, hour

    day = hour = step = 0

    background_image = mpimg.imread('world.jpg')
    network = load_network_start()
    network = update_nodes_positions(network)

    NX.write_gpickle(network, '../data/graph-data.p')

def update_nodes_positions(network):
    positions = dict()

    for i in network.nodes():
        x = int(round((network.node[i]['lng'] + lng_max) / (lng_max * 2) * img_width))
        y = int(round((network.node[i]['lat'] + lat_max) / (lat_max * 2) * img_height))
        y = img_height - y
        
        pos = dict()
        pos['x'] = x
        pos['y'] = y
        network.node[i]['position'] = pos

    return network

def draw():
    if network is not None:
        draw_botnet_status_map(network)

def step():
    return 0


if __name__ == '__main__':
    global simulations
    global final_steps

    img_width, img_height = Image.open(world_image_path).size

    interface = pycxsimulator.GUI()
    interface.start(func=[init,draw,step])