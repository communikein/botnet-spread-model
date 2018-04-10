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

results_path_base = '../data/results/'

def loadStatisticsFile():
	simulations_data = []
	fieldNames = ('infected', 'immune', 'susceptible', 'spread', 'attack', 'control')

	for sim in simulations:
		with open(sim + '/results.csv', 'r') as f:
			reader = csv.DictReader(f, fieldNames)
			rows = [row for row in reader]
			# Remove the headers
			del rows[0]

			out = json.dumps(rows)

		simulations_data.append(json.loads(out))

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
	global infectedData, immuneData
	global network_safe

	network_safe = False

	step = 0
	statistics = loadStatisticsFile()

	simulations_data = []
	for sim in range(len(statistics)):
		simulations_data.append(dict())
		simulations_data[sim]['infected'] = []
		simulations_data[sim]['immune'] = []

def draw():
	plot_title = 'Step ' + str(step)
	if network_safe:
		plot_title += ' - NETWORK SAFE.'
		print('NETWORK SAFE. Step ' + str(step))

	PL.figure(1)
	PL.cla()

	legend_handles = []
	for i in range(len(simulations_data)):
		selected_color = colors[int(i // 2)]
		infected_style = linestyles[i % 2]
		immune_style = linestyles[(i % 2) + 2]

		label_infected = 'Sim n. ' + str(sim_first + i) + ' - infected'
		sim_handle, = PL.plot(
			simulations_data[i]['infected'], 
			color=selected_color, linewidth=2, linestyle=infected_style, 
			label=label_infected)
		if not hide_immune:
			PL.plot(
				simulations_data[i]['immune'], 
				color=selected_color, linewidth=2, linestyle=immune_style)

		legend_handles.append(sim_handle)

	PL.legend(handles=legend_handles)
	PL.title(plot_title)
	PL.show()

def step():
	global step, final_steps
	global infectedData, immuneData, simulations_data
	global network_safe

	simulations_over = True
	for simulation in statistics:
		if step < len(simulation):
			new_infected = int(simulation[step]['infected'])
		else:
			new_infected = 0
		
		if new_infected > 0:
			simulations_over = False
			break

	if simulations_over:
		final_steps -= 1

	if final_steps == 0:
		network_safe = True
		interface.runEvent()
	else:
		for sim in range(len(statistics)):
			if step < len(statistics[sim]):
				simulations_data[sim]['infected'].append(int(statistics[sim][step]['infected']))
				simulations_data[sim]['immune'].append(int(statistics[sim][step]['immune']))
			else:
				simulations_data[sim]['infected'].append(int(simulations_data[sim]['infected'][step - 1]))
				simulations_data[sim]['immune'].append(int(simulations_data[sim]['immune'][step - 1]))

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

	if '-hybrid' in params:
		results_path_base += '-hybrid'
	results_path_base += '/'

	hide_immune = False
	if '-hide-immune' in params:
		hide_immune = True

	if '-all' in params:
		simulations = [results_path_base + sim for sim in os.listdir(results_path_base) if represents_int(sim)]
		sim_first = simulations[0]
		sim_first = sim_first[sim_first.rindex('/') + 1 :]
		if sim_first.startswith('0'):
			sim_first = int(sim_first[1:])
		else:
			sim_first = int(sim_first)
		
		print('Showing data from all simulations:')
		for simul in simulations:
			print(simul)
	elif '-num' in params:
		sim_first = params[params.index('-num') + 1]
		if not represents_int(sim_first):
			print('ERROR - Insert only one number.')
			return

		sim_first = int(sim_first)

		simulations = [results_path_base + str(sim_first)]
		if not os.path.exists(simulations[0]):
			print('ERROR - Couldn\'t find simulation\'s file: ' + str(simulations[0]))
			return

		print('Showing data from simulation number ' + str(sim_first) + '.')
	elif '-range' in params:
		sim_first = params[params.index('-range') + 1]
		if not represents_int(sim_first):
			print('ERROR \'-first\' - Insert only one number.')
			return
		sim_first = int(sim_first)

		sim_last = params[params.index('-range') + 2]
		if not represents_int(sim_last):
			print('ERROR \'-last\' - Insert only one number.')
			return
		sim_last = int(sim_last)

		simulations = [results_path_base + sim for sim in os.listdir(results_path_base) if represents_int(sim) and int(sim) >= sim_first and int(sim) <= sim_last]
		print('Showing data from the following simulations files:')
		for simul in simulations:
			print(simul)

		sim_count = sim_last - sim_first + 1

	return simulations

if __name__ == '__main__':
	global simulations
	global final_steps
	
	simulations = get_simulations(sys.argv)
	final_steps = 5

	interface = pycxsimulator.GUI()
	interface.start(func=[init,draw,step])