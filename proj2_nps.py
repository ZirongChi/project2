#################################
##### Name:
##### Uniqname:
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets # file that contains your API key

abbreviations = {'al': 'Alabama', 'ak': 'Alaska', 'as': 'American Samoa', 'az': 'Arizona', 'ar': 'Arkansas',
                 'ca': 'California', 'co': 'Colorado', 'ct': 'Connecticut', 'de': 'Delaware', 'dc': 'District of Columbia',
                 'fl': 'Florida', 'ga': 'Georgia', 'gu': 'Guam', 'hi': 'Hawaii', 'id': 'Idaho', 'il': 'Illinois',
                 'in': 'Indiana', 'ia': 'Iowa', 'ks': 'Kansas', 'ky': 'Kentucky', 'la': 'Louisiana', 'me': 'Maine',
                 'md': 'Maryland', 'ma': 'Massachusetts', 'mi': 'Michigan', 'mn': 'Minnesota', 'ms': 'Mississippi',
                 'mo': 'Missouri', 'mt': 'Montana', 'ne': 'Nebraska', 'nv': 'Nevada', 'nh': 'New Hampshire',
                 'nj': 'New Jersey', 'nm': 'New Mexico', 'ny': 'New York', 'nc': 'North Carolina', 'nd': 'North Dakota',
                 'mp': 'Northern Mariana Islands', 'oh': 'Ohio', 'ok': 'Oklahoma', 'or': 'Oregon', 'pa': 'Pennsylvania',
                 'pr': 'Puerto Rico', 'ri': 'Rhode Island', 'sc': 'South Carolina', 'sd': 'South Dakota',
                 'tn': 'Tennessee', 'tx': 'Texas', 'ut': 'Utah', 'vt': 'Vermont', 'vi': 'Virgin Islands',
                 'va': 'Virginia', 'wa': 'Washington', 'wv': 'West Virginia', 'wi': 'Wisconsin', 'wy': 'Wyoming'}



class NationalSite():
    '''a national site

    Instance Attributes
    -------------------
    category: string
        the category of a national site (e.g. 'National Park', '')
        some sites have blank category.
    
    name: string
        the name of a national site (e.g. 'Isle Royale')

    address: string
        the city and state of a national site (e.g. 'Houghton, MI')

    zipcode: string
        the zip-code of a national site (e.g. '49931', '82190-0168')

    phone: string
        the phone of a national site (e.g. '(616) 319-7906', '307-344-7381')
    '''
    def __init__(self, category, name, address,zipcode, phone,url):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone
        self.url = url
    def info(self):
        return (self.name + " (" + self.category + "): " + self.address + " " + self.zipcode)

    pass


