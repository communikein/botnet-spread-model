import matplotlib
matplotlib.use('TkAgg')

import numpy as np

import pycxsimulator
import pylab as PL

import sys
import os
import simplejson as json
import csv

colors = ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a', '#000000', '#ff0000', '#00ff00']
linestyles = ['-', '--', '-.', ':']

results_path_base = '../data/results/'

show_simulations = [False for i in range(50)]

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
		simulations_data[sim]['removal_after_detection'] = 0
		simulations_data[sim]['peak_infection_bots'] = 0
		simulations_data[sim]['peak_infection_susceptible'] = 0
		simulations_data[sim]['peak_infection_step'] = 0
		simulations_data[sim]['peak_infection_spread'] = 0
		simulations_data[sim]['peak_infection_attack'] = 0
		simulations_data[sim]['peak_infection_control'] = 0
		simulations_data[sim]['first_immune'] = 0

	if max_data_len < 0:
		max_data_len = max([len(statistics[num]) for num in statistics])
	
	while step < max_data_len:

		for sim_num in statistics:

			if len(statistics[sim_num]) > step:
				data_infected = int(statistics[sim_num][step]['infected'])
				data_immune = int(statistics[sim_num][step]['immune'])

				if simulations_data[sim_num]['peak_infection_bots'] < data_infected:
					simulations_data[sim_num]['peak_infection_bots'] = data_infected
					simulations_data[sim_num]['peak_infection_step'] = step
					simulations_data[sim_num]['peak_infection_susceptible'] = int(statistics[sim_num][step]['susceptible'])
					simulations_data[sim_num]['peak_infection_spread'] = int(statistics[sim_num][step]['spread'])
					simulations_data[sim_num]['peak_infection_attack'] = int(statistics[sim_num][step]['attack'])
					simulations_data[sim_num]['peak_infection_control'] = int(statistics[sim_num][step]['control'])
				if simulations_data[sim_num]['first_immune'] == 0 and data_immune > 0:
					simulations_data[sim_num]['first_immune'] = step
			else:
				data_infected = int(statistics[sim_num][len(statistics[sim_num]) - 1]['infected'])
				data_immune = int(statistics[sim_num][len(statistics[sim_num]) - 1]['immune'])

			simulations_data[sim_num]['infected'].append(data_infected)
			simulations_data[sim_num]['immune'].append(data_immune)
			simulations_data[sim_num]['tot_steps'] = len(statistics[sim_num])
			simulations_data[sim_num]['removal_after_detection'] = simulations_data[sim_num]['tot_steps'] - simulations_data[sim_num]['first_immune']

		step += 1

	
	simulations_steps = np.asarray([len(statistics[sim]) for sim in statistics])
	print('1. Total steps.')
	print('Average: ' + str(np.average(simulations_steps)))
	print('Standard Deviation: ' + str(np.std(simulations_steps)))
	print('Max: ' + str(np.max(simulations_steps)))
	print('Min: ' + str(np.min(simulations_steps)))
	print('')

	peak_infection_step = np.asarray([simulations_data[sim]['peak_infection_step'] for sim in simulations_data])
	peak_infection_infected = np.asarray([simulations_data[sim]['peak_infection_bots'] for sim in simulations_data])
	peak_infection_susceptible = np.asarray([simulations_data[sim]['peak_infection_susceptible'] for sim in simulations_data])
	peak_infection_spread = np.asarray([simulations_data[sim]['peak_infection_spread'] for sim in simulations_data])
	peak_infection_attack = np.asarray([simulations_data[sim]['peak_infection_attack'] for sim in simulations_data])
	peak_infection_control = np.asarray([simulations_data[sim]['peak_infection_control'] for sim in simulations_data])
	print('2. Peak infection.')
	print('Steps - (' + 
			'avg: ' + str(np.average(peak_infection_step)) + '; '
			'std: ' + str(np.std(peak_infection_step)) + '; '
			'max: ' + str(np.max(peak_infection_step)) + '; '
			'min: ' + str(np.min(peak_infection_step)) + ')')
	print('\t2.1 Infection status.')
	print(	'\tSusceptible - (' +
			'avg: ' + str(np.average(peak_infection_susceptible)) +  '; '
			'std: ' + str(np.std(peak_infection_susceptible)) + '; '
			'max: ' + str(np.max(peak_infection_susceptible)) + '; '
			'min: ' + str(np.min(peak_infection_susceptible)) + ')')
	print(	'\tInfected - (' +
			'avg: ' + str(np.average(peak_infection_infected)) +  '; '
			'std: ' + str(np.std(peak_infection_infected)) + '; '
			'max: ' + str(np.max(peak_infection_infected)) + '; '
			'min: ' + str(np.min(peak_infection_infected)) + ')')
	print(	'\tSpread bots - (' + 
			'avg: ' + str(np.average(peak_infection_spread)) + '; '
			'std: ' + str(np.std(peak_infection_spread)) + '; '
			'max: ' + str(np.max(peak_infection_spread)) + '; '
			'min: ' + str(np.min(peak_infection_spread)) + ')')
	print(	'\tAttack bots - (' + 
			'avg: ' + str(np.average(peak_infection_attack)) + '; '
			'std: ' + str(np.std(peak_infection_attack)) + '; '
			'max: ' + str(np.max(peak_infection_attack)) + '; '
			'min: ' + str(np.min(peak_infection_attack)) + ')')
	print(	'\tControl bots - (' + 
			'avg: ' + str(np.average(peak_infection_control)) + '; '
			'std: ' + str(np.std(peak_infection_control)) + '; '
			'max: ' + str(np.max(peak_infection_control)) + '; '
			'min: ' + str(np.min(peak_infection_control))) + ')'
	print('')

	botnet_detection = np.asarray([simulations_data[sim]['first_immune'] for sim in simulations_data])
	botnet_detection_removal = np.asarray([simulations_data[sim]['removal_after_detection'] for sim in simulations_data])
	print('3. Botnet detection.') 
	print('Average steps: ' + str(np.average(botnet_detection)))
	print('Standard deviation: ' + str(np.std(botnet_detection)))
	print('Max: ' + str(np.max(botnet_detection)))
	print('Min: ' + str(np.min(botnet_detection)))
	print('Average complete removal remaining steps: ' + str(np.average(botnet_detection_removal)))
	print('Standard deviation: ' + str(np.std(botnet_detection_removal)))
	print('Max: ' + str(np.max(botnet_detection_removal)))
	print('Min: ' + str(np.min(botnet_detection_removal)))
	print('')

