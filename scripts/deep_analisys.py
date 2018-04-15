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

SUSCEPTIBLE = 0
INFECTED = 1
IMMUNE = 2

ROLE_NONE = 3
ROLE_ATTACK = 4
ROLE_CONTROL = 5
ROLE_CONTROL_SPREAD = 6
ROLE_SPREAD = 7

results_path_base = '../data/results/'

def load_network_start():
	graph = NX.read_gpickle('../data/graph-data-hybrid.p')
	return graph

def load_network_history(day, step):
	data = dict()

	history_path = results_path_base + sim_num + '/'
	history_step_file = history_path + '0' * (2 - len(str(day))) + str(day) + '/'
	history_step_file += 'botnet-evolution-' + '0' * (4 - len(str(step))) + str(step) + '.p'

	#print(history_step_file)

	try:
		with open(history_step_file, 'rb') as origin:
			data = pickle.load(origin)
	except:
		print('ERROR NOT FOUND - ' + history_step_file)
		return None

	return data


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

def is_node_online(node):
	local_time = hour + node['time_zone']

	if local_time >= 8 and local_time <= 22:
		return True
	else:
		return False

def get_node_role(node):
	if node['role'] == ROLE_SPREAD:
		return 'spread'

	elif node['role'] == ROLE_CONTROL:
		return 'CONTROL'

	elif node['role'] == ROLE_ATTACK:
		return 'attack'

	elif node['role'] == ROLE_CONTROL_SPREAD:
		return 'CONTROL_SPREAD'

	else:
		return 'none'



def init():
	global step
	global network
	global day, hour

	day = hour = step = 0

	network = load_network_start()
	history = load_network_history(0, 0)

def stepp():
	global network
	global step, hour, day

	step += 1
	day = (step * 15) / (24 * 60)

	if step < 110:
		print('')
		print('STEP: ' + str(step) + ' - ' + str(len([x for x in network.nodes() if is_node_infected(network.node[x])])))
		history = load_network_history(day, step)

		for i in history:
			network.node[i]['state'] = history[i]['state']
			network.node[i]['role'] = history[i]['role']

		tot = 0
		for i in network.nodes():
			cont = 0

			if is_node_infected(network.node[i]):
				message = 'Node ' + str(i) + '('
				if is_node_online(network.node[i]):
					message += 'ONLINE/'
				else:
					message += 'offline/'
				message += get_node_role(network.node[i]) + ') -> '

				neighbors = network[i].keys()

				for nei in neighbors:
					if is_node_susceptible(network.node[nei]):
						cont += 1
				tot += cont

				print(message + str(len(neighbors)) + ' (' + str(cont) + ')')

		print(str(tot) + ' susceptible neighbor nodes.')
	

def get_simulations(params):
	global results_path_base, sim_num

	if '-central-server' in params:
		results_path_base += 'central-server'
		sim_num = params[params.index('-central-server') + 1]
	elif '-p2p' in params:
		results_path_base += 'peer-to-peer'
		sim_num = params[params.index('-p2p') + 1]
	else:
		print('ERROR - choose peer-to-peer or central-server mode.')
		return

	#if '-hybrid' in params:
	results_path_base += '-hybrid'
	results_path_base += '/'

	if len(sim_num) < 2:
		sim_num = '0' + sim_num

	simulations = [results_path_base + sim_num]

	print('Showing data from the following simulations files:')
	for simul in simulations:
		print(simul)

	return simulations


if __name__ == '__main__':
	global simulations
	global final_steps
	
	simulations = get_simulations(sys.argv)
	init()

	while True:
		stepp()