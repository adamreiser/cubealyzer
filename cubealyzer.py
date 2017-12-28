#!/usr/bin/env python3

import argparse
import matplotlib.pyplot as plt
import atexit
import mtg
import mtgtests
import os.path
import csv
import logging
from colorama import init, Fore, Back, Style

from collections import Counter


init()


logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s\
-\ %(message)s')

# TODO
#
# Should recognize that lands are playable in any color (Dryad Arbor)

# Finish subtype curves to allow tribal balance analysis

# Delete unused card info from JSON caches

# Improve storage; shelve?

# Possibly use a {name: count} dictionary instead of a list


class Cube():

    # Hard limit on CMC used to calculate/display curve to prevent issues with
    # cards like Gleemax.
    MAX_CMC = 15

    def __init__(self, csv_file, json_file):
        """Loads cube data from CSV file. Saves card data to JSON file."""
        self.curve = dict()

        # Cards in the cube (with repeats for multiples)
        self.contents = list()

        # Card info
        self.cards = mtg.Cards(json_file)

        # Save downloaded card data as a JSON file on exit
        atexit.register(self.cards.save)

        # Read cube CSV file into self.contents
        with open(csv_file) as cube_file:
            for row in csv.reader(cube_file):
                if len(row) > 0:
                    name = row[0]

                    # Download card data from public API
                    self.cards.add_card(name)

                    # List of cards in the cube
                    # Should be a dictionary of counts
                    self.contents.append(name)

    def conditional_curve(self, *conditions):
        """Return a curve dictionary ({cmc: count}) for cards matching the
        given list of conditions."""

        curve = {}

        # The highest cmc appearing in a cost
        max_cmc = int(max([self.cards.db.get(name).get('cmc', 0) for name in
                           self.contents]))

        max_cmc = min(max_cmc, self.MAX_CMC)

        for cmc in range(1, max_cmc + 1):

            num = 0
            cards = ((name, self.cards.db.get(name)) for name in self.contents)

            for name, card in cards:
                result = card.get('cmc') == cmc
                if result is False:
                    next
                for condition in conditions:
                    result = condition(card) and result
                if result is True:
                    num += 1

                curve[cmc] = num

        return curve

    def faction_curve(self, faction, curve_type='creature', sub_type=None):
        """Returns a curve dictionary ({cmc: count}) of creatures (or other
        permanent type) playable with only mana of a particular faction's
        colors (a single color, guild, shard, wedge, or nephilim name). If None
        is passed as the curve type, all permanents count towards the curve."""

        # True if this card's cost can be paid with mana from only this faction
        condition_list = [lambda card: faction in
                          mtg.Faction.who_can_play(card.get('cost'))]

        if curve_type is not None:
            # True if the card object is the specified type
            condition_list.append(lambda card: curve_type in card.get('types'))

        # Otherwise any permanent
        else:
            def is_permanent(card):
                return set() != set(card.get('types')).intersection(
                    {'creature', 'enchantment', 'land', 'artifact',
                     'planeswalker'})

            condition_list.append(is_permanent)

        if sub_type is not None:
            condition_list.append(lambda card: sub_type in
                                  card.get('subtypes'))

        return self.conditional_curve(*condition_list)

    def subtype_creature_curve(self, subtype):
        """Returns a curve dictionary {cmc: count} of creatures with a
        particular subtype."""
        return self.conditional_curve(lambda card: 'creature' in
                                      card.get('types', []), lambda card:
                                      subtype in card.get('subtypes', []))

    def cards_matching_conditions(self, *conditions):
        """Return a list of card names in the cube matching the specified
        conditions. Cards that appear multiple times in the cube will appear
        multiple times in these results. Example:
        cube.cards_matching_conditions(lambda c: c.get('cmc') == 1, lambda
        c: 'creature' in c.get('types'), lambda c: 'black' in
        mtg.Faction.who_can_play(c.get('cost')))"""
        cards = ((name, self.cards.db.get(name)) for name in self.contents)

        results = list()
        for name, card in cards:
            val = True

            for condition in conditions:
                val = condition(card) and val
            if val is True:
                results.append(name)

        return results

    def calculate_curve(self, curve_type='creature', sub_type=None):
        self.curve[curve_type] = dict()
        for faction in mtg.Faction.all_factions:
            self.curve[curve_type][faction] =\
                self.faction_curve(faction, curve_type=curve_type,
                                   sub_type=sub_type)

    def print_curve(self, faction_list, curve_type='creature'):
        """Displays the curve for a type"""
        if curve_type not in self.curve.keys():
            self.calculate_curve(curve_type=curve_type)

        print("{}Cards of type {} at each cost in:{}".format(Style.BRIGHT,
                                                             curve_type,
                                                             Style.RESET_ALL))

        for faction, curve in sorted(self.curve[curve_type].items()):
            if faction in faction_list:
                print(faction.ljust(12), end='')
                for mana, num in sorted(curve.items()):
                    print("{}{}{}:{:2} ".format(Style.BRIGHT, mana,
                                                Style.RESET_ALL, num), end='')
                print()

    def plot_curve(self, faction, curve_type='creature'):
        """Plot the curve for the given faction name and type."""

        d = thecube.curve[curve_type]
        x = [k for k, v in sorted(d.get(faction, {}).items())]
        y = [v for k, v in sorted(d.get(faction, {}).items())]

        # Plot colors
        if faction in mtg.Faction.pc.keys():
            plt.plot(x, y, color=mtg.Faction.pc[faction], label=faction)
        else:
            plt.plot(x, y, label=faction)

    def show_curve_plots(self, faction_list, curve_type='creature'):
        for f in faction_list:
            self.plot_curve(f, curve_type=curve_type)
        plt.title("Mana curves ({})".format(curve_type))
        plt.legend()
        plt.show()

    def card_count(self, faction):
        s = 0
        for name in self.contents:
            f = mtg.Faction.who_can_play(self.cards.db[name]['cost'])
            if faction in f:
                s += 1
        return s

    def count(self, card_type, faction):
        """Returns a dictionary of the number of..."""

        if card_type not in self.curve.keys():
            self.calculate_curve(curve_type='creature')

        return sum(self.curve.get(card_type, dict()).
                   get(faction, dict()).values())

    # Cards of a particular type name that are playable in a particular faction
    def show_type_counts(self, faction_type, card_type='creature'):
        print("{}Cards of type {} playable in:{}".format(Style.BRIGHT,
                                                         card_type,
                                                         Style.RESET_ALL))

        for faction in sorted(faction_type):
            cd = self.conditional_curve(lambda card: card_type in
                                        card['types'], lambda card: faction in
                                        mtg.Faction.
                                        who_can_play(card.get('cost')))

            print("{:12}{}".format(faction, sum(cd.values())))

    def show_card_counts(self, faction_type):
        print("{}Total cards playable in:{}".format(Style.BRIGHT,
                                                    Style.RESET_ALL))
        for f in sorted(faction_type):
            print("{:12}{}".format(f, self.card_count(f)))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Curve analysis tool \
                                     for Magic: the Gathering cubes.')

    parser.add_argument('cubefile', metavar='[FILE]', type=str,
                        help='The cube file (cubetutor CSV export)')

    parser.add_argument('-t', metavar='type', dest='t', type=str, nargs='?',
                        default='creature', help='The card type \
                        to calculate curves for (default: creature)')

    # Not used yet
    parser.add_argument('--subtype', metavar='subtype', dest='subtype',
                        type=str, nargs='?', default=None,
                        help='The card subtype \
                        to calculate curves for (default: none)')

    parser.add_argument('-c', dest='faction_type', const='c',
                        action='append_const', help='Calculate \
                        curves for colors')

    parser.add_argument('-g', dest='faction_type', const='g',
                        action='append_const', help='Calculate \
                        curves for guilds')

    parser.add_argument('-s', dest='faction_type', const='s',
                        action='append_const', help='Calculate \
                        curves for shards')

    parser.add_argument('-w', dest='faction_type', const='w',
                        action='append_const', help='Calculate \
                        curves for wedges')

    parser.add_argument('-n', dest='faction_type', const='n',
                        action='append_const', help='Calculate \
                        curves for nephilim')

    parser.add_argument('--plot', action='store_true',
                        help='Display plots of generated curves')

    parser.add_argument('--test', action='store_true',
                        help='Generate tests')

    args = parser.parse_args()

    thecube = Cube(args.cubefile, "{}.json".
                   format(os.path.splitext(args.cubefile)[0]))

    if args.test:
        mtg.create_tests()

    if args.faction_type:
        # any of "cgswn"
        for faction_type in args.faction_type:
            # ["azorius, "boros", "dimir", ...]
            faction_list = mtg.Faction.__dict__.get(faction_type)
            thecube.show_card_counts(faction_list)
            thecube.show_type_counts(faction_list, args.t)
            thecube.print_curve(faction_list, curve_type=args.t)
            if args.plot:
                thecube.show_curve_plots(faction_list, curve_type=args.t)