def draw():
	plot_title = 'Step ' + str(step)
	if network_safe:
		plot_title += ' - NETWORK SAFE.'
		print('NETWORK SAFE. Step ' + str(step))

	PL.figure(1)
	PL.cla()

	i = 0
	simulations_numbers = sorted(simulations_data.keys())
	for i in range(0, len(simulations_numbers)):
		sim_num = simulations_numbers[i]

		if show_simulations[int(sim_num) - 1]:
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

	if show_legend:
		PL.legend()
	PL.title(plot_title)
	PL.show()

def step(): return


def get_simulations(params):
	global results_path_base
	global sim_first, sim_count
	global hide_immune, show_legend, show_plot
	global max_data_len

	if '-cs' in params:
		results_path_base += 'central-server/'
	elif '-p2p' in params:
		results_path_base += 'peer-to-peer/'
	else:
		print('ERROR - choose peer-to-peer or central-server mode.')
		return

	'''
	show_plot = True
	if '-hide-plot':
		show_plot = False
	'''

	max_data_len = -1
	if '-limit' in params:
		max_data_len = int(params[params.index('-limit') + 1])

	show_legend = False
	if '-legend' in params:
		show_legend = True

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

	'''
	print('Showing data from the following simulations files:')
	for simul in simulations:
		print(simul)
	print('#' * 20)
	print('')
	'''

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




def simulation00(val='1234567890'):
	global show_simulations

	show_simulations = filter_simulations(base=0, val=val)

	return val

def simulation10(val='1234567890'):
	global show_simulations

	show_simulations = filter_simulations(base=10, val=val)

	return val

def simulation20(val='1234567890'):
	global show_simulations

	show_simulations = filter_simulations(base=20, val=val)

	return val

def simulation30(val='1234567890'):
	global show_simulations

	show_simulations = filter_simulations(base=30, val=val)

	return val

def simulation40(val='1234567890'):
	global show_simulations

	show_simulations = filter_simulations(base=40, val=val)

	return val

def filter_simulations(base, val):
	result = [x for x in show_simulations]

	for num in range(10):
		index = base
		if num == 0:
			index += 9
		else:
			index += num - 1

		user_input = str(val)
		if '.' in user_input:
			user_input = user_input[ : user_input.index('.')]
		
		if user_input == '-1':
			result[index] = False
		else:
			if str(num) in user_input:
				result[index] = True
			else:
				result[index] = False

	return result



global simulations
global final_steps
global show_plot

show_plot = False
final_steps = 5
args = ['-p2p', '-limit', '300', '-all', '-legend']
params = [simulation00, simulation10, simulation20, simulation30, simulation40]

if len(sys.argv) > 1:
	args = sys.argv
simulations = get_simulations(args)

interface = pycxsimulator.GUI(parameterSetters=params)
interface.start(func=[init,draw,step])