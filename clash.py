# -*- coding: utf-8 -*-

# dev: Renato Aranha

import urllib.request
import json
import pandas as pd
import dateutil.parser
from datetime import timedelta

# Base API url
base_url = "https://api.clashroyale.com/v1"


def get_data(base_url, endpoint):
    """
    retrieve data by consulting API via an endpoint in base url
    :param base_url: base url of supercell clash royale api
    :param endpoint: endpoint of a specific topic
    :return:
    """
    with open("my_key") as f:
        my_key = f.read().rstrip("\n")
        request = urllib.request.Request(base_url + endpoint,
                                         None,
                                         {"Authorization": "Bearer %s" % my_key})
        response = urllib.request.urlopen(request).read().decode("utf-8")
        data = json.loads(response)
    return data


# ================================
# GET RIVER RACE INFORMATION
# ================================

data = get_data(base_url, '/clans/%23PRP2UCY8/riverracelog')
raceRank = pd.json_normalize(data['items'], 'standings').drop(columns=['clan.participants', 'clan.tag'])
raceRank['clan.finishTime'] = raceRank['clan.finishTime'].apply(
    lambda x: dateutil.parser.parse(x).strftime('%d/%m/%Y %H:%M:%S') if not pd.isna(x) else x)

raceClanLog = pd.DataFrame(data['items'][0]['standings'][2]['clan']['participants']).sort_values('fame',
                                                                                                 ascending=False).drop(
    columns=['tag'])

# ================================
# GET CLAN MEMBERS INFORMATION
# ================================

data = get_data(base_url, '/clans/%23PRP2UCY8/members')
members = pd.json_normalize(data, 'items').drop(columns=['arena.id', 'clanChestPoints'])
members['lastSeen'] = members['lastSeen'].apply(
    lambda x: (dateutil.parser.parse(x) - timedelta(hours=3)).strftime('%d/%m/%Y %H:%M:%S'))
members['tag'] = members['tag'].apply(lambda x: x.replace('#', '%23'))

list_player_info = []
for i in members.tag:
    end = '/players/' + i
    data = get_data(base_url, end)
    player_info = pd.json_normalize(data).drop(
        columns=['badges', 'achievements', 'cards', 'currentDeck', 'currentFavouriteCard.id',
                 'currentFavouriteCard.iconUrls.medium'])
    list_player_info.append(player_info)

player_info = pd.concat(list_player_info).sort_values('trophies', ascending=False)

# ================================
# GET SPECIFIC PLAYER INFORMATION
# ================================

# get cards and deck
data = get_data(base_url, '/players/%2382PCLVYR')
player_cards = pd.json_normalize(data, 'cards').drop(columns=['id', 'iconUrls.medium']).sort_values(
    ['count', 'maxLevel'], ascending=False)
player_deck = pd.json_normalize(data, 'currentDeck').drop(columns=['id', 'iconUrls.medium']).sort_values(
    ['count', 'maxLevel'], ascending=False)

# get battle log
data = get_data(base_url, '/players/%2382PCLVYR/battlelog')
battle = pd.json_normalize(data)
battle['battleTime'] = battle['battleTime'].apply(
    lambda x: (dateutil.parser.parse(x) - timedelta(hours=3)).strftime('%d/%m/%Y %H:%M:%S'))

t = pd.json_normalize(data, 'team').explode('cards')
o = pd.json_normalize(data, 'opponent').explode('cards')

tcards = t.cards.apply(pd.Series).rename(columns={'name': 'card'})
ocards = o.cards.apply(pd.Series).rename(columns={'name': 'card'})

t = pd.concat([t, tcards], axis=1).add_prefix('t_')
o = pd.concat([o, ocards], axis=1).add_prefix('o_')

battle_log = pd.concat([battle, t, o], axis=1)
battle_log = battle_log.drop(columns=['o_cards', 't_cards', 'team', 'opponent', 't_iconUrls', 'o_iconUrls'])
battle_log = battle_log.reset_index()
