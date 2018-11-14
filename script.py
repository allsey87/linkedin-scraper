import csv, demjson, getopt, sys, requests, re 

def main():
    try:
        options, arguments = getopt.getopt(sys.argv[1:], "c:k:d:", ["country=", "keyword=", "database="])
    except getopt.GetoptError as err:
        print(err) # will print something like "option -a not recognized"
        sys.exit(1)
    # script configuration
    country = None
    keyword = None
    csv_database = None
    for option, argument in options:
        if option in ("-c", "--country"):
            country = argument
        elif option in ("-k", "--keyword"):
            keyword = argument
        elif option in ("-d", "--database"):
            csv_database = argument
        else:
            assert False, "invalid option specified"

    # check options
    if country is None:
        assert False, "country must be specified"
    if keyword is None:
        assert False, "keyword must be specified"

    # constants
    csv_header = ['Job ID', 'Title', 'URL', 'Company Name', 'Company Location', 'Date Posted']
    base_url = 'https://www.linkedin.com'
    job_search_url = '/jobs/search?keywords={0}&locationId={1}:0'

    # init database as an empty dictionary
    database = {}

    # populate database with existing jobs from csv file 
    if csv_database is not None:
       with open(csv_database, newline='') as csvfile:
            listings = csv.DictReader(csvfile)
            for listing in listings:
                database[int(listing['Job ID'])] = {
                    'Title':listing['Title'],
                    'URL':listing['URL'],
                    'Company Name':listing['Company Name'],
                    'Company Location':listing['Company Location'],
                    'Date Posted':listing['Date Posted'],
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
                            'Company Name':listing['decoratedJobPosting']['companyName'],
                            'Company Location':listing['decoratedJobPosting']['cityState'],
                            'Date Posted':listing['decoratedJobPosting']['formattedListDate'],
                    }
            current_url = listings['paging']['links']['next']
        else:
            print('warning: fetched page did not contain json data')
            break;

    # write the database back to the file
    if csv_database is None:
        csv_database = 'database' + '-' + keyword + '-' + country + '.csv'
    with open(csv_database, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_header)
        writer.writeheader()
        for job_id, job_desc in database.items():
            writer.writerow({'Job ID':job_id,
                             'Title':job_desc['Title'],
                             'URL':job_desc['URL'],
                             'Company Name':job_desc['Company Name'],
                             'Company Location':job_desc['Company Location'],
                             'Date Posted':job_desc['Date Posted']})


if __name__ == "__main__":
    main()

