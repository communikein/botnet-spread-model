import matplotlib
matplotlib.use('TkAgg')

import pycxsimulator
import pylab as PL

import sys
import os
import simplejson as json
import csv

# red, purple, 
colors = ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a']
# line styles
linestyles = ['-', '--', '-.', ':']


cs_cluster_1 = ['10']
cs_cluster_2 = ['17']
cs_cluster_3 = ['18']
cs_cluster_4 = ['03', '05', '08']
cs_cluster_5 = ['01', '02', '06', '07', '09', '11', '12', '15']
cs_cluster_6 = ['04', '16']
cs_cluster_7 = ['19']
cs_cluster_8 = ['13']
cs_cluster_9 = ['14', '20']

cs_clusters = []
cs_clusters.append(cs_cluster_1)
cs_clusters.append(cs_cluster_2)
cs_clusters.append(cs_cluster_3)
cs_clusters.append(cs_cluster_4)
cs_clusters.append(cs_cluster_5)
cs_clusters.append(cs_cluster_6)
cs_clusters.append(cs_cluster_7)
cs_clusters.append(cs_cluster_8)
cs_clusters.append(cs_cluster_9)


results_path_base = '../data/results/'

def loadStatisticsFile():
	simulations_data = dict()
	fieldNames = ('infected', 'immune', 'susceptible', 'spread', 'attack', 'control')

	for sim in simulations:
		index = sim[sim.rfind('/') + 1 : ]
		with open(sim + '/results.csv', 'r') as f:
			reader = csv.DictReader(f, fieldNames)
			rows = [row for row in reader]
			# Remove the headers
			del rows[0]

			out = json.dumps(rows)

		simulations_data[index] = json.loads(out)

	return simulations_data

def represents_int(s):
	try: 
		int(s)
		return True
	except ValueError:
		return False


def init():
	global step
	global statistics, clusters_data
	global network_safe, max_data_len

	network_safe = False
	step = 0

	statistics = loadStatisticsFile()

	clusters_data = []
	max_data_len = max([len(statistics[num]) for num in statistics])

	while step < max_data_len:

		for i in range(len(cs_clusters)):
			
			if len(clusters_data) <= i or clusters_data[i] == None:
				clusters_data.append([])

			buff_data = []
			for sim_num in cs_clusters[i]:
				if len(statistics[sim_num]) > step:
					data = int(statistics[sim_num][step]['infected'])
				else:
					data = int(statistics[sim_num][len(statistics[sim_num]) - 1]['infected'])
				buff_data.append(data)

			clusters_data[i].insert(step, sum(buff_data) / float(len(buff_data)))

		step += 1

def draw():
	plot_title = 'Step ' + str(step)
	if network_safe:
		plot_title += ' - NETWORK SAFE.'
		print('NETWORK SAFE. Step ' + str(step))

	PL.figure(1)
	PL.cla()
	
	for i in range(len(clusters_data)):
		selected_color = colors[i]
		infected_style = linestyles[0]

		label_infected = 'Sim cluster ' + str(i + 1) + ' - infected'
		PL.plot(clusters_data[i], 
			color=selected_color, linewidth=2, linestyle=infected_style, 
			label=label_infected)

	PL.legend()
	PL.title(plot_title)
	PL.show()

def step():
	global step, final_steps
	global simulations_data
	global network_safe

	simulations_over = max_data_len >= step

	if simulations_over:
		final_steps -= 1

	if final_steps == 0:
		network_safe = True
		interface.runEvent()
	else:
		step += 1


def get_simulations(params):
	global results_path_base
	global sim_first, sim_count
	global hide_immune

	if '-central-server' in params:
		results_path_base += 'central-server'
	elif '-p2p' in params:
		results_path_base += 'peer-to-peer'
	else:
		print('ERROR - choose peer-to-peer or central-server mode.')
		return

	#if '-hybrid' in params:
	results_path_base += '-hybrid'
	results_path_base += '/'


	simulations = []
	for cluster in cs_clusters:
		for sim in cluster:
			path_to_add = results_path_base + sim
			simulations.append(path_to_add)

	return simulations

if __name__ == '__main__':
	global simulations
	global final_steps
	
	simulations = get_simulations(sys.argv)
	final_steps = 5

	interface = pycxsimulator.GUI()
	interface.start(func=[init,draw,step])