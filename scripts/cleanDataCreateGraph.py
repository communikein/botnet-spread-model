import pycountry
import unidecode
import os
import csv
import simplejson as json
import pickle
import re
import unidecode

import networkx as NX
import random
import itertools

from timezonefinder import TimezoneFinder
import pycountry
import pytz
from pytz import timezone
from datetime import datetime

import time
import googlemaps

from botnetspread import SUSCEPTIBLE, INFECTED, ROLE_NONE, ROLE_SPREAD

tf = TimezoneFinder()
utc = pytz.utc
random.seed()

img_width = 1176
img_height = 489

lat_max = 90
lng_max = 180

global progress_devices, countries_with_devices_left
global devices_divider


# !!!!!!!!!!!!! DO NOT USE
def convertInternetDevicesToPickle():
    data = dict()

    # Read data from CSV and convert to JSON
    fieldNames = ('country', 'devices', 'percentage')
    with open('../data/internet-usage-data-cleaned.csv', 'r') as f:
        reader = csv.DictReader(f, fieldNames)
        rows = [row for row in reader]
        # Remove the headers
        del rows[0]
        
        out = json.dumps(rows)

    # Parse data to a more convenient JSON format
    for entry in json.loads(out):
        country = re.sub(r'\([^)]*\)', '', entry['country']).strip()
        country = unidecode.unidecode(country).lower()

        country_data = dict()
        country_data['devices'] = entry['devices']
        country_data['percentage'] = entry['percentage']

        if pycountry_lookup(country) is not None:
            country_data['code'] = pycountry_lookup(country).alpha_2    
        else:
            print('Country ' + country + ' not found code.')

        data[country] = country_data

    # Save the newly generated JSON to file
    with open('../data/backup/internet-usage-data-cleaned.json', 'w') as f:
        f.write(json.dumps(data))


    # Convert it to Pickle and save it to file
    with open('../data/internet-usage-data-cleaned.p', 'wb') as fp:
        pickle.dump(data, fp, protocol=pickle.HIGHEST_PROTOCOL)

    return data

def initGoogleMaps(api_key):
    gmaps = googlemaps.Client(key=api_key)

    return gmaps

# !!!!!!!!!!! THIS METHOD USES GOOGLE APIs, IT MIGHT REQUIRE PAYMENT
def addCountriesBoundaries(gmaps):
    with open('../data/internet-usage-data-cleaned.p', 'rb') as origin:
        data = pickle.load(origin)

    for country_name in data:
        #print(data[country_name])

        if 'total' != country_name and 'bounds' not in data[country_name]:
            geocode_result = gmaps.geocode(country_name)
            
            print('Country: ' + str(country_name))
            if 'bounds' in geocode_result[0]['geometry']:
                data[country_name]['bounds'] = geocode_result[0]['geometry']['bounds']
                print(country_name + ' boundaries: ' + str(data[country_name]['bounds']))
            else:
                print('Error, country not recognised!')
            time.sleep(1)

    # Save the newly generated JSON to file
    with open('../data/internet-usage-data-cleaned-bounds.p', 'wb') as dest:
        pickle.dump(data, dest, protocol=pickle.HIGHEST_PROTOCOL)

def pycountry_lookup(name):
    try:
        return pycountry.countries.lookup(name)
    except:
        return None

def splitCitiesFiles():
    rowsPerFile = 128000
    headers = 'country,city,accentCity,region,population,latitude,longitude\n'

    with open('../data/world-cities/world-cities.csv', 'r') as f:
        rows = [row for row in f]

    filesNum = len(rows) / rowsPerFile
    if len(rows) % rowsPerFile != 0:
        filesNum += 1

    for i in range(filesNum):
        file_path = '../data/world-cities/world-cities-part-' + str(i) + '.csv' 

        with open(file_path, 'w') as dest:
            dest.write(headers)
        
            for j in range(rowsPerFile):
                rowIndex = (i * rowsPerFile) + j
                if rowIndex < len(rows):
                    dest.write(rows[rowIndex])
                else:
                    break

def convertCitiesToPickle():
    data = dict()

    files = os.listdir('../data/world-cities')

    # Read data from CSV and convert to JSON
    fieldNames = ('country', 'city', 'accentCity', 'region', 'population', 'latitude', 'longitude')
    
    for file in files:
        print('Analyzing file: ' + str(file) + ' ...')
        with open('../data/world-cities/' + file, 'r') as origin:
            reader = csv.DictReader(origin, fieldNames)
            out = json.dumps([row for row in reader])

            # Parse data to a more convenient JSON format
            for entry in json.loads(out):
                city_name = entry['city'].lower().replace('_', ' ').replace('-', ' ').strip()
                city_data = dict()
                city_data['country'] = entry['country'].lower()
                city_data['region'] = entry['region']
                city_data['latitude'] = entry['latitude']
                city_data['longitude'] = entry['longitude']

                data[city_name] = city_data


    # Save the newly generated JSON to file
    print('Saving dictionary to JSON file...')
    with open('../data/backup/world-cities.json', 'w') as f:
        f.write(json.dumps(data))

    print('Saving dictionary to Pickle file...')
    # Convert it to Pickle and save it to file
    with open('../data/world-cities.p', 'wb') as fp:
        pickle.dump(data, fp, protocol=pickle.HIGHEST_PROTOCOL)

