import requests
from bs4 import BeautifulSoup
from multiprocessing import Pool
import multiprocessing
import json

def get_pokelist():
    url = 'http://www.smogon.com/dex/api/query'
    payload = {'q' : '{"pokemonalt":{"gen":"xy"},"$":["name","alias","base_alias","gen",{"types":["alias","name","gen"]},{"abilities":["alias","name","gen"]},{"tags":["name","alias","shorthand","gen"]},"weight","height","hp","patk","pdef","spatk","spdef","spe"]}'}

    response = requests.get(url, params=payload)

    return uniqify(lambda e: e['base_alias'], response.json()['result'])

def get_pokemon(alias):
    print 'fetching ' + alias

    url = 'http://www.smogon.com/dex/api/query'
    payload = {'q' : '{"pokemon":{"gen":"xy","alias":"' + alias + '"},"$":["name","alias","gen",{"genfamily":["alias","gen"]},{"alts":["alias","suffix","height","weight","gkpower",{"types":["alias","name","gen"]},{"$groupby":"modifier","effectives":["modifier",{"type":["alias","name","gen"]}]},{"abilities":["alias","name","gen","description"]},{"tags":["name","alias","shorthand","gen"]},"hp","patk","pdef","spatk","spdef","spe"]},{"family":["root",{"members":["name","alias","gen"]},{"evolutions":["preevo","evo"]}],"$tree":["root",["members","name"],["evolutions","preevo","evo"]]},{"movesets":["name",{"tags":["alias","shorthand","name","gen"]},{"items":["alias","name","gen","description"]},{"abilities":["alias","name","gen"]},{"evconfigs":["hp","patk","pdef","spatk","spdef","spe"]},{"natures":["hp","patk","pdef","spatk","spdef","spe"]},{"$groupby":"slot","moveslots":["slot",{"move":["name","alias","gen"]}]},"description"]},{"moves":["name","alias","gen","category","power","accuracy","pp","description",{"type":["alias","name","gen"]}]}]}'}

    response = requests.get(url, params=payload)
    as_json = response.json()

    if as_json['status'] != 'success':
        raise ValueError('Invalid JSON D:')

    return as_json['result'][0]

def uniqify(keyfunc, collection):
    d = {}
    for elem in collection:
        k = keyfunc(elem)
        if k not in d:
            d[k] = elem

    return d.values()

def fetch_all_pokemon_threaded():
    all_pokemon = []
    poke_aliases = [p['alias'] for p in get_pokelist()]
    print 'fetched aliases'

    print 'starting pool'
    pool = Pool(processes=4)
    all_pokemon = pool.map(get_pokemon, poke_aliases)
    pool.close()

    return all_pokemon

def to_pokedata(poke):
    data = {'name' : '',
            'alias' : '',
            'type' : [],
            'tier' : 0,
            'has_movesets' : False,
            'data' : {}}

    forms = filter(lambda a: len(a['tags']) > 0, poke['alts'])

    if len(forms) <= 0:
        main_form = pokemon['alts'][0]
        data['tier'] = tier_to_number('LIMBO')
    else:
        main_form = forms[0]
        data['tier'] = tier_to_number(main_form['tags'][0]['shorthand'])

    data['name'] = poke['name']
    data['alias'] = poke['alias']
    data['type'] = get_types(main_form['types'])

    in_data = {'forms' : [],
               'moves' : [],
               'movesets' : []}

    in_data['moves'] = get_moves(poke['moves'])
    in_data['movesets'] = get_movesets(poke['movesets'])
    in_data['forms'] = get_forms(forms)

    data['data'] = in_data
    data['has_movesets'] = len(in_data['movesets']) > 0

    return data

def get_abilities(abil):
    return [{'name' : a['name'],
             'alias' : a['alias']} for a in abil]

def get_types(types):
    return [type_to_number(t['name']) for t in types]

def get_moves(moves):
    return [{'name' : m['name'], 
             'alias' : m['alias'],
             'description' : m['description']} for m in moves]

def get_items(items):
    return [{'name' : i['name'],
             'alias' : i['alias']} for i in items]

def get_stats(alt):
    return {'atk' : alt['patk'],
            'def' : alt['pdef'],
            'hp' : alt['hp'],
            'spatk' : alt['spatk'],
            'spdef' : alt['spdef'],
            'spe' : alt['spe']}

def get_forms(fms):
    return [{'stats' : get_stats(f),
             'type' : get_types(f['types']),
             'abilities' : get_abilities(f['abilities']),
             'alias' : f['alias'],
             'suffix' : f['suffix']} for f in fms]

def type_to_number(type_):
    type_ = type_.lower()
    return ['normal', 'fire', 'water', 'electric', 'grass', 'ice', 'fighting', 'poison',
            'ground', 'flying', 'psychic', 'bug', 'rock', 'ghost', 'dragon', 'dark',
            'steel', 'fairy'].index(type_)

def tier_to_number(tier):
    tier = tier.upper()
    return ['UBER', 'OU', 'BL', 'UU', 'BL2', 'RU', 'BL3', 'NU', 'LC', 'LIMBO', 'NFE', 'UNRELEASED'].index(tier)

def natconfig_to_number(nc):
    natures = ['21011',
               '11111',
               '02111',
               '21110',
               '01121',
               '11021',
               '11111',
               '10121',
               '11111',
               '10112',
               '12011',
               '11012',
               '12101',
               '20111',
               '10211',
               '01211',
               '11102',
               '21101',
               '11210',
               '11111',
               '11201',
               '12110',
               '11120',
               '11111',
               '01112']

    tol = [nc['patk'], nc['pdef'], nc['spatk'], nc['spdef'], nc['spe']]
    conv = ''.join(('2' if t==1.1 else ('0' if t==0.9 else '1')) for t in tol)

    return natures.index(conv)

def get_movesets(movesets):
    return [extract_moveset(ms) for ms in movesets]

def extract_moveset(ms):
    ems = {'abilities' : [],
           'description' : [],
           'evs' : {},
           'items' : [],
           'moves' : [],
           'name' : ms['name'],
           'natures' : []}

    ems['evs'] = get_stats(ms['evconfigs'][0])
    ems['abilities'] = get_abilities(ms['abilities'])
    ems['items'] = get_abilities(ms['items'])
    ems['moves'] = [[{'name' : m['name'], 'alias' : m['alias']} for m in msl['moves']] for msl in ms['moveslots']]
    ems['natures'] = [natconfig_to_number(ncf) for ncf in ms['natures']]
    ems['description'] = extract_moveset_description(ms['description'])

    return ems

def extract_moveset_description(description):
    soup = BeautifulSoup(description)

    return [{'text' : p.text,
             'type' : ['h4', 'p', 'li'].index(p.name)} 
                for p in soup.descendants if p.name in ['p', 'li', 'h4']]

if __name__ == '__main__':
    multiprocessing.freeze_support()

    pdj = open('pokedata.json', 'w')
    pokedata = [to_pokedata(p) for p in fetch_all_pokemon_threaded()]
    pdj.write(json.dumps(pokedata))
    pdj.close()