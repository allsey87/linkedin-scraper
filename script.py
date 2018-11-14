import requests
import re
import demjson
import csv

# constants
csv_header = ['Job ID', 'Title', 'URL', 'Company Name-Location']
base_url = 'https://www.linkedin.com'
job_search_url = '/jobs/search?keywords={0}&locationId={1}:0'
keyword = 'robotics'
country = 'nl'

# init database as an empty dictionary
database = {}

# TODO add fix for no initial file
# populate database with existing jobs from csv file
with open('database.csv', newline='') as csvfile:
    listings = csv.DictReader(csvfile)
    for listing in listings:
        database[int(listing['Job ID'])] = {
            'Title':listing['Title'],
            'URL':listing['URL'],
            'Company Name-Location':listing['Company Name-Location'],
        }

# init the search URL
current_url = job_search_url.format(keyword, country)

while current_url is not None:
    # fetch current URL
    response = requests.get(base_url + current_url)
    print('fetch:', base_url + current_url, response.status_code)
    if response.status_code != 200:
        print('warning: status code was not 200')
        break;
        
    # find the JSON data containing the listings on the current page
    pattern = re.compile('<code id="decoratedJobPostingsModule"><!--(.+?)--></code>')
    listings = {}
    for match in pattern.finditer(response.text):
        if 'decoratedJobPosting' in match.group(1):
            listings = demjson.decode(match.group(1))
            break

    if 'elements' in listings:
        # add listing to database if it doesn't already exist
        for listing in listings['elements']:
            if listing['decoratedJobPosting']['jobPosting']['id'] not in database:
                database[listing['decoratedJobPosting']['jobPosting']['id']] = {
                        'Title':listing['decoratedJobPosting']['jobPosting']['title'],
                        'URL':listing['viewJobCanonicalUrl'],
                        'Company Name-Location':listing['decoratedJobPosting']['companyName'] +
                            ' in ' + listing['decoratedJobPosting']['cityState'],
                }
        current_url = listings['paging']['links']['next']
    else:
        print('warning: fetched page did not contain json data')
        break;

# write the database back to the file
with open('output.csv', 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=csv_header)
    writer.writeheader()
    for job_id, job_desc in database.items():
        writer.writerow({'Job ID':job_id,
                         'Title':job_desc['Title'],
                         'URL':job_desc['URL'],
                         'Company Name-Location':job_desc['Company Name-Location']})

