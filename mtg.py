#!/usr/bin/env python3

# TODO nephilim
# http://mtg.gamepedia.com/Nephilim

import re
import os
import json
import requests
import time
import functools


def normtype(name):
    """Standardize type field from cubetutor output."""
    name = name.lower()
    if name == 'artifact_creature':
        name = 'creature'
    return name


def create_tests():
    """Create tests asserting the validity of current state."""
    print("import mtg\n")
    for f in Faction.all_factions:
        print("assert(mtg.Faction.who_can_play('{}') == {})".
              format(f, Faction.who_can_play(f)))
    # Test colorless (Eldrazi) mana
    print("assert(mtg.Faction.who_can_play('{8}{C}{C}') == set())")
    # Test strange hybrids (colorless/phyrexian mana)
    print("assert(mtg.Faction.who_can_play('{{1}}{{P/C}}') == {})".
          format(Faction.all_factions))


def show_guild_numbers():
    for c in range(0, 10):
        print("{} {}".format(c, Faction.g[c]))


class Faction:

    # faction lists
    c = ['white', 'blue', 'black',  'red', 'green']
    g = ['azorius', 'boros', 'dimir',
         'golgari', 'gruul', 'izzet',
         'orzhov', 'rakdos', 'selesnya', 'simic']
    s = ['bant', 'naya', 'grixis', 'esper', 'jund']
    w = ['abzan', 'jeskai', 'mardu', 'sultai', 'temur']

    # plot color
    pc = {c[0]: 'gray', c[1]: 'blue', c[2]: 'black',
          c[3]: 'red', c[4]: 'green'
          }

    all_factions = frozenset(c + g + s + w)

    # guilds include these colors
    gm = {
        g[0]: {c[0], c[1]}, g[1]: {c[0], c[3]},
        g[2]: {c[1], c[2]}, g[3]: {c[2], c[4]},
        g[4]: {c[3], c[4]}, g[5]: {c[1], c[3]},
        g[6]: {c[0], c[2]}, g[7]: {c[2], c[3]},
        g[8]: {c[0], c[4]}, g[9]: {c[1], c[4]}
        }
    # shards include these colors
    sm = {
        s[0]: {c[0], c[1], c[4]},
        s[1]: {c[0], c[3], c[4]},
        s[2]: {c[1], c[2], c[3]},
        s[3]: {c[0], c[1], c[2]},
        s[4]: {c[2], c[3], c[4]}
        }

    # wedges include these colors
    wm = {
        w[0]: {c[0], c[2], c[4]},
        w[1]: {c[0], c[1], c[3]},
        w[2]: {c[0], c[2], c[3]},
        w[3]: {c[1], c[2], c[4]},
        w[4]: {c[1], c[3], c[4]}
        }

    # shards include these guilds
    sgm = {
        s[0]: {g[0], g[8], g[9]},
        s[1]: {g[1], g[8], g[4]},
        s[2]: {g[2], g[5], g[7]},
        s[3]: {g[0], g[2], g[6]},
        s[4]: {g[3], g[4], g[7]}
        }

    # wedges include these guilds
    wgm = {
        w[0]: {g[3], g[6], g[8]},
        w[1]: {g[0], g[1], g[5]},
        w[2]: {g[1], g[6], g[7]},
        w[3]: {g[2], g[3], g[9]},
        w[4]: {g[4], g[5], g[9]}
        }

    # color shorthand
    csh = {'w': c[0], 'u': c[1], 'b': c[2], 'r': c[3], 'g': c[4]}

    # we don't need this
    def reverse_guild_map():
        """Generates the reverse guild map"""
        Faction.rgm = dict()
        for k, v in Faction.gm.items():
            Faction.rgm[frozenset(v)] = k

    def colorname(name):
        """Standardize color names from cubetutor output."""
        name = name.lower()
        if name.startswith('mono_'):
            name = name[5:]
        if name in 'wubrg':
            name = Faction.csh[name]
        return name

    def colors(faction):
        faction = Faction.colorname(faction)

        if faction in Faction.g:
            r = Faction.gm[faction]
        elif faction in Faction.s:
            r = Faction.sm[faction]
        elif faction in Faction.w:
            r = Faction.wm[faction]
        elif faction in Faction.c:
            r = [faction]

        elif faction == 'colourless':
            r = Faction.c

        else:
            print(faction)

        return set(r)

    @functools.lru_cache(maxsize=200)
    def who_can_play(cost):
        # Start by assuming anyone can play anything
        can_play = set(Faction.all_factions)
        costs = re.findall('([^{^}]+)', cost)

        for subcost in costs:
            # Eldrazi mana
            if subcost == 'C':
                can_play = set()

            elif re.search('\d+|P|X', subcost) is not None:
                # print("Anyone can pay this subcost, moving on")
                continue

            # hybrid mana
            elif '/' in subcost:
                hybrid_colors = set([Faction.colorname(h) for h in
                                     subcost.split('/')])

                # who can pay this particular subcost?
                sub_sub_cost = set()
                for color in hybrid_colors:
                    sub_sub_cost.update(Faction.member_of(color))

                can_play.intersection_update(sub_sub_cost)

            # Single color
            else:
                # print("Who can play {}? Why, {} of course!"
                # .format(subcost, Faction.member_of(subcost)))
                subcost = Faction.colorname(subcost)
                can_play.intersection_update(Faction.member_of(subcost))

        return can_play

    def member_of(faction):
        faction = Faction.colorname(faction)

        # this color is a member of these shards
        m = {k for k, v in Faction.sm.items() if faction in v}

        # this color is a member of these guilds
        m = set.union(m, {k for k, v in Faction.gm.items() if faction in v})

        # this color is a member of these wedges
        m = set.union(m, {k for k, v in Faction.wm.items() if faction in v})

        # this guild is a member of these shards
        m = set.union(m, {k for k, v in Faction.sm.items() if faction in
                          Faction.sgm[k]})

        # this guild is a member of these wedges
        m = set.union(m, {k for k, v in Faction.wm.items() if faction in
                          Faction.wgm[k]})

        # always a member of itself
        m = set.union(m, {faction})

        return m


class Cards():
    def __init__(self, path=None):

        # save and load data here
        if path:
            self.path = path
            if os.path.isfile(path):
                with open(path, 'r') as db_file:
                    self.db = json.loads(db_file.read())
            else:
                self.db = dict()

        # temporary database
        else:
            self.db = dict()
            self.path = None

    def add_card(self, name, api_url='https://api.deckbrew.com'):
        """Download card data by name from deckbrew and
        add it to the card database. Since all we have is the name,
        just save the first result, which should be representative
        for the card mechanics. Skips downloading cards that are
        already in the database."""

        if name not in self.db.keys():
            print("Fetching {}".format(name))
            query = api_url + '/mtg/cards?name=' + name

            time.sleep(.1)  # FIXME basic rate limiting
            r = requests.get(query)
            if r.status_code == 200:
                self.db[name] = json.loads(r.text)[0]
            else:
                raise OSError.ConnectionError("Error communicating with API: \
                                      status code {}".format(r.status_code))

    def save(self):
        if self.path:
            with open(self.path, 'w') as db_file:
                db_file.write(json.dumps(self.db))

    def show_guild_numbers():
        """Debugging function"""
        for c in range(0, 10):
            print("{} {}".format(c, Faction.g[c]))
