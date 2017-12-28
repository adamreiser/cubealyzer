#!/usr/bin/env python3

import re
import os
import json
import requests
import time
import functools
import logging


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
    """Debugging function"""
    for c in range(0, 10):
        print("{} {}".format(c, Faction.g[c]))


class Faction:
    """Not intended to be instantiated."""

    # faction lists (not sets! order is used later)
    c = ['white', 'blue', 'black',  'red', 'green']
    g = ['azorius', 'boros', 'dimir',
         'golgari', 'gruul', 'izzet',
         'orzhov', 'rakdos', 'selesnya', 'simic']
    s = ['bant', 'naya', 'grixis', 'esper', 'jund']
    w = ['abzan', 'jeskai', 'mardu', 'sultai', 'temur']
    n = ['aggression', 'chaos', 'altruism', 'growth', 'artifice']

    # plot colors
    pc = {
        c[0]: 'gray'   , c[1]: 'blue'   , c[2]: 'black',
        c[3]: 'red'    , c[4]: 'green'  ,
        g[0]: '#8080ff', g[1]: '#ff8080', g[2]: 'blue',
        g[3]: 'green'  , g[4]: '#ffff00', g[5]: '#ff00ff',
        g[6]: '#808080', g[7]: 'red'    , g[8]: '#80ff80',
        g[9]: '#00ffff',
        s[0]: '#80ffff', s[1]: '#ffff80', s[2]: '#ff00ff',
        s[3]: '#8080ff', s[4]: '#ffff00',
        w[0]: '#008000', w[1]: '#800080', w[2]: '#800000',
        w[3]: '#00ffff', w[4]: 'gray',
        n[0]: '#ffff00', n[1]: '#000000', n[2]: '#ffff00',
        n[3]: 'gray'   , n[4]: '#00ffff'
    }

    all_factions = frozenset(c + g + s + w + n)

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

    # nephilim include these colors
    nm = {
        n[0]: {c[0], c[2], c[3], c[4]},
        n[1]: {c[1], c[2], c[3], c[4]},
        n[2]: {c[0], c[1], c[3], c[4]},
        n[3]: {c[0], c[1], c[2], c[4]},
        n[4]: {c[0], c[1], c[2], c[3]}
    }

    # nephilim include these guilds
    ngm = {
        n[0]: {g[1], g[3], g[4], g[6], g[7], g[8]},  # blueless
        n[1]: {g[2], g[3], g[4], g[6], g[6], g[8]},  # whiteless
        n[2]: {g[0], g[1], g[4], g[5], g[8], g[9]},  # blackless
        n[3]: {g[0], g[2], g[3], g[6], g[8], g[9]},  # redless
        n[4]: {g[0], g[1], g[2], g[5], g[6], g[7]}   # greenless
    }

    # nephilim include these shards
    nsm = {
        n[0]: {s[1], s[4]},
        n[1]: {s[2], s[4]},
        n[2]: {s[0], s[1]},
        n[3]: {s[0], s[3]},
        n[4]: {s[2], s[3]}
    }

    # nephilim include these wedges
    nwm = {
        n[0]: {w[0], w[2]},
        n[1]: {w[3], w[4]},
        n[2]: {w[1], w[4]},
        n[3]: {w[0], w[3]},
        n[4]: {w[1], w[2]}
    }

    # color shorthand
    csh = {'w': c[0], 'u': c[1], 'b': c[2], 'r': c[3], 'g': c[4]}

    # we don't need this
    def reverse_guild_map():
        """Generates the reverse guild map"""
        Faction.rgm = dict()
        for k, v in Faction.gm.items():
            Faction.rgm[frozenset(v)] = k

    @functools.lru_cache(maxsize=200)
    def who_can_play(cost):
        # Start by assuming anyone can play anything
        can_play = set(Faction.all_factions)
        costs = re.findall('([^{^}]+)', cost)

        for subcost in costs:
            # H = half (Little Girl)
            subcost = subcost.replace("H", "")
            # Colorless (eldrazi) mana
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
                #print("Who can play {}? Why, {} of course!"
                # .format(subcost, Faction.member_of(subcost)))
                subcost = Faction.colorname(subcost)
                can_play.intersection_update(Faction.member_of(subcost))

        return can_play

    def member_of(faction):
        """Takes the name of a faction - a color, guild, shard, wedge, or
        nephilim - and returns a set of names of the factions that it is a
        member of. For example, white belongs to azorius, abzan, jeskai, and so
        on.  This set will always include the faction in the argument."""

        faction = Faction.colorname(faction)

        # this color is a member of these shards
        m = {k for k, v in Faction.sm.items() if faction in v}

        # this color is a member of these guilds
        m = set.union(m, {k for k, v in Faction.gm.items() if faction in v})

        # this color is a member of these wedges
        m = set.union(m, {k for k, v in Faction.wm.items() if faction in v})

        # this color is a member of these nephilim
        m = set.union(m, {k for k, v in Faction.nm.items() if faction in v})

        # this guild is a member of these shards
        m = set.union(m, {k for k, v in Faction.sm.items() if faction in
                          Faction.sgm[k]})

        # this guild is a member of these wedges
        m = set.union(m, {k for k, v in Faction.wm.items() if faction in
                          Faction.wgm[k]})

        # this guild is a member of these nephilim
        m = set.union(m, {k for k, v in Faction.ngm.items() if faction in
                          Faction.ngm[k]})

        # this shard is a member of these nephilim
        m = set.union(m, {k for k, v in Faction.nsm.items() if faction in
                          Faction.nsm[k]})

        # this wedge is a member of these nephilim
        m = set.union(m, {k for k, v in Faction.nwm.items() if faction in
                          Faction.nwm[k]})

        # always a member of itself
        m = set.union(m, {faction})

        return m

    def colorname(name):
        """Convert color names from shorthand."""
        name = name.lower()
        if name in Faction.csh:
            name = Faction.csh.get(name)  # color shorthand (w,b,r,g,u)
        return name


