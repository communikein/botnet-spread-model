# *** Botnet spread in computer network ***
#
# Project by Maracani Elia
# Matricola: 763734

import matplotlib
matplotlib.use('TkAgg')

import pylab as PL
import random as RD
import scipy as SP
import networkx as NX
import random
import itertools

from timezonefinder import TimezoneFinder
from pytz import timezone
import pytz
from datetime import datetime

from numpy import array, float32
import numpy as np
from PIL import Image

from math import sin, cos, sqrt, atan2, radians, log, exp

img_width = 1176
img_height = 489

lat_max = 90
lng_max = 180

image = Image.open("world.png").convert("L")
arr_img = np.asarray(image)

RD.seed()

tf = TimezoneFinder()
utc = pytz.utc

# approximate radius of earth in km
R = 6373.0


DEBUG = True

# Every step of the simulator is equals to 'time_multiplier' minutes
time_multiplier = 15
# Time zone utils
time_zone_min = -12
time_zone_max = 14

### Simulation parameters
# Number of nodes in the network, it will be loaded from file
population_size = -1
# Base probability for link between two random nodes
link_prob_base = 0.1

# Probability to be infected without having an infected node in my neighbors, 
# it will be computed once the graph is loaded from file.
initial_infection_prob = -1
# Probability of infections having an infected node in my neighbors
infection_prob = 0.01

# Number of Security Reserachers looking for threats at the same time
# Only take the integer digits, leave out the decimal ones. It will be computed
# once the graph is loaded from file.
sr_amount = -1
# Probability of a node to get an update for its antivirus, and hance recovered
av_update_prob = 0.005
# Probability of the botnet to be detected
botnet_detection_prob = av_update_prob / 10

# Probability of a node to be chosen as spread type, once infected
spread_prob = 0.3
# Probability of a node to be chosen as attack type, once infected
attack_prob = 0.4
# Probability of a node to be chosen as control type, once infected
control_prob = 1 - spread_prob - attack_prob

SUSCEPTIBLE = 0
INFECTED = 1
IMMUNE = 2

ROLE_NONE = 3
ROLE_ATTACK = 4
ROLE_CONTROL = 5
ROLE_SPREAD = 6



def init(keep_patient_zero=True):
    global first
    global steps, days, hours, minutes
    global network, next_network, positions
    global n_infected, n_susceptible, n_immune
    global n_spread, n_attack, n_control
    global infectedData, susceptibleData, immuneData
    global spreadData, attackData, controlData
    global botnet_detected
    global population_size, initial_infection_prob, sr_amount

    first = True
    steps = days = hours = minutes = 0
    n_infected = n_susceptible = n_immune = 0
    n_attack = n_spread = n_control = 0
    botnet_detected = False
    
    # Generate network
    print('Generating graph...')

    network = load_graph()
    population_size = len(network.nodes())
    initial_infection_prob = 0.005 / population_size
    sr_amount = int(population_size * 0.005)
    positions = get_nodes_positions(network)
    
    print('Graph generated.')
    print('---------------------------------------------')

    if not keep_patient_zero:
        # Remove previously selected 'patient zero'
        for i in network.nodes():
            network.node[i]['state'] = SUSCEPTIBLE
            network.node[i]['role'] = ROLE_NONE
            network.node[i]['just_infected'] = False

        # Choose random 'patient zero'
        i = random.randint(0, len(network.nodes()))
        network.node[i]['state'] = INFECTED
        network.node[i]['role'] = ROLE_SPREAD
        network.node[i]['just_infected'] = True

        if DEBUG:
            print('Random \'patient zero\' chosen.')
            print('Node n.' + str(i))
            print('Time zone: ' + str(network.node[i]['time_zone']))
            print('---------------------------------------------')

    n_spread = n_infected = 1
    n_susceptible = population_size - n_infected

    print_data()

    next_network = network.copy()

    infectedData = [n_infected]
    immuneData = [n_immune]
    susceptibleData = [n_susceptible]

    spreadData = [n_spread]
    attackData = [n_attack]
    controlData = [n_control]

    save_step_data()

def load_graph():
    graph = NX.read_gpickle('graph-data.pickle')
    return graph

def get_nodes_positions(network):
    positions = dict()

    for i in network.nodes():
        x = (network.node[i]['lng'] + lng_max) / (lng_max * 2) * img_width
        y = (network.node[i]['lat'] + lat_max) / (lat_max * 2) * (img_height + lat_max)
        y = img_height - y + lat_max

        pos = [x, y]

        positions[i] = array(pos, dtype=float32)

    return positions

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

