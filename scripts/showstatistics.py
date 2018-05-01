import matplotlib
matplotlib.use('TkAgg')

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
		simulations_data[sim]['max_infected'] = 0
		simulations_data[sim]['max_infected_step'] = 0
		simulations_data[sim]['first_immune'] = 0

	if max_data_len < 0:
		max_data_len = max([len(statistics[num]) for num in statistics])

	steps = 0
	for sim in statistics:
		steps += len(statistics[sim])
	
	print('Avg steps: ' + str(int(steps / len(statistics.keys()))))
	print('Max steps: ' + str(max([len(statistics[sim]) for sim in statistics])))
	print('Min steps: ' + str(min([len(statistics[sim]) for sim in statistics])))

	while step < max_data_len:

		for sim_num in statistics:

			if len(statistics[sim_num]) > step:
				data_infected = int(statistics[sim_num][step]['infected'])
				data_immune = int(statistics[sim_num][step]['immune'])

				if simulations_data[sim_num]['max_infected'] < data_infected:
					simulations_data[sim_num]['max_infected'] = data_infected
					simulations_data[sim_num]['max_infected_step'] = step
				if simulations_data[sim_num]['first_immune'] == 0 and data_immune > 0:
					simulations_data[sim_num]['first_immune'] = step
			else:
				data_infected = int(statistics[sim_num][len(statistics[sim_num]) - 1]['infected'])
				data_immune = int(statistics[sim_num][len(statistics[sim_num]) - 1]['immune'])

			simulations_data[sim_num]['infected'].append(data_infected)
			simulations_data[sim_num]['immune'].append(data_immune)
			simulations_data[sim_num]['tot_steps'] = len(statistics[sim_num])

		step += 1

	steps_to_zero = dict()
	steps_to_zero_first_immune = dict()
	for sim in simulations_data:
		steps_to_zero[sim] = simulations_data[sim]['tot_steps'] - simulations_data[sim]['max_infected_step']
		steps_to_zero_first_immune[sim] = simulations_data[sim]['tot_steps'] - simulations_data[sim]['first_immune']

	print('Avg max infected step: ' + str(sum([simulations_data[sim]['max_infected_step'] for sim in simulations_data]) / len(simulations_data)))
	print('Avg max infected: ' + str(sum([simulations_data[sim]['max_infected'] for sim in simulations_data]) / len(simulations_data)))
	print('Avg from max infected to zero steps: ' + str(sum([steps_to_zero[sim] for sim in steps_to_zero]) / len(steps_to_zero)))
	print('Avg first immune step: ' + str(sum([simulations_data[sim]['first_immune'] for sim in simulations_data]) / len(simulations_data)))
	print('Avg from first immune to zero steps: ' + str(sum([steps_to_zero_first_immune[sim] for sim in steps_to_zero_first_immune]) / len(steps_to_zero_first_immune)))

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
	global hide_immune, show_legend
	global max_data_len

	if '-cs' in params:
		results_path_base += 'central-server'
	elif '-p2p' in params:
		results_path_base += 'peer-to-peer'
	else:
		print('ERROR - choose peer-to-peer or central-server mode.')
		return

	max_data_len = -1
	if '-limit' in params:
		max_data_len = int(params[params.index('-limit') + 1])

	show_legend = False
	if '-legend' in params:
		show_legend = True

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
	print('#' * 20)
	print('')

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


if __name__ == '__main__':
	global simulations
	global final_steps
	
	simulations = get_simulations(sys.argv)
	final_steps = 5

	params = [simulation00,simulation10,simulation20,simulation30,simulation40]
	interface = pycxsimulator.GUI(parameterSetters=params)
	interface.start(func=[init,draw,step])