def cleanCountryCodes():
    with open('../data/country-code.p', 'rb') as origin:
        data = pickle.load(origin)

    result = dict()
    for item in data:
        country = re.sub(r'\([^)]*\)', '', item['Country']).strip()
        country = unidecode.unidecode(country.lower())
        
        result[country] = item['Code-2'].lower()

    # Save the newly generated JSON to file
    print('Saving dictionary to JSON file...')
    with open('../data/backup/country-code.json', 'w') as dest:
        dest.write(json.dumps(result))

    with open('../data/country-code.p', 'wb') as fdest:
        pickle.dump(result, dest, protocol=pickle.HIGHEST_PROTOCOL)

    return result

def cleanTimeZoneCountryCodes():
    with open('../data/tzdb-list-tz-utf.json', 'r') as origin:
        data = json.load(origin)

    result = dict()
    for entry in data:
        new_data = dict()
        new_data['code'] = entry['CC'].lower()
        new_data['comments'] = entry['Comments']
        new_data['notes'] = entry['Notes']

        result[entry['TZ']] = new_data

    # Save the newly generated JSON to file
    with open('../data/backup/tzdb-list-tz-cleaned.json', 'w') as dest:
        dest.write(json.dumps(result))

    with open('../data/tzdb-list-tz-cleaned.p', 'wb') as dest:
        pickle.dump(result, dest, protocol=pickle.HIGHEST_PROTOCOL)




def loadInternetDevices():
    with open('../data/internet-usage-data-cleaned-bounds.p', 'rb') as origin:
        data = pickle.load(origin)

    return data

def lookupInternetDevicesByCode(progress_devices, code):
    if code in progress_devices:
        return progress_devices[code]

    return None

def loadCountriesCodes():
    with open('../data/country-code.p', 'rb') as origin:
        data = pickle.load(origin)

    return data

def loadCountryCodeFromTimeZone():
    with open('../data/tzdb-list-tz-cleaned.p', 'rb') as origin:
        data = pickle.load(origin)

    return data



def init_nodes(graph):
    for i in graph.nodes():
        # Generate valid coordinates
        while True:
            if len(progress_devices.keys()) != 0:
                country = progress_devices.keys()[0]
                bounds = progress_devices[country]['bounds']
                lat, lng, min_lat, max_lat, min_lng, max_lng = pick_coords(bounds)
                if country == debug_country and debug:
                    print('lat: ' + str(lat) + ', lng: ' + str(lng))
                    print('Bounds. lat: [' + str(min_lat) + '::' + str(max_lat) + '] lng: [' + str(min_lng) + '::' + str(max_lng) + ']')
                    print('Chosen. lat: ' + str(lat) + ', lng: ' + str(lng))
                
                time_zone = get_time_zone(lat, lng, country)
                if time_zone is not None:
                   break
            else:
                break

        if len(progress_devices.keys()) == 0:
            print('Node: ' + str(i))
        # Assign values to node
        graph.node[i]['lat'] = lat
        graph.node[i]['lng'] = lng
        graph.node[i]['time_zone'] = time_zone
        graph.node[i]['state'] = SUSCEPTIBLE
        graph.node[i]['role'] = ROLE_NONE
        graph.node[i]['just_infected'] = False

    return graph

def pick_coords(bounds):
    min_lat = bounds['northeast']['lat']
    max_lat = bounds['southwest']['lat']
    '''
    if max_lat < min_lat:
        tmp = max_lat
        max_lat = min_lat
        min_lat = tmp
    '''
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
    
    return latitude, longitude, min_lat, max_lat, min_lng, max_lng

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
        if country == debug_country and debug:
            print(tz_target_name)
        tz_target_name = check_time_zone(tz_target_name, country)
        if tz_target_name is None:
            return None
    except:
        #print('ERROR: get_time_zone()')
        #print('lat: ' + str(latitude) + ', lng: ' + str(longitude))
        return None

    if tz_target_name is None:
        return None

    tz_target = timezone(tz_target_name)
    today_target = tz_target.localize(today)
    today_utc = utc.localize(today)

    return (today_utc - today_target).total_seconds() // (60 * 60)

