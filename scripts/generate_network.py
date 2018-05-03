# *** Botnet spread in computer network ***
#
# Project by Maracani Elia
# Matricola: 763734

import networkx as NX
import itertools
import random

from datetime import datetime
from timezonefinder import TimezoneFinder
from pytz import timezone
import pytz

import pickle

from numpy import array, float32
from math import sin, cos, sqrt, atan2, radians, log, exp

SUSCEPTIBLE = 0
INFECTED = 1
IMMUNE = 2

ROLE_NONE = 3
ROLE_ATTACK = 4
ROLE_CONTROL = 5
ROLE_CONTROL_SPREAD = 6
ROLE_SPREAD = 7

tf = TimezoneFinder()
utc = pytz.utc

random.seed()

# approximate radius of earth in km
R = 6373.0

img_width = 1176
img_height = 489

lat_max = 90
lng_max = 180

DEBUG = True

# Base probability for link between two random nodes
link_prob_base = 0.1


devices_divider = 100000
total_devices = int(3404265884 // devices_divider) - 102

def loadInternetDevices():
    with open('../data/internet-usage-data-final.p', 'rb') as origin:
        data = pickle.load(origin)
    del data['TOTAL']

    return data

def lookupInternetDevicesByCode(progress_devices, code):
    if code in progress_devices:
        return progress_devices[code]

    return None

def loadCountryCodeFromTimeZone():
    with open('../data/tzf-list-tz-final.p', 'rb') as origin:
        data = pickle.load(origin)

    return data

def init_devices_lists(internet_data):
    result = dict()

    for country_code in internet_data:
        data = dict()
        devices = int(internet_data[country_code]['devices']) // devices_divider
        if devices > 0:
            data['devices'] = devices
            data['bounds'] = internet_data[country_code]['bounds']
            data['perc'] = 1.0

            result[country_code.lower()] = data

    return result
            


def init_nodes(graph):
    for i in graph.nodes():
        # Generate valid coordinates
        while True:
            if len(progress_devices.keys()) != 0:
                country = progress_devices.keys()[0]
                bounds = progress_devices[country]['bounds']
                lat, lng = pick_coords(bounds)
                time_zone = get_time_zone(lat, lng, country)

                if time_zone is not None:
                   break
            else:
                break

        # Assign values to node
        graph.node[i]['lat'] = lat
        graph.node[i]['lng'] = lng
        graph.node[i]['time_zone'] = time_zone
        graph.node[i]['state'] = SUSCEPTIBLE
        graph.node[i]['role'] = ROLE_NONE
        graph.node[i]['just_infected'] = False
        graph.node[i]['clients'] = []
        graph.node[i]['parent'] = None

    return graph

def pick_coords(bounds):
    min_lat = bounds['northeast']['lat']
    max_lat = bounds['southwest']['lat']
    latitude = choose_latitude(min_lat, max_lat)

    min_lng = bounds['southwest']['lng']
    max_lng = bounds['northeast']['lng']
    if max_lng < min_lng:
        option_one = choose_longitude(min_lng, 180)
        option_two = choose_longitude(-180, max_lng)

        choice = random.randint(0,1)
        if choice == 0:
            longitude = option_one
        else:
            longitude = option_two
    else:
        longitude = choose_longitude(min_lng, max_lng)
    
    return latitude, longitude

def choose_latitude(lower, upper):
    rnd = random.uniform(lower, upper)
    return round(rnd, 2)

def choose_longitude(lower, upper):
    rnd = random.uniform(lower, upper)
    return round(rnd, 2)

def get_time_zone(latitude, longitude, country):
    today = datetime.now()

    try:
        tz_target_name = tf.timezone_at(lat=latitude, lng=longitude)
        tz_target_name = check_time_zone(tz_target_name, country, latitude, longitude)

        if tz_target_name is None:
            return None

    except:
        return None

    tz_target = timezone(tz_target_name)
    today_target = tz_target.localize(today)
    today_utc = utc.localize(today)

    time_zone_offset = (today_utc - today_target).total_seconds() // (60 * 60)
    return time_zone_offset

def check_time_zone(name, country_bounds, latitude, longitude):
    # If the timezone coords are relatives to water, try again
    if name is None:
        return None
    else:
        #if the timezone is not in the statistics, try again
        if name not in timezone_cc:
            return None
        else:
            country = timezone_cc[name]

            # Check whether the country from the bounds is the same as the one from the coords
            if country_bounds.lower() == country.lower():
                data_new = lookupInternetDevicesByCode(progress_devices, country)
                data_old = lookupInternetDevicesByCode(original_devices, country)

                if data_new is None:
                    return None
                else:
                    checkProgress(data_new, data_old, country)
                    return name
            else:
                return None

    return name

def checkProgress(data_new, data_old, country):
    global progress_devices
    devices_new = data_new['devices'] - 1
    
    if devices_new == 0:
        if DEBUG:
            print('Device from \"' + country + '\". IT WAS THE LAST.')
        
        del progress_devices[country]
        countries_left = [left for left in progress_devices]
        
        if DEBUG:
            print(countries_left)

    else:
        progress_devices[country]['devices'] = devices_new

        perc_old = progress_devices[country]['perc']
        perc_new = float(devices_new) / float(data_old['devices'])
        if perc_old * 100 - perc_new * 100 >= 1:
            progress_devices[country]['perc'] = perc_new
            perc_new_used = (1 - perc_new) * 100
            perc_old_used = (1 - perc_old) * 100
            
            if DEBUG:
                print('Device from \"' + str(country) + '\". Used devices: ' + str(int(perc_new_used)) + '%')

def add_nodes_positions(network):
    positions = dict()

    for i in network.nodes():
        x = (network.node[i]['lng'] + lng_max) / (lng_max * 2) * img_width
        y = (network.node[i]['lat'] + lat_max) / (lat_max * 2) * (img_height + lat_max)
        y = img_height - y + lat_max

        pos = dict()
        pos['x'] = x
        pos['y'] = y
        network.node[i]['position'] = pos

    return network



def compute_graph_links(graph):
    population_size = len(graph.nodes())

    # Get all the possible links
    if DEBUG:
        print('Generating all the possible egdes...')
    edges = itertools.combinations(range(population_size), 2)

    # Choose the links to keep based on the time zones
    if DEBUG:
        print('Choosing the links to keep based on nodes location...')
    for e in edges:
        distance = get_distance(graph.node[e[0]], graph.node[e[1]])
        if random.random() < link_prob(distance, link_prob_base):
            graph.add_edge(*e)

    return graph

def get_distance(node_a, node_b):
    dlon = node_b['lng'] - node_a['lng']
    dlat = node_b['lat'] - node_a['lat']

    a = sin(dlat / 2)**2 + cos(node_a['lat']) * cos(node_b['lat']) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c

def link_prob(distance, base_prob):
    min_prob = 0.000039
    max_prob = 0.999961

    b = log(max_prob / min_prob) / (max_prob - min_prob)
    a = min_prob / exp(b * min_prob)

    prob = 1 - (distance / 20040.0)

    exp_prob = a * exp(prob * b)

    return base_prob * exp_prob

def load_graph(path='../data/graph-data-complete.p'):
    graph = NX.read_gpickle(path)
    return graph

def save_graph(graph, path='../data/graph-data-complete.p'):
    NX.write_gpickle(graph, path)

def pick_patient_zero(network):

    for i in network.nodes():
        network.node[i]['state'] = SUSCEPTIBLE
        network.node[i]['role'] = ROLE_NONE
        network.node[i]['just_infected'] = False
        network.node[i]['clients'] = []
        network.node[i]['parent'] = None

    # Choose random 'patient zero'
    i = random.randint(0, len(network.nodes()))
    network.node[i]['state'] = INFECTED
    network.node[i]['role'] = ROLE_SPREAD
    network.node[i]['clients'] = []
    network.node[i]['parent'] = i

    print('---------------------------------------------')
    print('Random \'patient zero\' chosen.')
    print('Node n.' + str(i))
    print('Time zone: ' + str(network.node[i]['time_zone']))
    print('---------------------------------------------')

    return network


if __name__ == "__main__":
    global progress_devices, original_devices, devices_divider, timezone_cc
    global debug, debug_country
    
    internet_data = loadInternetDevices()
    timezone_cc = loadCountryCodeFromTimeZone()
    progress_devices = init_devices_lists(internet_data)
    original_devices = init_devices_lists(internet_data)

    if DEBUG:
        print('----------------------------------------------')
        print('Generating graph...')
        print('Generating ' + str(total_devices) + ' nodes.')
        print('Using statistics from ' + str(len(original_devices)) + ' different countries.')
        print('----------------------------------------------')
        print('')

    # Create a non-directed graph
    network = NX.Graph()
    
    # Add n nodes to the graph
    if DEBUG:
        print('Creating the nodes..')
    network.add_nodes_from(range(total_devices))

    if DEBUG:
        print('Initializing nodes..')
    network = init_nodes(network)

    if DEBUG:
        print('Computing nodes positions..')
    network = add_nodes_positions(network)

    if DEBUG:
        print('Computing links..')
    network = compute_graph_links(network)

    if DEBUG:
        print('Picking patient zero..')
    network = pick_patient_zero(network)

    if DEBUG:
        print('Saving network structure..')
    NX.write_gpickle(network, '../data/graph-data-hybrid.p')