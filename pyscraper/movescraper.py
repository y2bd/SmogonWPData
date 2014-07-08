import requests
import json

def get_movelist():
    url = 'http://www.smogon.com/dex/api/query'
    payload = {'q' : '{"move":{"gen":"xy"},"$":["name","alias","gen","category","power","accuracy","pp","description",{"type":["alias","name","gen"]}]}'}

    response = requests.get(url, params=payload)

    return response.json()['result']

def to_schmogon_movedata(move):
    print 'converting ' + move['name']

    return {'Competitive' : [],
            'Description' : [{'Content' : move['description']}],
            'Name' : move['name'],
            'RelatedMoves' : [],
            'Stats' : {'Accuracy' : val_or_blank(str(move['accuracy']), '0'),
                       'Damage' : move['category'],
                       'PP' : move['pp'],
                       'Power' : val_or_blank(str(move['power']), '0'),
                       'Priority' : '-',
                       'Target' : '-',
                       'Type' : move['type']['name']
                      }
           }

def val_or_blank(val, should_blank):
    return '-' if val == should_blank else val

def fetch_moves():
    return map(to_schmogon_movedata, get_movelist())

def type_to_number(type_):
    type_ = type_.lower()
    return ['normal', 'fire', 'water', 'electric', 'grass', 'ice', 'fighting', 'poison',
            'ground', 'flying', 'psychic', 'bug', 'rock', 'ghost', 'dragon', 'dark',
            'steel', 'fairy'].index(type_)

def minimize(pokedata):
    return {'Description' : pokedata['Description'][0]['Content'],
            'Name' : pokedata['Name'],
            'PageLocation' : '',
            'Type' : type_to_number(pokedata['Stats']['Type'])}

if __name__ == '__main__':
    mdj = open('movedata.json', 'w')
    movedata = fetch_moves()
    mdj.write(json.dumps(movedata))
    
    mj = open('moves.json', 'w')
    mj.write(json.dumps(map(minimize, movedata)))
    
    mdj.close()
    mj.close()