def draw():
    global positions, network, first
    
    PL.figure(1)
    PL.cla()
    PL.imshow(arr_img, cmap='gray')

    if not first:
        # To show also the edges use NX.draw, instead of NX.draw_networkx_nodes. 
        # Also, add the following arguments: width=0.3, edge_color='#333333'
        NX.draw_networkx_nodes(network,
                pos = positions,
                node_color = get_nodes_color(network),
                node_size = 10,
                with_labels = False)

    first = False
    PL.title(print_time())
    PL.show()

    PL.figure(2)
    PL.cla()
    PL.plot(infectedData, 'r')
    PL.plot(immuneData, 'g')
    PL.title('Botnet propagation - step ' + str(steps))
    

def step():
    global steps
    global network, next_network
    global n_infected, n_susceptible, n_immune
    global n_attack, n_control, n_spread
    global botnet_detected

    steps += 1
    n_infected = n_susceptible = n_immune = 0
    n_attack = n_control = n_spread = 0
    save_time(steps)

    # Check if the botnet has been detected
    botnet_detected = botnet_got_detected(network)

    # For each node in the network
    for i in network.nodes():
        
        # If the node is up
        if is_node_online(network.node[i]):
            
            # If the botnet has been detected, then the node might have an updated antivirus
            # that allows the node to be immune against attacks
            if botnet_detected and is_antivirus_updated(network.node[i]):
                next_network.node[i]['state'] = IMMUNE
                next_network.node[i]['role'] = ROLE_NONE
                next_network.node[i]['lat'] = network.node[i]['lat']
                next_network.node[i]['lng'] = network.node[i]['lng']
                next_network.node[i]['time_zone'] = network.node[i]['time_zone']

            # If the node is susceptible, then it might become source of infection
            elif is_node_susceptible(network.node[i]):

                # Try to infect it
                if got_infected_by_hacker(network.node[i]):
                    next_network.node[i]['state'] = INFECTED
                    next_network.node[i]['role'] = choose_role()
                    next_network.node[i]['just_infected'] = True
                    next_network.node[i]['lat'] = network.node[i]['lat']
                    next_network.node[i]['lng'] = network.node[i]['lng']
                    next_network.node[i]['time_zone'] = network.node[i]['time_zone']

            # If the node is infected, then it might infect others
            elif is_node_infected(network.node[i]):

                # The node has not been detected, thus remains infected
                next_network.node[i]['state'] = network.node[i]['state']
                next_network.node[i]['role'] = network.node[i]['role']
                next_network.node[i]['just_infected'] = network.node[i]['just_infected']
                next_network.node[i]['lat'] = network.node[i]['lat']
                next_network.node[i]['lng'] = network.node[i]['lng']
                next_network.node[i]['time_zone'] = network.node[i]['time_zone']

                # If the node is has the role to spread
                if is_node_spreading(network.node[i]):
                    # Try to spread to all its neighbors
                    for j in network.neighbors(i):
                        # If the neighbor is susceptible
                        if is_node_online(network.node[j]) and is_node_susceptible(network.node[j]):
                            # Try to infect it
                            if got_infected_by_node(network.node[j]):
                                next_network.node[j]['state'] = INFECTED
                                next_network.node[j]['role'] = choose_role()
                                next_network.node[j]['just_infected'] = True
                                next_network.node[j]['lat'] = network.node[j]['lat']
                                next_network.node[j]['lng'] = network.node[j]['lng']
                                next_network.node[j]['time_zone'] = network.node[j]['time_zone']
                                break
    
    # Get, print and save statistics
    get_statistics(next_network)
    print_data()
    save_step_data()

    del network
    network = next_network.copy()
    

def get_random_online_node(network):
    online = False
    while not online:
        index = RD.randrange(0, population_size - 1)
        node = network.node[index]
        online = is_node_online(node)

    return node

def is_node_online(node):
    local_time = hours + node['time_zone']

    if local_time >= 8 and local_time <= 22:
        return True
    else:
        return False

def is_node_infected(node):
    if node['state'] == INFECTED and not node['just_infected']:
        return True
    else:
        return False

def is_node_susceptible(node):
    if node['state'] == SUSCEPTIBLE:
        return True
    else:
        return False

def is_node_spreading(node):
    if is_node_infected(node) and node['role'] == ROLE_SPREAD:
        return True
    else:
        return False

