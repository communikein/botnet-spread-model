# *** Botnet spread in computer network ***
#
# Project by Maracani Elia
# Matricola: 763734
import pycxsimulator
import matplotlib
matplotlib.use('TkAgg')

import pylab as PL
import random as RD
import scipy as SP
import networkx as NX
import random
import itertools
import copy

import os
import simplejson as json
import pickle
import time

RD.seed()


log_level = 1

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


def init_simulations(network_path='../data/graph-data-small.p', keep_patient_zero=True):
    global population_size, initial_infection_prob, sr_amount
    global network
    global infectedData, immuneData, steps

    steps = 0
    infectedData = []
    immuneData = []

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

    # Remove unused data
    for i in network.nodes():
        del network.node[i]['lat']
        del network.node[i]['lng']
        del network.node[i]['position']

        if not keep_patient_zero:
            # Remove previously selected 'patient zero'
            network.node[i]['state'] = SUSCEPTIBLE
            network.node[i]['role'] = ROLE_NONE
            network.node[i]['just_modified'] = False

        if log_level >= 2 and network.node[i]['state'] == INFECTED:
            print('Found infected!!')
            print(network.node[i])

    if not keep_patient_zero:
        # Choose random 'patient zero'
        i = random.randint(0, len(network.nodes()))
        network.node[i]['state'] = INFECTED
        network.node[i]['role'] = ROLE_SPREAD
        network.node[i]['just_modified'] = True

        if log_level >= 1:
            print('Random \'patient zero\' chosen.')
            print('Node n.' + str(i))
            print('Time zone: ' + str(network.node[i]['time_zone']))
            print('---------------------------------------------')

    return network

def pick_patient_zero(network):
    # Remove previously selected 'patient zero'
    for i in network.nodes():
        network.node[i]['state'] = SUSCEPTIBLE
        network.node[i]['role'] = ROLE_NONE
        network.node[i]['just_modified'] = False

    # Choose random 'patient zero'
    i = random.randint(0, len(network.nodes()))
    network.node[i]['state'] = INFECTED
    network.node[i]['role'] = ROLE_SPREAD
    network.node[i]['just_modified'] = True

    return network

def change_patient_zero(network):
    network = pick_patient_zero(network)
    NX.write_gpickle(graph, '../data/graph-data-complete.p')

    return network



def simulate(network, simulation_number):
	if simulation_number % 2 == 0:
		simulate_peer_to_peer(network, simulation_number)
	else:	
		simulate_central_server(network, simulation_number)

def simulate_central_server(network, simulation_number):
	dest_path = create_data_file(network, peer_to_peer=False)
	print(str(simulation_number) + ' - Central server simulation initiated...')

	steps = 0
	botnet_detected = False
	n_infected = 1
	while n_infected > 0:
		print(str(simulation_number) + ' - ' + str(n_infected) + ' left to fix.')

		network, botnet_detected = step(network=network, 
			steps=steps, botnet_detected=botnet_detected,
			peer_to_peer=False, dest_path=dest_path)

		# Get, print and save statistics
		n_infected, n_immune, n_susceptible, n_spread, n_attack, n_control = get_statistics(network)
		print_data(n_infected, n_immune, n_susceptible, steps)

		save_step_data(network, steps, 
			n_infected, n_immune, n_susceptible, n_spread, n_attack, n_control,
			dest_path)

		steps += 1

def simulate_peer_to_peer(network, simulation_number):
	dest_path = create_data_file(network, peer_to_peer=True)
	print(str(simulation_number) + ' - Peer-2-peer simulation initiated...')

	steps = 0
	botnet_detected = False
	n_infected = 1
	while n_infected > 0:
		print(str(simulation_number) + ' - ' + str(n_infected) + ' left to fix.')

		network, botnet_detected = step(network=network, 
			steps=steps, botnet_detected=botnet_detected,
			peer_to_peer=True, dest_path=dest_path)

		# Get, print and save statistics
		n_infected, n_immune, n_susceptible, n_spread, n_attack, n_control = get_statistics(network)
		print_data(n_infected, n_immune, n_susceptible, steps)

		save_step_data(network, steps, 
			n_infected, n_immune, n_susceptible, n_spread, n_attack, n_control,
			dest_path)

		steps += 1

