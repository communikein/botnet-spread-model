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
import copy

import sys
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


def get_data_from_network():
	global network
	data = dict()

	for i in network.nodes():
		node = dict()
		node['state'] = network.node[i]['state']
		node['role'] = network.node[i]['role']
		node['just_modified'] = False
		data[i] = node

		del network.node[i]['lat']
		del network.node[i]['lng']
		del network.node[i]['state']
		del network.node[i]['role']
		del network.node[i]['position']
		if 'just_modified' in network.node[i]:
			del network.node[i]['just_modified']

	return data

def init(keep_patient_zero=True):
    global network, network_data
    global n_infected, n_susceptible, n_immune
    global n_spread, n_attack, n_control
    global population_size, initial_infection_prob, sr_amount

    n_infected = n_susceptible = n_immune = 0
    n_attack = n_spread = n_control = 0
    
    # Generate network
    if log_level >= 1:
        print('Loading graph...')

    network = NX.read_gpickle(network_path)
    network_data = get_data_from_network()

    population_size = len(network.nodes())
    initial_infection_prob = 0.005 / population_size
    sr_amount = int(population_size * 0.005)
    
    if log_level >= 1:
        print('Graph loaded.')
        print('---------------------------------------------')

    if not keep_patient_zero:
        # Remove previously selected 'patient zero'
        for i in network_data:
            network_data[i]['state'] = SUSCEPTIBLE
            network_data[i]['role'] = ROLE_NONE
            network_data[i]['just_modified'] = False

        # Choose random 'patient zero'
        i = random.randint(0, len(network.nodes()))
        network_data[i]['state'] = INFECTED
        network_data[i]['role'] = ROLE_SPREAD
        network_data[i]['just_modified'] = True

        if log_level >= 1:
            print('Random \'patient zero\' chosen.')
            print('Node n.' + str(i))
            print('Time zone: ' + str(network.node[i]['time_zone']))
            print('---------------------------------------------')

    n_spread = n_infected = 1
    n_susceptible = population_size - n_infected

    print_data()
    create_data_file()

def step_v1():
    global steps
    global network_data
    global botnet_detected

    nodes_modified = dict()

    steps += 1
    save_time()

    # Check if the botnet has been detected
    botnet_detected = botnet_got_detected()

    if log_level >= 2 and botnet_detected:
        print('Botnet detected!')

    # For each node in the network
    for i in network.nodes():
        
        # If the node is up
        if is_node_online(network.node[i]):
            
            # If the botnet has been detected, then the node might have an updated antivirus
            # that allows the node to be immune against attacks
            if can_update_antivirus(network_data[i]):
                network_data[i]['state'] = IMMUNE
                network_data[i]['role'] = ROLE_NONE
                nodes_modified[i] = network_data[i]

                network_data[i]['just_modified'] = True

            # If peer to peer mode enabled
            elif peer_to_peer and is_node_immune(network_data[i]):
                # Try to update its neighbors antivirus
                for j in network.neighbors(i):
                    # If the neighbor is online and not already updated
                    if is_node_online(network.node[j]) and not is_node_immune(network_data[j]):
                        # Update its antivirus
                        network_data[j]['state'] = IMMUNE
                        network_data[j]['role'] = ROLE_NONE
                        nodes_modified[i] = network_data[i]

                        network_data[j]['just_modified'] = True
                        break

            # If the node is susceptible, then it might become source of infection
            elif is_node_susceptible(network_data[i]):

                # Try to infect it
                if got_infected_by_hacker(network_data[i]):
                    network_data[i]['state'] = INFECTED
                    network_data[i]['role'] = choose_role()
                    nodes_modified[i] = network_data[i]

                    network_data[i]['just_modified'] = True

            # If the node is infected, then it might infect others
            elif is_node_infected(network_data[i]):
                if log_level >= 2:
                    print('Found an infected node.')

                # If the node is has the role to spread
                if is_node_spreading(network_data[i]):
                    # Try to spread to all its neighbors
                    for j in network.neighbors(i):
                        # If the neighbor is susceptible
                        if is_node_online(network.node[j]) and is_node_susceptible(network_data[j]):
                            # Try to infect it
                            if got_infected_by_node(network_data[i]):
                                network_data[j]['state'] = INFECTED
                                network_data[j]['role'] = choose_role()
                                nodes_modified[i] = network_data[i]

                                network_data[j]['just_modified'] = True
                                break
    
    # Get, print and save statistics
    get_statistics()
    print_data()

    save_step_data(nodes_modified)
    del nodes_modified

