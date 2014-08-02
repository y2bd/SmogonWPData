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
    url = 'http://www.smogon.com/dex/api/query'
    payload = {'q' : '{"pokemon":{"gen":"xy","alias":"' + alias + '"},"$":["name","alias","gen",{"genfamily":["alias","gen"]},{"alts":["alias","suffix","height","weight","gkpower",{"types":["alias","name","gen"]},{"$groupby":"modifier","effectives":["modifier",{"type":["alias","name","gen"]}]},{"abilities":["alias","name","gen","description"]},{"tags":["name","alias","shorthand","gen"]},"hp","patk","pdef","spatk","spdef","spe"]},{"family":["root",{"members":["name","alias","gen"]},{"evolutions":["preevo","evo"]}],"$tree":["root",["members","name"],["evolutions","preevo","evo"]]},{"movesets":["name",{"tags":["alias","shorthand","name","gen"]},{"items":["alias","name","gen","description"]},{"abilities":["alias","name","gen"]},{"evconfigs":["hp","patk","pdef","spatk","spdef","spe"]},{"natures":["hp","patk","pdef","spatk","spdef","spe"]},{"$groupby":"slot","moveslots":["slot",{"move":["name","alias","gen"]}]},"description"]},{"moves":["name","alias","gen","category","power","accuracy","pp","description",{"type":["alias","name","gen"]}]}]}'}

    response = requests.get(url, params=payload)
    as_json = response.json()

    return None if as_json['status'] != 'success' else as_json['result'][0]

def uniqify(keyfunc, collection):
    d = {}
    for elem in collection:
        k = keyfunc(elem)
        if k not in d:
            d[k] = elem

    return d.values()

def fetch_pokemon(alias):
    print 'fetching ' + alias

    pokemon = get_pokemon(alias)
    if pokemon is None: return None

    movesets = pokemon['movesets']

    print alias, str(len(movesets)) + ' movesets'

    return None if len(movesets) <= 0 else pokemon

def fetch_all_pokemon():
    all_pokemon = []
    poke_aliases = [p['alias'] for p in get_pokelist()]
    print 'fetched aliases'

    all_pokemon = map(fetch_pokemon, poke_aliases)

    return all_pokemon

def fetch_all_pokemon_threaded():
    all_pokemon = []
    poke_aliases = [p['alias'] for p in get_pokelist()]
    print 'fetched aliases'

    pool = Pool(processes=4)

    print 'starting pool'

    all_pokemon = pool.map(fetch_pokemon, poke_aliases)

    pool.close()

    return filter(lambda p : p is not None, all_pokemon)

def to_schmogon_pokedata(pokemon):
    pokedata = {'Abilities' : [],
                'BaseStats' : {},
                'ChecksAndCounters' : [],
                'Moves' : [],
                'Movesets' : [],
                'Name' : pokemon['name'],
                'OtherOptions' : [],
                'Overview' : [],
                'PageLocation' : '',
                'SpritePath' : '',
                'Tier' : 0,
                'Types' : []}

    alt_data_list = filter(lambda a: len(a['tags']) > 0, pokemon['alts'])

    if len(alt_data_list) <= 0:
        alt_data = pokemon['alts'][0]
        pokedata['Tier'] = tier_to_number('LIMBO')
    else:
        alt_data = alt_data_list[0]
        pokedata['Tier'] = tier_to_number(alt_data['tags'][0]['shorthand'])

    pokedata['BaseStats'] = get_stats(alt_data)
    pokedata['Abilities'] = get_abilities(alt_data['abilities'])
    pokedata['Types'] = get_types(alt_data['types'])
    pokedata['Moves'] = get_moves(pokemon['moves'])
    pokedata['Movesets'] = get_movesets(pokemon['movesets'])

    print 'converted ' + pokemon['name']

    return pokedata

def get_abilities(abil):
    return map(lambda a : {'Description' : '', 'Name' : a['name'], 'PageLocation' : ''}, abil)

def get_types(types):
    return [type_to_number(t['name']) for t in types]

def get_moves(moves):
    return [{'Name' : m['name'], 'Description' : m['description'], 'PageLocation' : ''} for m in moves]

def get_items(items):
    return [{'Name' : i['name'], 'Description' : '', 'PageLocation' : ''} for i in items]

def get_stats(alt):
    return {'Attack' : alt['patk'],
            'Defense' : alt['pdef'],
            'HP' : alt['hp'],
            'SpecialAttack' : alt['spatk'],
            'SpecialDefense' : alt['spdef'],
            'Speed' : alt['spe']}

def tier_to_number(tier):
    tier = tier.upper()
    return ['UBER', 'OU', 'BL', 'UU', 'BL2', 'RU', 'NU', 'LC', 'LIMBO', 'NFE'].index(tier)

def type_to_number(type_):
    type_ = type_.lower()
    return ['normal', 'fire', 'water', 'electric', 'grass', 'ice', 'fighting', 'poison',
            'ground', 'flying', 'psychic', 'bug', 'rock', 'ghost', 'dragon', 'dark',
            'steel', 'fairy'].index(type_)

def get_movesets(movesets):
    return [extract_moveset(ms) for ms in movesets]

def extract_moveset(ms):
    ems = {'Abilities' : [],
           'Description' : [],
           'EVSpread' : {},
           'Items' : [],
           'Moves' : [],
           'Name' : ms['name'],
           'Natures' : []}

    ems['EVSpread'] = get_stats(ms['evconfigs'][0])
    ems['Abilities'] = get_abilities(ms['abilities'])
    ems['Items'] = get_abilities(ms['items'])
    ems['Moves'] = [[{'Name' : m['name'], 'Description' : '', 'PageLocation' : ''} for m in msl['moves']] for msl in ms['moveslots']]
    ems['Natures'] = [natconfig_to_number(ncf) for ncf in ms['natures']]
    ems['Description'] = [{'Content' : p} for p in extract_moveset_description(ms['description'])]

    return ems

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

def extract_moveset_description(description):
    soup = BeautifulSoup(description)

    return [p.text for p in soup.descendants if p.name in ['p', 'li']]

def minimize(pokedata):
    return {'Abilities' : pokedata['Abilities'],
            'BaseStats' : pokedata['BaseStats'],
            'Name' : pokedata['Name'],
            'PageLocation' : pokedata['PageLocation'],
            'Tier' : pokedata['Tier'],
            'Types' : pokedata['Types']}

if __name__ == '__main__':
    multiprocessing.freeze_support()
    pdj = open('pokedata.json', 'w')
    pokedata = [to_schmogon_pokedata(p) for p in fetch_all_pokemon_threaded()]
    pdj.write(json.dumps(pokedata))
    pj = open('pokemon.json', 'w')
    pj.write(json.dumps(map(minimize, pokedata)))
    pdj.close()
    pj.close()