def do_step():
	global network, steps
	global infectedData, immuneData

	days, hours, minutes = save_time(steps)

	botnet_detected = botnet_got_detected(network, hours)
	step(network, steps, botnet_detected, False, '../data/results/central-server/1/')

	n_infected, n_immune, n_susceptible, n_spread, n_attack, n_control = get_statistics(network)
	infectedData.append(n_infected)
	immuneData.append(n_immune)

	steps += 1

def step(network, steps, botnet_detected, peer_to_peer, dest_path):
    days, hours, minutes = save_time(steps)

    # Check if the botnet has been detected
    botnet_detected = botnet_got_detected(network, hours)

    if log_level >= 2 and botnet_detected:
        print('Botnet detected!')

    next_network = network.copy()

    # For each node in the network
    for i in network:
        
        # If the node is up
        if is_node_online(network.node[i], hours):
            
            # If the botnet has been detected, then the node might have an updated antivirus
            # that allows the node to be immune against attacks
            if can_update_antivirus(network.node[i]):
                next_network.node[i]['state'] = IMMUNE
                next_network.node[i]['role'] = ROLE_NONE
                next_network.node[i]['just_modified'] = True

            # If peer to peer mode enabled
            elif is_node_immune(network.node[i]) and peer_to_peer:
                # Try to update its neighbors antivirus
                for j in network.neighbors(i):
                    # If the neighbor is online and not already updated
                    if is_node_online(network.node[j], hours) and not is_node_immune(network.node[j]):
                        # Update its antivirus
                        next_network.node[j]['state'] = IMMUNE
                        next_network.node[j]['role'] = ROLE_NONE
                        next_network.node[j]['just_modified'] = True

                        break

            # If the node is susceptible, then it might become source of infection
            elif is_node_susceptible(network.node[i]):

                # Try to infect it
                if got_infected_by_hacker(network.node[i]):
                    next_network.node[i]['state'] = INFECTED
                    next_network.node[i]['role'] = choose_role()
                    next_network.node[i]['just_modified'] = True

            # If the node is infected, then it might infect others
            elif is_node_infected(network.node[i]):
                if log_level >= 2:
                    print('Found an infected node.')

                # If the node is has the role to spread
                if is_node_spreading(network.node[i]):
                    # Try to spread to all its neighbors
                    for j in network.neighbors(i):
                        # If the neighbor is susceptible
                        if is_node_online(network.node[j], hours) and is_node_susceptible(network.node[j]):
                            # Try to infect it
                            if got_infected_by_node(network.node[j]):
                                next_network.node[j]['state'] = INFECTED
                                next_network.node[j]['role'] = choose_role()
                                next_network.node[j]['just_modified'] = True

                                break

    del network
    network = next_network.copy()

    return network, botnet_detected

def draw():
    plot_title = 'Step ' + str(steps)

    PL.figure(1)
    PL.cla()
    PL.plot(infectedData, 'r')
    PL.plot(immuneData, 'g')
    PL.title(plot_title)
    PL.show()




def get_random_online_node(network, hours):
    online = False
    while not online:
        index = RD.randrange(0, population_size - 1)
        node = network.node[index]
        online = is_node_online(node, hours)

    return node

def is_node_online(node, hours):
    local_time = hours + node['time_zone']

    if local_time >= 8 and local_time <= 22:
        return True
    else:
        return False

def is_node_infected(node):
    if node['state'] == INFECTED and not node['just_modified']:
        return True
    else:
        return False

def is_node_susceptible(node):
    if node['state'] == SUSCEPTIBLE:
        return True
    else:
        return False

def is_node_immune(node):
    if node['state'] == IMMUNE:
        return True
    else:
        return False

def is_node_spreading(node):
    if is_node_infected(node) and node['role'] == ROLE_SPREAD:
        return True
    else:
        return False

def botnet_got_detected(network, hours):
    if botnet_detected:
        return True

    for i in range(1, sr_amount):
        # Choose a random online node
        node = get_random_online_node(network, hours)

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

def can_update_antivirus(node):
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
    days = (steps * time_multiplier) / (24 * 60)

    time = (steps * time_multiplier) - (days * 24 * 60)
    hours = int(time / 60)
    minutes = int(time - hours * 60)

    return days, hours, minutes

def print_time(days, hours, minutes):
    str_hours = '0' + str(hours)
    if (hours >= 10):
        str_hours = str(hours)

    str_minutes = '0' + str(minutes)
    if (minutes >= 10):
        str_minutes = str(minutes)

    message = 'Day: ' + str(days) + ', Time: ' + str(str_hours) + ":" + str(str_minutes)
    return message

