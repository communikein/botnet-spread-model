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
spread_prob = 0.4
# Probability of a node to be chosen as attack type, once infected
attack_prob = 0.6

SUSCEPTIBLE = 0
INFECTED = 1
IMMUNE = 2

MAX_CLIENTS = 100

ROLE_NONE = 3
ROLE_ATTACK = 4
ROLE_CONTROL = 5
ROLE_CONTROL_SPREAD = 6
ROLE_SPREAD = 7

network_data = dict()


def get_data_from_network():
	global network, network_data

	for i in network.nodes():
		node = dict()
		node['state'] = network.node[i]['state']
		node['role'] = network.node[i]['role']
		node['clients'] = list(network.node[i]['clients'])
		node['parent'] = network.node[i]['parent']
		node['just_modified'] = False
		network_data[i] = node

		del network.node[i]['lat']
		del network.node[i]['lng']
		del network.node[i]['state']
		del network.node[i]['role']
		del network.node[i]['position']
		del network.node[i]['clients']
		del network.node[i]['parent']
		if 'just_modified' in network.node[i]:
			del network.node[i]['just_modified']

def init(keep_patient_zero=True):
	global network, network_data
	global n_infected, n_susceptible, n_immune
	global n_spread, n_attack, n_control, n_control_spread
	global population_size, sr_amount

	n_infected = n_susceptible = n_immune = 0
	n_attack = n_spread = n_control = n_control_spread = 0

	# Generate network
	if log_level >= 1:
		print('Loading graph...')

	network = NX.read_gpickle(network_path)
	get_data_from_network()

	population_size = len(network.nodes())
	sr_amount = int(population_size * 0.001)

	if log_level >= 1:
		print('Graph loaded.')
		print('---------------------------------------------')

	if not keep_patient_zero:
		# Remove previously selected 'patient zero'
		for i in network_data:
			network_data[i]['state'] = SUSCEPTIBLE
			network_data[i]['role'] = ROLE_NONE
			network_data[i]['just_modified'] = False
			network_data[i]['clients'] = []
			network_data[i]['parent'] = None

		# Choose random 'patient zero'
		i = random.randint(0, len(network.nodes()))
		network_data[i]['state'] = INFECTED
		network_data[i]['role'] = ROLE_CONTROL_SPREAD
		network_data[i]['just_modified'] = False
		network_data[i]['clients'] = []
		network_data[i]['parent'] = i

		if log_level >= 1:
			print('Random \'patient zero\' chosen.')
			print('Node n.' + str(i))
			print('Time zone: ' + str(network.node[i]['time_zone']))
			print('---------------------------------------------')

	n_spread = n_infected = 1
	n_susceptible = population_size - n_infected

	print_data()
	create_data_file()

def step():
	global steps
	global network_data, network_change
	global botnet_detected

	nodes_modified = dict()
	network_change = dict()

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

			# If the node is of type Spread but there is no more node ot infect it becomes of type Attack
			if is_node_spreading(network_data[i]) and not any_susceptible_neighbor(network, i):
				network_data[i]['role'] = ROLE_ATTACK

			# If the botnet has been detected, then the node might have an updated antivirus
			# that allows the node to be immune against attacks
			if can_update_antivirus(network_data[i]):
				nodes_modified[i] = increase_immune_chance(i, nodes_modified)

			# If peer to peer mode enabled
			elif peer_to_peer and is_node_immune(network_data[i]):
				# Try to update its neighbors antivirus
				for j in network.neighbors(i):
					# If the neighbor is online and not already updated
					if is_node_online(network.node[j]) and not is_node_immune(network_data[j]):
						# Update its antivirus
						nodes_modified[j] = increase_immune_chance(j, nodes_modified)
						break

			# If the node is infected, then it might infect others
			elif is_node_infected(network_data[i]):
				if log_level >= 2:
					print('Found an infected node.')

				# If the node has been infected the previous step and is of type control
				if is_node_control_spread(network_data[i]):

					# Try to infect one of its neighbors nodes and make it of type spread
					j = infect_random_neighbor_node(network, i)
					if j is not None:
						nodes_modified[j] = increase_infect_chance(j, i, nodes_modified, revert_control_spread=True)

				# If the node is has the role to spread
				if is_node_spreading(network_data[i]):
					# Get the control node to whom is connected
					parent = get_parent(i)

					# Try to spread to all its neighbors
					for j in network.neighbors(i):
						# If the neighbor is susceptible
						if is_node_online(network.node[j]) and is_node_susceptible(network_data[j]) and control_can_add_clients(parent):
							# Try to infect it
							if got_infected():
								nodes_modified[j] = increase_infect_chance(j, parent, nodes_modified)
								break
	
	update_network_status(nodes_modified)

	# Get, print and save statistics
	get_statistics()
	print_data()

	save_step_data(network_change)
	del nodes_modified

