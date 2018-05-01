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

def clean_country_codes():
    with open('../data/backup/wikipedia-countries-code-iso-utf.json', 'r') as origin:
        data = json.load(origin)

    result = dict()
    for item in data:
        country = item['Country name'].lower()
        
        result[country] = dict()
        result[country]['code'] = item['Code'].lower()
        result[country]['notes'] = item['Notes'].lower()

    print('Save the newly generated JSON to file...')
    with open('../data/backup/wikipedia-countries-code-iso-utf-cleaned.json', 'w') as dest:
        dest.write(json.dumps(result))

    print('Convert it to Pickle and save it to file...')
    with open('../data/backup/wikipedia-countries-code-iso-utf-cleaned.p', 'wb') as dest:
        pickle.dump(result, dest, protocol=pickle.HIGHEST_PROTOCOL)

    return result