def step_v2():
    global steps
    global network_data
    global botnet_detected

    nodes_modified = dict()

    steps += 1
    save_time()

    # Check if the botnet has been detected
    botnet_detected = botnet_got_detected()

    if log_level >= 2 and botnet_detected:
        print('Botnet detected!')

    # For each node in the network
    for i in network.nodes():
        
        # If the node is up
        if is_node_online(network.node[i]):
            # If the botnet has been detected, then the node might have an updated antivirus
            # that allows the node to be immune against attacks
            if can_update_antivirus(network_data[i]):
                if i not in nodes_modified:
                    nodes_modified[i] = dict()
                if 'immune' not in nodes_modified[i]:
                    nodes_modified[i]['immune'] = 1
                else:
                    nodes_modified[i]['immune'] += 1

            # If peer to peer mode enabled
            elif peer_to_peer and is_node_immune(network_data[i]):
                # Try to update its neighbors antivirus
                for j in network.neighbors(i):
                    # If the neighbor is online and not already updated
                    if is_node_online(network.node[j]) and not is_node_immune(network_data[j]):
                        # Update its antivirus
                        if j not in nodes_modified:
                            nodes_modified[j] = dict()
                        if 'immune' not in nodes_modified[j]:
                            nodes_modified[j]['immune'] = 1
                        else:
                            nodes_modified[j]['immune'] += 1
                        break

            # If the node is susceptible, then it might become source of infection
            elif hacker_can_continue_spread and is_node_susceptible(network_data[i]):

                # Try to infect it
                if got_infected_by_hacker(network_data[i]):
                    if i not in nodes_modified:
                        nodes_modified[i] = dict()
                    if 'infected' not in nodes_modified[i]:
                        nodes_modified[i]['infected'] = 1
                    else:
                        nodes_modified[i]['infected'] += 1

            # If the node is infected, then it might infect others
            elif is_node_infected(network_data[i]):
                if log_level >= 2:
                    print('Found an infected node.')

                # If the node is has the role to spread
                if is_node_spreading(network_data[i]):
                    # Try to spread to all its neighbors
                    for j in network.neighbors(i):
                        # If the neighbor is susceptible
                        if is_node_online(network.node[j]) and is_node_susceptible(network_data[j]):
                            # Try to infect it
                            if got_infected_by_node(network_data[j]):
                                if j not in nodes_modified:
                                    nodes_modified[j] = dict()
                                if 'infected' not in nodes_modified[j]:
                                    nodes_modified[j]['infected'] = 1
                                else:
                                    nodes_modified[j]['infected'] += 1
                                break
    
    network_data, network_change = update_network_status(nodes_modified)
    
    # Get, print and save statistics
    get_statistics()
    print_data()

    save_step_data(network_change)
    del nodes_modified

def update_network_status(nodes_modified):
	network_change = dict()

	for i in nodes_modified.keys():
		n_infections = 0
		if 'infected' in nodes_modified[i]:
			n_infections = nodes_modified[i]['infected']

		n_immunizations = 0
		if 'immune' in nodes_modified[i]:
			n_immunizations = nodes_modified[i]['immune']

		if n_infections > n_immunizations:
			network_data[i]['state'] = INFECTED
			network_data[i]['role'] = choose_role()
		elif n_immunizations > n_infections:
			network_data[i]['state'] = IMMUNE
			network_data[i]['role'] = ROLE_NONE
		else:
			rnd = RD.random()
			if rnd <= 0.5:
				network_data[i]['state'] = IMMUNE
				network_data[i]['role'] = ROLE_NONE
			else:
				network_data[i]['state'] = INFECTED
				network_data[i]['role'] = choose_role()

		network_change[i] = network_data[i]

	return network_data, network_change



def get_random_online_node(network):
    online = False
    while not online:
        index = RD.randrange(0, population_size - 1)
        node = network.node[index]
        online = is_node_online(node)

    return index

def is_node_online(node):
    local_time = hours + node['time_zone']

    if local_time >= 8 and local_time <= 22:
        return True
    else:
        return False