def increase_immune_chance(index, nodes_modified):
	if index in nodes_modified:
		result = nodes_modified[index]
	else:
		result = dict()

	if 'updates' not in result:
		result['updates'] = 0

	result['updates'] += 1

	return result

def increase_infect_chance(index_target, index_control_origin, nodes_modified, revert_control_spread=False):
	result = dict()
	result['attacks'] = dict()
	if index_target in nodes_modified:
		result = nodes_modified[index_target]

	if 'attacks' not in result:
		result['attacks'] = dict()

	if index_control_origin not in result['attacks']:
		result['attacks'][index_control_origin] = 1
	else:
		result['attacks'][index_control_origin] += 1

	if revert_control_spread:
		result['infected_control'] = True

	return result



def update_network_status(nodes_modified):
	global network_change

	network_change = dict()
	for node in nodes_modified.keys():
		attacks = 0
		attacks_info = dict()
		if 'attacks' in nodes_modified[node]:
			for attack_origin in nodes_modified[node]['attacks']:
				attacks += nodes_modified[node]['attacks'][attack_origin]
				attacks_info[attacks] = attack_origin

		updates = 0
		if 'updates' in nodes_modified[node]:
			updates = nodes_modified[node]['updates']

		if attacks + updates > 0:
			rnd = random.randint(1, attacks + updates)
			
			if rnd <= attacks:
				rnd = random.randint(0, attacks)

				most_attacks_origin = attacks_info[attacks_info.keys()[0]]
				for num in attacks_info:
					if rnd <= num:
						most_attacks_origin = attacks_info[num]

				update_network_data_infected(node, most_attacks_origin, nodes_modified)

			else:
				update_network_data_immune(node)

def update_network_data_infected(node, parent, nodes_modified):
	global network_data

	network_data[node]['state'] = INFECTED
	network_data[node]['parent'] = parent

	if 'infected_control' in nodes_modified[node]:
		network_data[node]['role'] = ROLE_SPREAD
		# Set the control_spread node to normal Control role
		network_data[parent]['role'] = ROLE_CONTROL

	else:
		if len(network_data[parent]['clients']) < MAX_CLIENTS - 1:
			network_data[node]['role'] = choose_role()
		else:
			network_data[node]['role'] = ROLE_CONTROL_SPREAD
			network_data[node]['clients'] = []

	network_data[parent]['clients'].append(node)

	network_change[node] = network_data[node]
	network_change[parent] = network_data[parent]

def update_network_data_immune(node):
	global network_data
	
	previous_role = network_data[node]['role']
	parent = network_data[node]['parent']
	clients = list(network_data[node]['clients'])

	network_data[node]['state'] = IMMUNE
	network_data[node]['role'] = ROLE_NONE
	network_data[node]['parent'] = None
	network_data[node]['clients'] = []

	if network_data[node]['state'] == INFECTED:

		if previous_role == ROLE_CONTROL:
			
			if clients is not None and len(clients) > 0:
				chosen = RD.choice(clients)
				clients.remove(chosen)

				network_data[chosen]['role'] = ROLE_CONTROL
				network_data[chosen]['clients'] = list(clients)

				for client in clients:
					network_data[client]['parent'] = chosen
					network_change[client] = network_data[client]

				network_data[chosen]['parent'] = parent

				print('NEW CHOSEN PARENT (CONTROL) node: ' + str(chosen))
				print(network_data[chosen])
				print('#' * 30)

				network_change[chosen] = network_data[chosen]

			# If this is not the patient zero
			if node != parent:
				if node not in network_data[parent]['clients']:
					print('NODE BECOMING IMMUNE: ' + str(node))
					print(network_data[node])
					print('#' * 30)
					print('PARENT OF NODE BECOMING IMMUNE: ' + str(parent))
					print(network_data[parent])
					print('#' * 30)			
				network_data[parent]['clients'].remove(node)
				
				network_change[parent] = network_data[parent]

	network_change[node] = network_data[node]