def build_state_url_dict():
    ''' Make a dictionary that maps state name to state page url from "https://www.nps.gov"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a state name and value is the url
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''
    state_text = requests.get("https://www.nps.gov/findapark/index.htm")
    state_soup = BeautifulSoup(state_text.text, 'html.parser')
    park_list = state_soup.find('map')
    sites_content = park_list.find_all('area')
    sites_list = {}
    for s in sites_content:
        state = s['alt'].lower()
        url = s['href']
        sites_list[state] = "https://www.nps.gov" + url
    return sites_list


def get_site_instance(site_url):
    '''Make an instances from a national site URL.
    
    Parameters
    ----------
    site_url: string
        The URL for a national site page in nps.gov
    
    Returns
    -------
    instance
        a national site instance
    '''
    if site_url is not None:
        detail_text = make_request_using_cache(site_url)
        detail_soup = BeautifulSoup(detail_text, 'html.parser')
        name = detail_soup.find('a', class_="Hero-title").text
        category = detail_soup.find('span', class_='Hero-designation').text
        if category is None:
            category = "no category"
        address1 = detail_soup.find('span', itemprop='addressLocality').text
        if address1 is None:
            address1 = "no local address"
        address2 = detail_soup.find('span', itemprop='addressRegion').text
        if address2 is None:
            address2 = "no regional address"
        address = address1 + ", " + address2
        zipcode = detail_soup.find('span', itemprop='postalCode').text.strip()
        if zipcode is None:
            zipcode = "no zipcode"
        phone = detail_soup.find('span', itemprop='telephone').text.strip()
        if phone is None:
            phone = "no phone"
        instance = NationalSite(category, name, address, zipcode, phone, site_url)
    return instance

def get_sites_for_state(state_url):
    '''Make a list of national site instances from a state URL.
    
    Parameters
    ----------
    state_url: string
        The URL for a state page in nps.gov
    
    Returns
    -------
    list
        a list of national site instances
    '''
    state_text = requests.get(state_url)
    state_soup = BeautifulSoup(state_text.text, 'html.parser')
    park_list = state_soup.find('ul',id='list_parks')
    sites_content = park_list.find_all('li',class_='clearfix')
    sites_list = []
    for s in sites_content:
        site_name = s.find('h3')
        site_type = site_name.find('a')
        href = site_type['href']
        site_url = 'https://www.nps.gov/' + href
        site = get_site_instance(site_url)
        sites_list.append(site)
    return sites_list


def get_nearby_places(site_object):
    '''Obtain API data from MapQuest API.
    
    Parameters
    ----------
    site_object: object
        an instance of a national site
    
    Returns
    -------
    dict
        a converted API return from MapQuest API
    '''
    params = {'key': secrets.API_KEY, 'origin': site_object.zipcode, 'radius': 10, 'maxMatches': 10,
              'ambiguities': "ignore", 'outFormat': "json"}

    url = "http://www.mapquestapi.com/search/v2/radius"
    page = requests.get(url, params)
    return json.loads(page.text)

CACHE_FNAME = 'proj2_cache.json'
try:
    cache_file = open(CACHE_FNAME, 'r')
    cache_contents = cache_file.read()
    CACHE_DICTION = json.loads(cache_contents)
    cache_file.close()

# if there was no file, no worries. There will be soon!
except:
    CACHE_DICTION = {}

def get_unique_key(url):
    return url

def make_request_using_cache(url):
    unique_ident = get_unique_key(url)

    ## first, look in the cache to see if we already have this data
    if unique_ident in CACHE_DICTION:
        # print("Getting cached data...")
        return CACHE_DICTION[unique_ident]

    ## if not, fetch the data afresh, add it to the cache,
    ## then write the cache to file

    else:
        # print("Making a request for new data...")
        # Make the request and cache the new data
        resp = requests.get(url)
        CACHE_DICTION[unique_ident] = resp.text
        dumped_json_cache = json.dumps(CACHE_DICTION)
        fw = open(CACHE_FNAME, "w")
        fw.write(dumped_json_cache)
        fw.close()  # Close the open file
        return CACHE_DICTION[unique_ident]

def interactive():
    while True:
        site_results = []
        command = input(f'\nEnter a state name (e.g. Michigan, michigan) or "exit": ')
        words = command.split()
        abbreviations =build_state_url_dict()
        if command == "exit":
            return
        elif command not in abbreviations.keys():
            print("[Error] Enter proper state name")
            continue
        else:
            try:
                info = CACHE_DICTION[command]["state_info"]
                for i in info:
                    print('Using Cache')
            except:
                stateurl = abbreviations[command]
                statelist = get_sites_for_state(stateurl)
                statelist_info = []
                site_urls = []
                for i in statelist:
                    site_url = i.url
                    statelist_info.append(i.info())
                    site_urls.append(site_url)
                    print("Fetching")
                CACHE_DICTION[command] = {}
                CACHE_DICTION[command]["statelist_info"] = statelist_info
                CACHE_DICTION[command]["site_urls"] = site_urls
                #save cache:
                dumped_json_cache = json.dumps(CACHE_DICTION)
                fw = open(CACHE_FNAME, "w")
                fw.write(dumped_json_cache)
                fw.close()
if __name__ == "__main__":
    interactive()