def is_node_infected(node):
    if node['state'] == INFECTED:
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
    if node['role'] == ROLE_SPREAD:
        return True
    else:
        return False

def botnet_got_detected():
    if botnet_detected or n_immune > 0:
        return True

    for i in range(1, sr_amount):
        # Choose a random online node
        node = get_random_online_node(network)

        # If the node is not infected, than the SR surely can't detect the botnet
        if network_data[node]['state'] != INFECTED:
            continue

        # If the node is infected, it's chances to be detected depends on the amount
        # of traffic it generates, hance it depends on its role.
        rnd = RD.random()
        multiplier = 1
        threshold = botnet_detection_prob

        if network_data[node]['role'] == ROLE_ATTACK:
            multiplier = 1
        elif network_data[node]['role'] == ROLE_CONTROL:
            multiplier = 2
        elif network_data[node]['role'] == ROLE_SPREAD:
            multiplier = 5

        if rnd < threshold * multiplier:
            return True

    return False

def can_update_antivirus(node):
    # If the botnet has not been detected yet, there is no update available
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

def get_statistics():
    global network_data
    global n_infected, n_immune, n_susceptible
    global n_spread, n_attack, n_control
    global simulation_over

    n_infected = n_susceptible = n_immune = 0
    n_attack = n_control = n_spread = 0

    for i in network_data:
    	network_data[i]['just_modified'] = False

        if network_data[i]['state'] == INFECTED:
            n_infected += 1

            if network_data[i]['role'] == ROLE_SPREAD:
                n_spread += 1
            elif network_data[i]['role'] == ROLE_ATTACK:
                n_attack += 1
            else:
                n_control += 1

        elif network_data[i]['state'] == IMMUNE:
            n_immune += 1

        elif network_data[i]['state'] == SUSCEPTIBLE:
            n_susceptible += 1

    if steps > 100 and n_infected == 0:
    	simulation_over = True

def create_data_file():
    global network_history
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
    f.write('infected,immune,susceptible,spread,attack,control\n')
    f.write('1,0,' + str(population_size - 1) + ',1,0,0\n')
    f.close()

    if not os.path.exists(dest_path + '00/'):
    	os.makedirs(dest_path + '00/')

    with open(dest_path + '00/botnet-evolution-0000.p', 'wb') as dest:
        pickle.dump(network_data, dest, protocol=pickle.HIGHEST_PROTOCOL)

def save_step_data(network_status):
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

    day_folder = dest_path + str(days) + '/'
    if len(str(days)) == 1:
    	day_folder = dest_path + '0' + str(days) + '/'

    if not os.path.exists(day_folder):
        os.makedirs(day_folder)

    step_number = '0' * (4 - len(str(steps))) + str(steps)
    destination_path = day_folder + 'botnet-evolution-' + step_number
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
	global first
	global steps, days, hours, minutes
	global botnet_detected, simulation_over
	global peer_to_peer, hacker_can_continue_spread
	global network_path, results_path, dest_path
	global simulations

	if '-p2p' in sys.argv:
		peer_to_peer = True
		repeat = int(sys.argv[sys.argv.index('-p2p') + 1])

	if '-central-server' in sys.argv:
		peer_to_peer = False
		repeat = int(sys.argv[sys.argv.index('-central-server') + 1])

	if '-log' in sys.argv:
		log_level = int(sys.argv[sys.argv.index('-log') + 1])		

	for x in range(repeat):
		print('Starting simulation n. ' + str(x))
		first = True
		steps = days = hours = minutes = 0
		botnet_detected = False
		simulation_over = False

		hacker_can_continue_spread = False
		network_path = '../data/graph-data-complete.p'
		results_path = '../data/results/' 

		if peer_to_peer:
			dest_path = results_path + 'peer-to-peer/'
		else:
			dest_path = results_path + 'central-server/'

		simulations = [int(sim) for sim in os.listdir(dest_path) if represents_int(sim)]
		if len(simulations) == 0:
			latest_sim = 0
		else:
			latest_sim = max(simulations)
		latest_sim_path = str(latest_sim + 1) + '/'

		dest_path += latest_sim_path

		if not os.path.exists(dest_path):
			os.makedirs(dest_path)

		init(keep_patient_zero=True)
		while not simulation_over:
			step_v2()