def botnet_got_detected(network):
    if botnet_detected:
        return True

    for i in range(1, sr_amount):
        # Choose a random online node
        node = get_random_online_node(network)

        # If the node is not infected, than the SR surely can't detect the botnet
        if node['state'] != INFECTED:
            continue

        # If the node is infected, it's chances to be detected depends on the amount
        # of traffic it generates, hance it depends on its role.
        rnd = RD.random()
        multiplier = 1
        threshold = botnet_detection_prob

        if node['role'] == ROLE_ATTACK:
            multiplier = 1
        elif node['role'] == ROLE_CONTROL:
            multiplier = 2
        elif node['role'] == ROLE_SPREAD:
            multiplier = 5

        if rnd < threshold * multiplier:
            return True

    return False

def is_antivirus_updated(node):
    # If the botnet has not been detected yet, the node's antivirus 
    # cannot be updated against it
    if not botnet_detected:
        return False

    rnd = RD.random()
    multiplier = 0.8

    # If the node's antivirus is updated
    if rnd < av_update_prob * multiplier:
        return True
    else:
        return False

def got_infected_by_hacker(node):
    rnd = RD.random()
    return rnd < initial_infection_prob

def got_infected_by_node(node):
    rnd = RD.random()
    return rnd < infection_prob

def choose_role():
    rnd = RD.random()

    if rnd < spread_prob:
        return ROLE_SPREAD
    elif rnd < spread_prob + attack_prob:
        return ROLE_ATTACK
    else:
        return ROLE_CONTROL



def save_time(steps):
    global days, hours, minutes
    
    days = (steps * time_multiplier) / (24 * 60)

    time = (steps * time_multiplier) - (days * 24 * 60)
    hours = int(time / 60)
    minutes = int(time - hours * 60)

def print_time():
    str_hours = '0' + str(hours)
    if (hours >= 10):
        str_hours = str(hours)

    str_minutes = '0' + str(minutes)
    if (minutes >= 10):
        str_minutes = str(minutes)

    message = 'Day: ' + str(days) + ', Time: ' + str(str_hours) + ":" + str(str_minutes)
    return message

def print_data():
    print(print_time())
    print('N. infected: ' + str(n_infected))
    print('N. immune: ' + str(n_immune))
    print('N. susceptible: ' + str(n_susceptible))
    print('')

def get_statistics(network):
    global n_infected, n_immune, n_susceptible
    global n_spread, n_attack, n_control
    global infectedData, immuneData, susceptibleData
    global spreadData, attackData, controlData
    global nodes_color

    for i in network.nodes():
        network.node[i]['just_infected'] = False

        if network.node[i]['state'] == INFECTED:
            n_infected += 1

            if network.node[i]['role'] == ROLE_SPREAD:
                n_spread += 1
            elif network.node[i]['role'] == ROLE_ATTACK:
                n_attack += 1
            else:
                n_control += 1

        elif network.node[i]['state'] == IMMUNE:
            n_immune += 1

        elif network.node[i]['state'] == SUSCEPTIBLE:
            n_susceptible += 1

    # Prepare the data to be plotted
    infectedData.append(n_infected)
    immuneData.append(n_immune)
    susceptibleData.append(n_susceptible)

    spreadData.append(n_spread)
    attackData.append(n_attack)
    controlData.append(n_control)

def create_data_file(path='results.txt'):
    f = open('results.txt', 'w')
    f.write('@SETTINGS\n')
    f.write('population_size: ' + str(population_size) + '\n')
    f.write('link_prob_base: ' + str(link_prob_base) + '\n')
    f.write('initial_infection_prob: ' + str(initial_infection_prob) + '\n')
    f.write('infection_prob: ' + str(infection_prob) + '\n')
    f.write('av_update_prob: ' + str(av_update_prob) + '\n')
    f.write('spread_prob: ' + str(spread_prob) + '\n')
    f.write('attack_prob: ' + str(attack_prob) + '\n')
    f.write('control_prob: ' + str(control_prob) + '\n\n')

    f.write('@DATA\n')
    f.close()

def save_step_data(path='results.txt'):
    f = open(path, 'a')
    f.write('#\n')
    f.write('infected: ' + str(n_infected) + '\n')
    f.write('immune: ' + str(n_immune) + '\n')
    f.write('susceptible: ' + str(n_susceptible) + '\n')
    f.write('spread: ' + str(n_spread) + '\n')
    f.write('attack: ' + str(n_attack) + '\n')
    f.write('control: ' + str(n_control) + '\n')
    f.close()



import pycxsimulator
pycxsimulator.GUI().start(func=[init,draw,step])