def get_random_online_node(network):
	online = False
	while not online:
		index = RD.randrange(0, population_size - 1)
		node = network.node[index]
		online = is_node_online(node)

	return index

def infect_random_neighbor_node(network, index):
	options = [i for i in network.neighbors(index) if is_node_susceptible(network_data[i]) and is_node_online(network.node[i])]

	node_infected = False
	while not node_infected and len(options) > 0:
		chosen = RD.choice(options)

		if got_infected():
			node_infected = True

	if node_infected:
		return chosen
	else:
		return None

def any_susceptible_neighbor(network, index):
	options = [i for i in network.neighbors(index) if network_data[i]['state'] == SUSCEPTIBLE]

	return len(options) > 0

def control_can_add_clients(index):
	if len(network_data[index]['clients']) < MAX_CLIENTS:
		return True
	else:
		return False

def get_parent(index):
	return network_data[index]['parent']



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

def is_node_control_spread(node):
	if node['role'] == ROLE_CONTROL_SPREAD:
		return True
	else:
		return False

def botnet_got_detected():
	if botnet_detected or n_immune > 0:
		#print('!!!!!!!!!!!!!!!!! BOTNET DETECTED: ' + str(botnet_detected))
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

		if network_data[node]['role'] == ROLE_ATTACK:
			multiplier = 1
		elif network_data[node]['role'] == ROLE_CONTROL:
			multiplier = 2
		elif network_data[node]['role'] == ROLE_SPREAD:
			multiplier = 5

		if rnd < botnet_detection_prob * multiplier:
			#print('!!!!!!!!!!!!!!!!!!!!!! BOTNET DETECTED: ' + str(botnet_detected))
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

def got_infected():
	rnd = RD.random()
	return rnd < infection_prob

def choose_role():
	rnd = RD.random()

	if rnd < spread_prob:
		return ROLE_SPREAD
	else:
		return ROLE_ATTACK



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
		print('N. control & spread: ' + str(n_control_spread))
		print('N. control: ' + str(n_control))
		print('')

def get_statistics():
	global network_data
	global n_infected, n_immune, n_susceptible
	global n_spread, n_attack, n_control, n_control_spread
	global simulation_over

	n_infected = n_susceptible = n_immune = 0
	n_attack = n_control = n_spread = n_control_spread = 0

	for i in network_data:
		network_data[i]['just_modified'] = False

		if network_data[i]['state'] == INFECTED:
			n_infected += 1

			if network_data[i]['role'] == ROLE_SPREAD:
				n_spread += 1
			elif network_data[i]['role'] == ROLE_ATTACK:
				n_attack += 1
			elif network_data[i]['role'] == ROLE_CONTROL:
				n_control += 1
			else:
				n_control_spread += 1

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
	line += 'infection_prob' + ','
	line += 'av_update_prob' + ','
	line += 'spread_prob' + ','
	line += 'attack_prob' + '\n'
	f.write(line)

	line = ''
	line += str(population_size) + ','
	line += str(infection_prob) + ','
	line += str(av_update_prob) + ','
	line += str(spread_prob) + ','
	line += str(attack_prob) + '\n'
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

	if '-cs' in sys.argv:
		peer_to_peer = False
		repeat = int(sys.argv[sys.argv.index('-cs') + 1])

	if '-log' in sys.argv:
		log_level = int(sys.argv[sys.argv.index('-log') + 1])		

	for x in range(repeat):
		print('Starting simulation n. ' + str(x))
		first = True
		steps = days = hours = minutes = 0
		botnet_detected = False
		simulation_over = False

		hacker_can_continue_spread = False
		network_path = '../data/graph-data.p'
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
		next_sim = '0' * (2 - len(str(latest_sim + 1))) + str(latest_sim + 1)
		dest_path += next_sim + '/'

		if not os.path.exists(dest_path):
			os.makedirs(dest_path)

		init(keep_patient_zero=True)
		while not simulation_over:
			step()