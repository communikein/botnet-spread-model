# *** Botnet spread in computer network ***
#
# Project by Maracani Elia
# Matricola: 763734

import pylab as PL
import random as RD
import scipy as SP
import networkx as NX
import random
import itertools

import os
import simplejson as json
import time

RD.seed()


log_level = 0

# Every step of the simulator is equals to 'time_multiplier' minutes
time_multiplier = 15

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


global first
global steps, days, hours, minutes
global botnet_detected

first = True
steps = days = hours = minutes = 0
botnet_detected = False


def init(keep_patient_zero=True):
    global network_status
    global network, next_network
    global n_infected, n_susceptible, n_immune
    global n_spread, n_attack, n_control
    global infectedData, susceptibleData, immuneData
    global spreadData, attackData, controlData
    global population_size, initial_infection_prob, sr_amount

    network_status = dict()
    n_infected = n_susceptible = n_immune = 0
    n_attack = n_spread = n_control = 0
    
    # Generate network
    if log_level >= 1:
        print('Loading graph...')

    network = NX.read_gpickle(network_path)
    population_size = len(network.nodes())
    initial_infection_prob = 0.005 / population_size
    sr_amount = int(population_size * 0.005)
    
    if log_level >= 1:
        print('Graph loaded.')
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

        if log_level >= 1:
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

    create_data_file(network)
    


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

    if log_level >= 2 and botnet_detected:
        print('Botnet detected!')

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
                next_network.node[i]['position'] = network.node[i]['position']

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
                    next_network.node[i]['position'] = network.node[i]['position']

            # If the node is infected, then it might infect others
            elif is_node_infected(network.node[i]):
                if log_level >= 2:
                    print('Found an infected node.')

                # The node has not been detected, thus remains infected
                next_network.node[i]['state'] = network.node[i]['state']
                next_network.node[i]['role'] = network.node[i]['role']
                next_network.node[i]['just_infected'] = network.node[i]['just_infected']
                next_network.node[i]['lat'] = network.node[i]['lat']
                next_network.node[i]['lng'] = network.node[i]['lng']
                next_network.node[i]['time_zone'] = network.node[i]['time_zone']
                next_network.node[i]['position'] = network.node[i]['position']

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
                                next_network.node[i]['position'] = network.node[i]['position']
                                break
    
    # Get, print and save statistics
    get_statistics(next_network)
    print_data()
    save_step_data(steps, next_network)

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
    print(time.strftime('%H:%M:%S %p') + ' - ' +str(steps))
    
    if log_level >= 1:
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

def create_data_file(network):
    global network_history
    #
    f = open(results_dest_path + 'settings.csv', 'w')

    line = ''
    line += 'population_size' + ','
    line += 'link_prob_base' + ','
    line += 'initial_infection_prob' + ','
    line += 'infection_prob' + ','
    line += 'av_update_prob' + ','
    line += 'spread_prob' + ','
    line += 'attack_prob' + ','
    line += 'control_prob' + '\n'
    f.write(line)

    line = ''
    line += str(population_size) + ','
    line += str(link_prob_base) + ','
    line += str(initial_infection_prob) + ','
    line += str(infection_prob) + ','
    line += str(av_update_prob) + ','
    line += str(spread_prob) + ','
    line += str(attack_prob) + ','
    line += str(control_prob) + '\n'
    f.write(line)
    f.close()

    #
    f = open(results_dest_path + 'results.csv', 'w')

    line = ''
    line += 'infected' + ','
    line += 'immune' + ','
    line += 'susceptible' + ','
    line += 'spread' + ','
    line += 'attack' + ','
    line += 'control' + '\n'
    f.write(line)

    line = ''
    line += str(n_infected) + ','
    line += str(n_immune) + ','
    line += str(n_susceptible) + ','
    line += str(n_spread) + ','
    line += str(n_attack) + ','
    line += str(n_control) + '\n'
    f.write(line)
    f.close()

    network_history = []
    network_status = dict()
    for i in network.nodes():
        data = dict()
        data['state'] = network.node[i]['state']
        data['role'] = network.node[i]['role']
        network_status[i] = data
    network_history.append(network_status)

    with open(results_dest_path + 'botnet-evolution-0.p', 'wb') as dest:
        pickle.dump(network_history, dest, protocol=pickle.HIGHEST_PROTOCOL)

    with open(results_dest_path + 'botnet-evolution-0.json', 'w') as dest:
        dest.write(json.dumps(network_history))

def save_step_data(network, step):
    #infected,immune,susceptible,spread,attack,control
    f = open(results_dest_path + 'results.csv', 'a')

    line = ''
    line += str(n_infected) + ','
    line += str(n_immune) + ','
    line += str(n_susceptible) + ','
    line += str(n_spread) + ','
    line += str(n_attack) + ','
    line += str(n_control) + '\n'
    f.write(line)
    f.close()

    network_status = dict()
    for i in network.nodes():
        data = dict()
        data['state'] = network.node[i]['state']
        data['role'] = network.node[i]['role']
        network_status[i] = data
    network_history.append(network_status)

    with open(results_dest_path + 'botnet-evolution-' + str(step) + '.json', 'w') as dest:
        dest.write(json.dumps(network_history))

    with open(results_dest_path + 'botnet-evolution-' + str(step) + '.p', 'wb') as dest:
        pickle.dump(network_history, dest, protocol=pickle.HIGHEST_PROTOCOL)

def represents_int(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

###############################
###############################

network_path = '../data/graph-data-complete.p'

simulations = [int(sim) for sim in os.listdir('../data/results/') if represents_int(sim)]
latest_sim = max(simulations)

results_dest_path = '../data/results/' + str(latest_sim + 1) + "/"
os.makedirs(results_dest_path)


init(keep_patient_zero=False)
while True:
    step()