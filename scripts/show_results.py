import matplotlib
matplotlib.use('TkAgg')

import pycxsimulator
import pylab as PL

import sys
import simplejson as json
import csv

colors = ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a', '#000000', '#ff0000', '#00ff00']
linestyles = ['-', '--', '-.', ':']

cs_clusters = [
	['15', '16', '27'], # 1
	['02', '04', '14', '19', '25', '31', '32', '37', '50'], # 2
	['01', '05', '11', '13', '17', '20', '22', '28', '33', '35', '41', '42', '46', '48', '49'], # 3
	['03', '06', '07', '08', '09', '18', '21', '23', '24', '26', '29', '30', '34', '36', '38', '39', '40', '44', '45', '47'], # 4
]

p2p_clusters = [
	['39'],	# 1
	['42'],	# 2
	['12'], # 3
	['21', '29'], # 4
	['09', '16', '47'], # 5
	['30', '32', '40'], # 6
	['11', '13', '33'], # 7
	['04', '15', '24', '25', '27', '49'], # 8
	['01', '02', '10', '31', '36', '43', '46'], # 9
	['06', '07', '14', '22', '26', '35', '45'], # 10
	['03', '05', '19', '20', '28', '41', '44', '50'], # 11
	['08', '17', '18', '23', '34', '37', '38', '48'], # 12
]
'''
p2p_clusters = [
	['39'],	# 1
	['42'],	# 2
	['21', '29'], # 4
	['09', '16', '47'], # 5
	['11', '12', '13', '30', '32', '33', '40'], # 6
	['01', '02', '10', '31', '36', '43', '46'], # 7
	['03', '05', '19', '20', '28', '41', '44', '50'], # 8
	['04', '06', '07', '08', '14', '15', '17', '18', '22', '23', '24', '25', '26', '27', '35', '37', '38', '45', '48', '49'], # 9
]
'''

results_path_base = '../data/results/'

def loadStatisticsFile(simulations):
	simulations_data = dict()
	simulations_data['cs'] = dict()
	simulations_data['p2p'] = dict()
	fieldNames = ('infected', 'immune', 'susceptible', 'spread', 'attack', 'control')

	for sim in simulations:
		index = sim[sim.rfind('/') + 1 : ]
		with open(sim + '/results.csv', 'r') as f:
			reader = csv.DictReader(f, fieldNames)
			rows = [row for row in reader]
			# Remove the headers
			del rows[0]

			out = json.dumps(rows)

		model = 'cs'
		if 'peer-to-peer' in sim:
			model = 'p2p'

		simulations_data[model][index] = json.loads(out)

	return simulations_data


def init():
	global step
	global clusters_data
	global max_data_len

	step = 0

	clusters_data = []
	if max_data_len < 0:
		if model == 'both':
			max1 = max([len(statistics['cs'][num]) for num in statistics['cs']])
			max2 = max([len(statistics['p2p'][num]) for num in statistics['p2p']])
			max_data_len = max([max1, max2])
		else:
			max_data_len = max([len(statistics[model][num]) for num in statistics[model]])

	while step < max_data_len:

		for i in range(len(selected_model_clusters)):
			
			if len(clusters_data) <= i or clusters_data[i] == None:
				clusters_data.append([])

			clusters_data[i].insert(step, get_simulation_data(i, step))

		step += 1

def get_simulation_data(cluster_index, step):
	buff_data = []

	origin_model = model
	if model == 'both':
		if cluster_index < selected_model_clusters_len[0]:
			origin_model = 'cs'
		else:
			origin_model = 'p2p'

	for sim_num in selected_model_clusters[cluster_index]:
		if len(statistics[origin_model][sim_num]) > step:
			data = int(statistics[origin_model][sim_num][step]['infected'])
		else:
			data = int(statistics[origin_model][sim_num][len(statistics[origin_model][sim_num]) - 1]['infected'])
		buff_data.append(data)

	return sum(buff_data) / float(len(buff_data))

def draw():
	PL.figure(1)
	PL.cla()
	
	for i in range(len(clusters_data)):
		selected_color, infected_style = get_line_style(i)

		label_infected = 'Cluster ' + str(i + 1) + ' (' + str(len(selected_model_clusters[i])) + ' sim)'
		PL.plot(clusters_data[i], 
			color=selected_color, linewidth=2, linestyle=infected_style, 
			label=label_infected)

	if show_legend:
		PL.legend()
	PL.title('Step ' + str(step))
	PL.show()

def get_line_style(cluster_index):
	index_color = cluster_index
	index_style = 0

	if model == 'both':
		index_color = cluster_index % max(selected_model_clusters_len)

		if cluster_index >= selected_model_clusters_len[0]:
			index_style = 1

	return colors[index_color], linestyles[index_style]


def step(): return


def get_simulations(params):
	global selected_model_clusters, selected_model_clusters_len
	global results_path_base
	global model, max_data_len, show_legend

	max_data_len = -1
	if '-limit' in params:
		max_data_len = int(params[params.index('-limit') + 1])

	show_legend = False
	if '-legend' in params:
		show_legend = True

	if '-cs' in params:
		results_path_base += 'central-server-hybrid/'
		selected_model_clusters = cs_clusters
		selected_model_clusters_len = [len(selected_model_clusters)]
		model = 'cs'
	elif '-p2p' in params:
		results_path_base += 'peer-to-peer-hybrid/'
		selected_model_clusters = p2p_clusters
		selected_model_clusters_len = [len(selected_model_clusters)]
		model = 'p2p'
	else:
		selected_model_clusters = cs_clusters + p2p_clusters
		selected_model_clusters_len = [len(cs_clusters), len(p2p_clusters)]
		model = 'both'

	simulations = []

	if model == 'both':
		for cluster in selected_model_clusters:
			for sim in cluster:
				if selected_model_clusters.index(cluster) < selected_model_clusters_len[0]:
					simulations.append(results_path_base + 'central-server-hybrid/' + sim)
				else:
					simulations.append(results_path_base + 'peer-to-peer-hybrid/' + sim)
	else:
		for cluster in selected_model_clusters:
			for sim in cluster:
				simulations.append(results_path_base + sim)

	return simulations

if __name__ == '__main__':
	global statistics
	
	simulations = get_simulations(sys.argv)
	statistics = loadStatisticsFile(simulations)

	pycxsimulator.GUI().start(func=[init,draw,step])