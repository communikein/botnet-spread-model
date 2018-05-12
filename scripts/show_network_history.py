import matplotlib
matplotlib.use('TkAgg')
import matplotlib.image as mpimg

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

SUSCEPTIBLE = 0
INFECTED = 1
IMMUNE = 2

world_image_path = '.\\world.jpg'
results_path_base = '../data/results/'

def load_network_start():
	graph = NX.read_gpickle('../data/graph-data-hybrid.p')
	return graph

def load_network_history(day, step):
	data = dict()

	history_path = results_path_base + sim_num + '/'
	history_step_file = history_path + '0' * (2 - len(str(day))) + str(day) + '/'
	history_step_file += 'botnet-evolution-' + '0' * (4 - len(str(step))) + str(step) + '.p'

	print(history_step_file)

	try:
		with open(history_step_file, 'rb') as origin:
			data = pickle.load(origin)
	except:
		print('ERROR NOT FOUND')
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
	if len(simulations) > 0:
		nodes_color = [get_node_color(network.node[i]) for i in network.nodes()]
	else:
		nodes_color = [get_node_color(network.node[i]) for i in network.nodes()]

	return nodes_color

def get_node_color(node):
	# Needed to show online/offline node when we 
	# don't load the history of the simulation
	if len(simulations) < 0:
		if is_node_online(node):
			return '#0000cc'
		else:
			return '#000050'
	# If we have the history of the simulation,
	# use it to pick the node's color
	else:
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


def init():
	global step
	global network
	global background_image
	global day, hour

	day = hour = step = 0

	background_image = mpimg.imread(world_image_path)
	network = load_network_start()
	if len(simulations) > 0:
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

	if len(simulations) > 0:
		history = load_network_history(day, step)

		for i in history:
			network.node[i]['state'] = history[i]['state']
			network.node[i]['role'] = history[i]['role']
	

def get_simulations(params):
	global results_path_base, sim_num

	if '-cs' in params:
		results_path_base += 'central-server'
		sim_num = params[params.index('-cs') + 1]
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
	
	if len(sys.argv) > 1:
		simulations = get_simulations(sys.argv)
	else:
		simulations = []

	interface = pycxsimulator.GUI()
	interface.start(func=[init,draw,step])