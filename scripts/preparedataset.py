import unidecode
import os
import csv
import simplejson as json
import pickle
import re

import pycountry

import time
import googlemaps


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

def loadCountriesCodes():
    with open('../data/country-code.p', 'rb') as origin:
        data = pickle.load(origin)

    return data

def loadCountryCodeFromTimeZone():
    with open('../data/tzdb-list-tz-cleaned.p', 'rb') as origin:
        data = pickle.load(origin)

    return data


if __name__ == "__main__":