def check_time_zone(name, country_bounds):
    global progress_devices, original_devices

    if name is None:
        #print('Hit the water, retry!!')
        return None
    else:
        '''
        city = name
        if '/' in city:
            city = city[city.rfind('/') + 1:]
        if '-' in city or '_' in city:
            city = city.replace('_', ' ').replace('-', ' ')
        if '(' in city and ')' in city:
            city = re.sub(r'\([^)]*\)', '', city)
        city = unidecode.unidecode(city.strip().lower())
        #print('Done.')
        '''
        
        #if city not in cities:
        if name not in timezone_cc:
            #print('City not recognised, retry!!\t city: ' + str(city))
            return None
        else:
            '''
            possible_cities = []
            for city_index in cities:
                if city_index == city:
                    possible_cities.append(cities[city_index])

            if len(possible_cities) > 1:
                print('Found ' + len(possible_cities) + ' cities with the same name...')
            '''    
            #print(city)
            #country = cities[city]['country'].lower()
            country = timezone_cc[name]['code']
            if country_bounds.lower() == debug_country.lower() and debug:
                print('Country found: ' + str(country) + ' - Expected: ' + str(country_bounds))

            # Check whether the country from the bounds is the same as the one from the coords
            if country_bounds.lower() == country.lower():
                #print('Countries are equals :D')
                data_new = lookupInternetDevicesByCode(progress_devices, country)
                data_old = lookupInternetDevicesByCode(original_devices, country)

                if data_new is None:
                    #print('Connected devices data not available for this country, or are already been used, retry!!\t Country: ' + str(country))
                    return None
                else:
                    checkProgress(data_new, data_old, country)
                    return name

            else:
                #print('Countries are different !! ' + str(country_bounds) + ' ## ' + str(country))
                #print(str(country_bounds) + ': ' + str(progress_devices[country_bounds]['bounds']))
                #print(str(country) + ': ' + str(progress_devices[country]['bounds']))
                return None

    return name

def checkProgress(data_new, data_old, country):
    global progress_devices
    devices_new = data_new['devices'] - 1
    
    if devices_new == 0:
        print('Device from \"' + country + '\". IT WAS THE LAST.')
        del progress_devices[country]
        countries_left = [left for left in progress_devices]
        print(countries_left)

    else:
        progress_devices[country]['devices'] = devices_new

        perc_old = progress_devices[country]['perc']
        perc_new = float(devices_new) / float(data_old['devices'])
        
        if perc_old * 100 - perc_new * 100 >= 1:
            progress_devices[country]['perc'] = perc_new
            perc_new_used = (1 - perc_new) * 100
            perc_old_used = (1 - perc_old) * 100
            print('Device from \"' + str(country) + '\". Used devices: ' + str(round(perc_new_used, 2)) + '%')

def check_for_errors():
    internet_data = loadInternetDevices()
    countries_target = [country for country in internet_data]
    
    countries_data = loadCountriesCodes()
    countries_names = [country for country in countries_data]

    found = False
    for name in countries_target:
        if name not in countries_names:
            for name_compare in countries_names:
                if name in name_compare:
                    found = True
                    break

            if not found:
                print(internet_data[name])
        else:
            found = True
            break

    return found

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


if __name__ == "__main__":
    global progress_devices, original_devices, devices_divider, timezone_cc
    global debug, debug_country
    
    progress_devices = dict()
    original_devices = dict()
    timezone_cc = dict()
    devices_divider = 100000
    total_devices = int(3404265884 // devices_divider) - 102

    debug = False
    debug_country = 'cf'

    internet_data = loadInternetDevices()
    timezone_cc = loadCountryCodeFromTimeZone()

    for country in internet_data:
        data = dict()
        devices = int(internet_data[country]['devices']) // devices_divider
        if devices > 0 and country != 'total':
            data['devices'] = devices
            data['bounds'] = internet_data[country]['bounds']
            data['perc'] = 1.0
            original_devices[internet_data[country]['code'].lower()] = data

    for country in internet_data:
        data = dict()
        devices = int(internet_data[country]['devices']) // devices_divider
        if devices > 0 and country != 'total':
            data['devices'] = devices
            data['bounds'] = internet_data[country]['bounds']
            data['perc'] = 1.0
            progress_devices[internet_data[country]['code'].lower()] = data

    print('Countries left: ' + str(len(progress_devices.keys())))
    print(progress_devices.keys())
    
    print('Generating graph...')
    print('Generating ' + str(total_devices) + ' nodes...')

    # Create a non-directed graph
    network = NX.Graph()
    
    # Add n nodes to the graph
    network.add_nodes_from(range(total_devices))
    network = init_nodes(network)
    network = add_nodes_positions(network)

    # Choose random 'patient zero'
    i = random.randint(0, len(network.nodes()))
    network.node[i]['state'] = INFECTED
    network.node[i]['role'] = ROLE_SPREAD
    network.node[i]['just_infected'] = True

    if DEBUG:
        print('Random \'patient zero\' chosen.')
        print('Node n.' + str(i))
        print('Time zone: ' + str(network.node[i]['time_zone']))
        print('---------------------------------------------')

    NX.write_gpickle(network, '../data/graph-data.p')