def print_data(n_infected, n_immune, n_susceptible, steps):
    if log_level >= 2:
    	print(time.strftime('%H:%M:%S %p') + ' - ' +str(steps))
        print(print_time())
        print('N. infected: ' + str(n_infected))
        print('N. immune: ' + str(n_immune))
        print('N. susceptible: ' + str(n_susceptible))
        print('')

def get_statistics(network):
    n_infected = n_susceptible = n_immune = 0
    n_attack = n_control = n_spread = 0

    for i in network.nodes():
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

    return n_infected, n_immune, n_susceptible, n_spread, n_attack, n_control

def create_data_file(network_status, peer_to_peer):
    network_path = '../data/graph-data-complete.p'
    results_path = '../data/results/' 

    if peer_to_peer:
    	dest_path = results_path + 'peer-to-peer/'
    else:
    	dest_path = results_path + 'central-server/'

    simulations = [int(sim) for sim in os.listdir(results_path) if represents_int(sim)]
    if len(simulations) == 0:
        latest_sim = 0
    else:
        latest_sim = max(simulations)
    latest_sim_path = str(latest_sim + 1) + '/'

    dest_path += latest_sim_path

    if not os.path.exists(dest_path):
    	os.makedirs(dest_path)
    
    #
    f = open(dest_path + 'settings.csv', 'w')

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
    f = open(dest_path + 'results.csv', 'w')

    line = ''
    line += 'infected' + ','
    line += 'immune' + ','
    line += 'susceptible' + ','
    line += 'spread' + ','
    line += 'attack' + ','
    line += 'control' + '\n'
    f.write(line)

    line = ''
    line += '1,'
    line += '0,'
    line += str(population_size - 1) + ','
    line += '1,'
    line += '0,'
    line += '0\n'
    f.write(line)
    f.close()

    destination_path = dest_path + '0/botnet-evolution-0000'
    os.makedirs(dest_path + '0/')

    with open(destination_path + '.p', 'wb') as dest:
        pickle.dump(network_status, dest, protocol=pickle.HIGHEST_PROTOCOL)

    return dest_path



def save_step_data(network_status, steps, 
    n_infected, n_immune, n_susceptible, n_spread, n_attack, n_control, 
    dest_path):
    #infected,immune,susceptible,spread,attack,control
    f = open(dest_path + 'results.csv', 'a')

    line = ''
    line += str(n_infected) + ','
    line += str(n_immune) + ','
    line += str(n_susceptible) + ','
    line += str(n_spread) + ','
    line += str(n_attack) + ','
    line += str(n_control) + '\n'
    f.write(line)
    f.close()

    if not os.path.exists(dest_path + str(days) + '/'):
        os.makedirs(dest_path + str(days) + '/')

    step_number = '0' * (4 - len(str(steps))) + str(steps)
    destination_path = dest_path + str(days) + '/botnet-evolution-' + step_number
    with open(destination_path + '.p', 'wb') as dest:
        pickle.dump(network_status, dest, protocol=pickle.HIGHEST_PROTOCOL)

def represents_int(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

###############################
###############################

if __name__ == '__main__':
    network_path = '../data/graph-data-complete.p'
    network = init_simulations(network_path)

    '''
    if log_level >= 1:
        print('Loading network status')

    network_status = dict()
    for i in network.nodes():
        status = dict()
        status['state'] = network.node[i]['state']
        status['role'] = network.node[i]['role']
        status['just_modified'] = False
        network_status[i] = status
    simulate(network_status, 0)
    '''


    interface = pycxsimulator.GUI()
    interface.start(func=[init_simulations,draw,do_step])

    '''
    import multiprocessing as mp

    pool = mp.Pool(1)

    tasks = []
    for process in range(2):
        if log_level >= 1:
            print(str(process + 1) + ' - Loading network status')

        network_status = dict()
        for i in network.nodes():
            status = dict()
            status['state'] = network.node[i]['state']
            status['role'] = network.node[i]['role']
            status['just_modified'] = False
            network_status[i] = status
        tasks.append( (network, process, ) )

    if log_level >= 1:
        print('Processes ready to start.')
    results = [pool.apply_async(simulate, task) for task in tasks]

    [res.get() for res in results]
    '''