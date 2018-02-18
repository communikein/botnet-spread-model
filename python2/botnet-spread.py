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
# Number of nodes in the network
population_size = 5000
# Base probability for link between two random nodes
link_prob_base = 0.1

# Probability to be infected without having an infected node in my neighbors
initial_infection_prob = 0.005 / population_size
# Probability of infections having an infected node in my neighbors
infection_prob = 0.01

# Number of Security Reserachers looking for threats at the same time
# Only take the integer digits, leave out the decimal ones
sr_amount = int(population_size * 0.005)
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



def init():
    global first
    global time, day, hours, minutes
    global network, next_network, positions
    global n_infected, n_susceptible, n_immune
    global n_spread, n_attack, n_control
    global infectedData, susceptibleData, immuneData
    global spreadData, attackData, controlData
    global botnet_detected

    first = True
    time = 0
    day = 0
    hours = 0
    minutes = 0
    n_infected = n_susceptible = n_immune = 0
    n_attack = n_spread = n_control = 0
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
    i = random.randint(0, 1000)
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
    PL.title(get_time())
    PL.show()

    PL.figure(2)
    PL.cla()
    PL.plot(infectedData, 'r')
    PL.plot(immuneData, 'g')
    PL.title('Botnet propagation - step ' + str(day * 24 * 4 + hours * 4 + minutes // 15))
    

def step():
    global time, day, hours, minutes
    global network, next_network
    global n_infected, n_susceptible, n_immune
    global n_attack, n_control, n_spread
    global botnet_detected

    time += 1
    n_infected = n_susceptible = n_immune = 0
    n_attack = n_control = n_spread = 0
    save_time()

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
    global hours
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



def save_time():
    global day, time, hours, minutes
    time_tmp = time * time_multiplier

    if time_tmp >= 24 * 60:
        time = time_tmp - 24 * 60
        day = day + 1

    hours = time_tmp // 60
    minutes = time_tmp - hours * 60

def get_time():
    global day, hours, minutes
    return 'Day: ' + str(day) + ', Time: ' + str(hours) + ":" + str(minutes)

def print_time():
    time = get_time()
    print(time)

def print_data():
    print_time()
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

    #print('lat: ' + str(latitude) + ', lng: ' + str(longitude))

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



import pycxsimulator
pycxsimulator.GUI().start(func=[init,draw,step])