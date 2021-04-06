#################################
##### Name:Zirong Chi
##### Uniqname:zirongch
#################################

from bs4 import BeautifulSoup
import requests
import json
import secrets  # file that contains your API key

abbreviations = {'al': 'Alabama', 'ak': 'Alaska', 'as': 'American Samoa', 'az': 'Arizona', 'ar': 'Arkansas',
                 'ca': 'California', 'co': 'Colorado', 'ct': 'Connecticut', 'de': 'Delaware',
                 'dc': 'District of Columbia',
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

    def __init__(self, category, name, address, zipcode, phone, url):
        self.category = category
        self.name = name
        self.address = address
        self.zipcode = zipcode
        self.phone = phone
        self.url = url

    def info(self):
        return self.name + " (" + self.category + "): " + self.address + " " + self.zipcode

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
        category = "no category" if category is None else category
        address1 = detail_soup.find('span', itemprop='addressLocality').text
        address1 = "no local address" if address1 is None else address1
        address2 = detail_soup.find('span', itemprop='addressRegion').text
        address2 = "no regional address" if address2 is None else address2
        address = address1 + ", " + address2
        zipcode = detail_soup.find('span', itemprop='postalCode').text.strip()
        zipcode = "no zipcode" if zipcode is None else zipcode
        phone = detail_soup.find('span', itemprop='telephone').text.strip()
        phone = "no phone" if zipcode is None else phone
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
    park_list = state_soup.find('ul', id='list_parks')
    sites_content = park_list.find_all('li', class_='clearfix')
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


def print_with_delimiter(str):
    print("-" * 35)
    print(str)
    print("-" * 35)


def is_valid(choose_num, len):
    if int(choose_num) < 0:
        return False
    if int(choose_num) > len:
        return False
    return True

def storeToDict(site_for_state,state,CACHE_DICTION,info,site_urls):
    CACHE_DICTION[state] = {}
    CACHE_DICTION[state]["info"] = info
    CACHE_DICTION[state]["site_urls"] = site_urls

def interactive():
    while True:
        site_results = []
        command = input(f'\nEnter a state name (e.g. Michigan, michigan) or "exit": ')
        if command == "exit":
            return
        elif command.lower() not in build_state_url_dict():
            print("[Error] Enter proper state name")
            continue
        else:
            try:
                info = CACHE_DICTION[command]["info"]
                for i in info:
                    print('Using Cache')
            except:
                info = []
                site_url_list = []
                url = build_state_url_dict()[command]
                sites_for_state = get_sites_for_state(url)
                for i in sites_for_state:
                    info.append(i.info())
                    site_url_list.append(i.url)
                    print("Fetching")
                # cache
                storeToDict(sites_for_state, command, CACHE_DICTION, info, site_url_list)
                # save cache:
                dumped_json_cache = json.dumps(CACHE_DICTION)
                fw = open(CACHE_FNAME, "w")
                fw.write(dumped_json_cache)
                fw.close()
                # save cache end
            print_with_delimiter("List of national sites in " + command)
            for i in range(len(info)):
                print("[" + str(i + 1) + "]" + info[i])
            while True:
                choose_num = input("Choose the number for detail search or \"exit\" or \"back\" ")
                if choose_num == "exit":
                    return
                elif choose_num == "back":
                    interactive()
                    break
                elif is_valid(choose_num, len(CACHE_DICTION[command]["info"])):
                    site_instance = get_site_instance(CACHE_DICTION[command]["site_urls"][int(choose_num) - 1])
                    try:
                        nearby_place = CACHE_DICTION[command][site_instance.name]
                        print("Using cache")
                    except:
                        CACHE_DICTION[command][site_instance.name] = {}
                        nearby_place = get_nearby_places(site_instance)
                        CACHE_DICTION[command][site_instance.name] = nearby_place["searchResults"]
                        dumped_json_cache = json.dumps(CACHE_DICTION)
                        fw = open(CACHE_FNAME, "w")
                        fw.write(dumped_json_cache)
                        fw.close()
                        print("Fetching")
                    print_with_delimiter("Places near " + site_instance.name)
                    for i in CACHE_DICTION[command][site_instance.name]:
                        category = "no category" if i["fields"]["group_sic_code_name_ext"] == '' else i["fields"][
                            "group_sic_code_name_ext"]
                        address = "no address" if i["fields"]["address"] == '' else i["fields"]["address"]
                        city = "no city" if i["fields"]["city"] == '' else i["fields"]["city"]
                        name = i["name"]
                        print("-" + name + " (" + category + "): " + address + ", " + city)
                        continue
                else:
                    print("[Error]")
                    continue
                break


if __name__ == "__main__":
    interactive()
