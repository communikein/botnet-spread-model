import pylab as PL
import matplotlib
matplotlib.use('TkAgg')

import simplejson as json
import csv

results_path_base = '../data/results/'
simulation_number = 1
results_path = results_path_base + str(simulation_number) + '/results.csv'

def loadStatisticsFile():
    data = dict()

    # Read data from CSV and convert to JSON
    fieldNames = ('infected', 'immune', 'susceptible', 'spread', 'attack', 'control')
    with open(results_path, 'r') as f:
        reader = csv.DictReader(f, fieldNames)
        rows = [row for row in reader]
        # Remove the headers
        del rows[0]
    
    out = json.dumps(rows)
    return json.loads(out)

def draw_botnet_statistics(infectedData, immuneData, step):
    PL.figure(1)
    PL.cla()
    PL.plot(infectedData, 'r')
    PL.plot(immuneData, 'g')
    PL.title('Botnet propagation - step ' + str(step))
    PL.show()

def init():
    global step
    global statistics
    global infectedData, immuneData

    infectedData = []
    immuneData = []

    step = 0
    statistics = loadStatisticsFile()

    print(type(statistics))

def draw():
    draw_botnet_statistics(infectedData, immuneData, step)

def step():
    global step
    global infectedData, immuneData

    infectedData.append(int(statistics[step]['infected']))
    immuneData.append(int(statistics[step]['immune']))

    step += 1


import pycxsimulator
pycxsimulator.GUI().start(func=[init,draw,step])