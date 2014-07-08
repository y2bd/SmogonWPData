import requests
import json

def get_itemlist():
    url = 'http://www.smogon.com/dex/api/query'
    payload = {'q' : '{"item":{"gen":"xy"},"$":["name","alias","gen","description"]}'}

    response = requests.get(url, params=payload)

    return response.json()['result']

def to_schmogon_itemdata(item):
    print 'converting ' + item['name']

    return {'Competitive' : [],
            'Description' : [{'Content' : item['description']}],
            'Name' : item['name']}

def minimize(pokedata):
    return {'Description' : pokedata['Description'][0]['Content'],
            'Name' : pokedata['Name'],
            'PageLocation' : ''}

def fetch_itemities():
    return map(to_schmogon_itemdata, get_itemlist())

if __name__ == '__main__':
    mdj = open('itemdata.json', 'w')
    itemdata = fetch_itemities()
    mdj.write(json.dumps(itemdata))
    
    mj = open('items.json', 'w')
    mj.write(json.dumps(map(minimize, itemdata)))
    
    mdj.close()
    mj.close()