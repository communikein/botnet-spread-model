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
def add_country_codes_to_wikipedia_devices_country():
    data = dict()

    # Read data from CSV and convert to JSON
    fieldNames = ('country', 'devices', 'percentage')
    with open('../data/backup/internet-usage-data.csv', 'r') as f:
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

    print('Save the newly generated JSON to file...')
    with open('../data/backup/internet-usage-data-country-codes.json', 'w') as dest:
        dest.write(json.dumps(data))

    print('Convert it to Pickle and save it to file...')
    with open('../data/backup/internet-usage-data-country-codes.p', 'wb') as dest:
        pickle.dump(data, dest, protocol=pickle.HIGHEST_PROTOCOL)

    return data

def initGoogleMaps(api_key):
    gmaps = googlemaps.Client(key=api_key)

    return gmaps

# !!!!!!!!!!! THIS METHOD USES GOOGLE APIs, IT MIGHT REQUIRE PAYMENT
def add_countries_boundaries(gmaps):
    with open('../data/backup/internet-usage-data-country-codes.p', 'rb') as origin:
        data = pickle.load(origin)

    for country_name in data:
        if 'total' != country_name and 'bounds' not in data[country_name]:
            geocode_result = gmaps.geocode(country_name)
            
            print('Country: ' + str(country_name))
            if 'bounds' in geocode_result[0]['geometry']:
                data[country_name]['bounds'] = geocode_result[0]['geometry']['bounds']
                print(country_name + ' boundaries: ' + str(data[country_name]['bounds']))
            else:
                print('Error, country not recognised!')
            time.sleep(1)

    print('Save the newly generated JSON to file...')
    with open('../data/backup/internet-usage-data-bounds.json', 'w') as dest:
        dest.write(json.dumps(data))

def clean_internet_devices_data():
    with open('../data/backup/internet-usage-data-final.json', 'r') as origin:
        data = json.load(origin)

    result = dict()
    for entry in data:
        code = data[entry]['code']
        if code == ' ':
            code = 'TOTAL'

        result[code] = dict()
        result[code]['bounds'] = data[entry]['bounds']
        result[code]['devices'] = data[entry]['devices']

    print('Save the newly generated JSON to file...')
    with open('../data/backup/internet-usage-data-final.json', 'w') as dest:
        dest.write(json.dumps(result))

    print('Convert it to Pickle and save it to file...')
    with open('../data/internet-usage-data-final.p', 'wb') as dest:
        pickle.dump(result, dest, protocol=pickle.HIGHEST_PROTOCOL)


def pycountry_lookup(name):
    try:
        return pycountry.countries.lookup(name)
    except:
        return None

def clean_time_zone_country_codes():
    with open('../data/backup/wikipedia-tzf-list-tz-utf.json', 'r') as origin:
        data = json.load(origin)

    result = dict()
    for entry in data:
        notes = entry['Notes']
        
        new_entry = None
        if entry['CC'] == '' and 'link to ' in notes.lower():
            new_entry = get_linked_time_zone(entry, data)
        if new_entry is not None:
            entry = new_entry

        country_code = entry['CC'].lower()
        if '|' in entry['TZ']:
            tzs = entry['TZ'].split('|')

            for tz in tzs:
                result[tz] = entry['CC'].lower()
        else: 
            result[entry['TZ']] = entry['CC'].lower()

    print('Save the newly generated JSON to file...')
    with open('../data/backup/wikipedia-tzf-list-tz-cleaned.json', 'w') as dest:
        dest.write(json.dumps(result))

    print('Convert it to Pickle and save it to file...')
    with open('../data/tzf-list-tz-final.p', 'wb') as dest:
        pickle.dump(result, dest, protocol=pickle.HIGHEST_PROTOCOL)

def get_linked_time_zone(entry, data):
    notes = entry['Notes']
    new_time_zone_name = notes[notes.lower().index('link to') + len('link to ') : ]
    
    for temp in data:
        if temp['TZ'] == new_time_zone_name:
            new_entry = temp

            if new_entry['CC'] == '' and 'link to' in new_entry['Notes'].lower():
                return get_linked_time_zone(new_entry)
            else:
                return new_entry


if __name__ == "__main__":
    clean_time_zone_country_codes()

    with open('../data/tzf-list-tz-final.p', 'rb') as origin:
        data = pickle.load(origin)

    if 'Africa/Libreville' in data:
        print('Africa/Libreville')
    if 'Africa/Bangui' in data:
        print('Africa/Bangui')