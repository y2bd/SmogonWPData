import requests
import json

def get_abillist():
    url = 'http://www.smogon.com/dex/api/query'
    payload = {'q' : '{"ability":{"gen":"xy"},"$":["name","alias","gen","description"]}'}

    response = requests.get(url, params=payload)

    return response.json()['result']

def to_schmogon_abildata(abil):
    print 'converting ' + abil['name']

    return {'Competitive' : [],
            'Description' : [{'Content' : abil['description']}],
            'Name' : abil['name']}

def minimize(pokedata):
    return {'Description' : pokedata['Description'][0]['Content'],
            'Name' : pokedata['Name'],
            'PageLocation' : ''}

def fetch_abilities():
    return map(to_schmogon_abildata, get_abillist())

if __name__ == '__main__':
    mdj = open('abildata.json', 'w')
    abildata = fetch_abilities()
    mdj.write(json.dumps(abildata))
    
    mj = open('abilities.json', 'w')
    mj.write(json.dumps(map(minimize, abildata)))
    
    mdj.close()
    mj.close()