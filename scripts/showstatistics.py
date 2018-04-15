import matplotlib
matplotlib.use('TkAgg')

import pycxsimulator
import pylab as PL

import sys
import os
import simplejson as json
import csv

# red, purple, 
colors = ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a', '#000000', '#ff0000', '#00ff00']
# line styles
linestyles = ['-', '--', '-.', ':']

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
	global statistics, simulations_data
	global network_safe, max_data_len

	network_safe = False
	step = 0

	statistics = loadStatisticsFile()

	simulations_data = dict()
	for sim in statistics:
		simulations_data[sim] = dict()
		simulations_data[sim]['infected'] = []
		simulations_data[sim]['immune'] = []

	max_data_len = max([len(statistics[num]) for num in statistics])

	while step < max_data_len:

		for sim_num in statistics:

			if len(statistics[sim_num]) > step:
				data_infected = int(statistics[sim_num][step]['infected'])
				data_immune = int(statistics[sim_num][step]['immune'])
			else:
				data_infected = int(statistics[sim_num][len(statistics[sim_num]) - 1]['infected'])
				data_immune = int(statistics[sim_num][len(statistics[sim_num]) - 1]['immune'])

			simulations_data[sim_num]['infected'].append(data_infected)
			simulations_data[sim_num]['immune'].append(data_immune)

		step += 1

def draw():
	plot_title = 'Step ' + str(step)
	if network_safe:
		plot_title += ' - NETWORK SAFE.'
		print('NETWORK SAFE. Step ' + str(step))

	PL.figure(1)
	PL.cla()

	i = 0
	for sim_num in simulations_data:
		selected_color = colors[int(i // 4)]
		infected_style = linestyles[i % 4]
		immune_style = linestyles[3]

		label_infected = 'Sim n. ' + sim_num + ' - infected'
		label_immune = 'Sim n. ' + sim_num + ' - immune'

		PL.plot(simulations_data[sim_num]['infected'], 
			color=selected_color, linewidth=2, linestyle=infected_style, 
			label=label_infected)

		if not hide_immune:
			PL.plot(simulations_data[sim_num]['immune'], 
				color=selected_color, linewidth=2, linestyle=immune_style, 
				label=label_immune)

		i += 1

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

	hide_immune = True
	if '-immune' in params:
		hide_immune = False


	if '-all' in params:
		simulations = [results_path_base + sim for sim in os.listdir(results_path_base) if represents_int(sim)]
		sim_first = simulations[0]
		sim_first = sim_first[sim_first.rindex('/') + 1 :]
		if sim_first.startswith('0'):
			sim_first = int(sim_first[1:])
		else:
			sim_first = int(sim_first)
	
	elif '-num' in params:
		first_num_index = params.index('-num') + 1
		last_num_index = len(params)
		nums = params[first_num_index : last_num_index]
		
		if len(nums) == 0:
			print('ERROR - Insert at least one number.')
			return

		sim_first = 0
		simulations = []
		nums = parse_nums_input(nums)
		for num in nums:
			path_to_add = results_path_base + num
			simulations.append(path_to_add)
	
		if not os.path.exists(simulations[0]):
			print('ERROR - Couldn\'t find simulation\'s file: ' + str(simulations[0]))
			return

	simulations.sort()

	print('Showing data from the following simulations files:')
	for simul in simulations:
		print(simul)

	return simulations

def format_num(num):
	if len(num) < 2:
		result = '0' + num
	else:
		result = num

	return result

def parse_nums_input(nums):
	results = []
	for num in nums:
		first = num
		last = num

		if '-' in num:
			first = num.split('-')[0]
			last = num.split('-')[1]

		if first == last:
			results.append(format_num(first))
		else:
			for i in range(int(first), int(last) + 1):
				results.append(format_num(str(i)))

	return results

if __name__ == '__main__':
	global simulations
	global final_steps
	
	simulations = get_simulations(sys.argv)
	final_steps = 5

	interface = pycxsimulator.GUI()
	interface.start(func=[init,draw,step])