class Cards():
    """Simple database of card data from Scryfall."""

    rate_limit = .1

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

    def add_card(self, name, api_url='https://api.scryfall.com'):
        """Download card data by name from deckbrew and add it to the card
        database. Since all we have is the name, just save the first result,
        which should be representative for the card mechanics. Skips
        downloading cards that are already in the database."""

        if name not in self.db.keys():
            print("Fetching {}".format(name))
            query = "{}/cards/named?exact={}".format(api_url, name)
            time.sleep(self.rate_limit)
            r = requests.get(query)
            if r.status_code == 200:
                self.db[name] = json.loads(r.text)

                # https://scryfall.com/docs/api/layouts
                # Split cards should be handled differently - unclear how.
                # Currently, just ignore other card faces, but if layout
                # is 'split', this doesn't make sense.

                if 'card_faces' in self.db[name]:
                    self.db[name] = self.db[name]['card_faces'][0]

                # Compatibility with previous Deckbrew format
                self.db[name]['cost'] = self.db[name]['mana_cost']

                typeline = self.db[name]['type_line'].lower()

                # Parse card type into types (including supertype) and creature type
                # A set might make more logical sense, but for now easier
                # to use lists with default JSON encoder.
                # Cover unlikely event of an empty typeline
                self.db[name]['types'] = list()

                if '—' in typeline:
                    self.db[name]['types'] = typeline.split('—', 1)[0].strip().split(' ')
                    self.db[name]['subtypes'] = typeline.split('—', 1)[1].strip().split(' ')
                else:
                    self.db[name]['types'] = typeline.split(' ')
                    self.db[name]['subtypes'] = list()

                logging.debug("{}\n\tCost: {}\n\t{}\n\t{} {}".format(
                    name, self.db[name]['cost'],
                    Faction.who_can_play(self.db[name]['cost']),
                    self.db[name]['types'], self.db[name]['subtypes']))

            # Too many requests: wait, decrease rate, try again
            elif r.status_code == 429:
                logging.warn("Rate limit exceeded, throttling...")
                self.rate_limit += .1
                time.sleep(2)
                self.add_card(name)

            # otherwise fail
            elif r.status_code == 404:
                exit("Card {} not found in API!".format(name))

            else:
                exit("Error communicating with API: status code {}".
                     format(r.status_code))

    def save(self):
        """Write the card database file."""
        if self.path:
            with open(self.path, 'w') as db_file:
                db_file.write(json.dumps(self.db))

    def show_guild_numbers():
        """Debugging function"""
        for c in range(0, 10):
            print("{} {}".format(c, Faction.g[c]))

    # there isn't really a point of looking up cards against the info database.
    # you'd actually want to look up cards against the cube contents.

    def condition_match(self, condition, **kwargs):
        """Returns the set of card names in the database that match a condition
        function.  Example: print(cdb.condition_match(lambda c: 'treefolk' in
        c.get('subtypes', []))).  """

        return {n for n, c in self.db.items() if condition(c, **kwargs)}
