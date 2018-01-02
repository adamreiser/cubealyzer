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

# Possibly use a {name: count} dictionary instead of a list


class Cube():

    def __init__(self, csv_file, json_file):
        """Loads cube data from CSV file. Saves card data to JSON file."""
        self.curve = dict()

        # Dictionary of name: count cards in cube
        self.counter = Counter()

        # Card info
        self.cards = mtg.Cards(json_file)

        # Save downloaded card data as a JSON file on exit
        atexit.register(self.cards.save)

        # Read cube CSV file into self.counter
        with open(csv_file, newline='') as cube_file:

            # Card names in cubes, with repeats
            name_list = [row[0] for row in csv.reader(cube_file, escapechar='\\') if len(row) > 0]

            for name in name_list:

                # Download any uncached card data from public API
                self.cards.add_card(name)

                # Experimental feature: counters
                self.counter[name] += 1

        # Remember the input filename for plot titles
        self.csv_file = csv_file

    def conditional_curve(self, *conditions):
        """Return a curve dictionary ({cmc: count}) for cards matching the
        given list of condition functions."""

        curve = Counter()

        for name in self.counter:
            card = self.cards.get(name)
            if all(condition(card) for condition in conditions):
                curve[card.get('cmc', 0)] += self.counter[name]

        return curve

    def faction_curve(self, faction, curve_type, sub_type=None):
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

        # Otherwise any nonland permanent
        else:
            def is_permanent(card):
                return any(t in {'creature', 'enchantment', 'artifact',
                                 'planeswalker'} for t in card.get('types'))
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

    # Experiment - not sure how to change
    # This is called by the count method

    def cards_matching_conditions(self, *conditions):
        """Return a list of card names in the cube matching the specified
        conditions. Cards that appear multiple times in the cube will appear
        multiple times in these results. Example:
        cube.cards_matching_conditions(lambda c: c.get('cmc') == 1, lambda
        c: 'creature' in c.get('types'), lambda c: 'black' in
        mtg.Faction.who_can_play(c.get('cost')))"""

        # Counter version
        results = Counter()
        for name, num in self.counter.items():
            if all(condition(self.cards.get(name)) for condition in
                   conditions):
                results[name] = num

        return results

    def calculate_curve(self, curve_type='creature', sub_type=None):
        self.curve[curve_type] = dict()
        for faction in mtg.Faction.all_factions:
            self.curve[curve_type][faction] =\
                self.faction_curve(faction, curve_type=curve_type,
                                   sub_type=sub_type)

    def print_curve(self, faction_type, curve_type='creature'):
        """Displays the curve for a type."""
        if curve_type not in self.curve:
            self.calculate_curve(curve_type=curve_type)

        faction_list = mtg.Faction.get_factions(faction_type)

        print("{}Cards of type {} at each cost in:{}".format(Style.BRIGHT,
                                                             curve_type,
                                                             Style.RESET_ALL))

        for faction, curve in sorted(self.curve[curve_type].items()):
            if faction in faction_list:
                print(faction.ljust(12), end='')
                for mana, num in sorted(curve.items()):
                    print("{}{:.0f}{}:{:2} ".format(Style.BRIGHT, mana,
                                                    Style.RESET_ALL, num),
                          end='')
                print()

    def plot_curve(self, faction, curve_type='creature'):
        """Plot the curve for the given faction name and type."""

        d = self.curve[curve_type]
        x = [k for k, v in sorted(d.get(faction, {}).items())]
        y = [v for k, v in sorted(d.get(faction, {}).items())]

        # Plot colors
        if faction in mtg.Faction.pc:
            plt.plot(x, y, color=mtg.Faction.pc[faction], label=faction)
        else:
            plt.plot(x, y, label=faction)

    def show_curve_plots(self, faction_type, curve_type='creature'):

        faction_list = mtg.Faction.get_factions(faction_type)

        for f in faction_list:
            self.plot_curve(f, curve_type=curve_type)
        plt.title("{} mana curves ({}) for "
                  "{}".format(mtg.Faction.fsh[faction_type], curve_type,
                              self.csv_file))
        plt.legend()
        plt.show()

    def card_count(self, faction):
        """Returns the total number of cards playable in decks of only a
        particular faction. Duplicates count."""
        conditions = [lambda card: faction in mtg.Faction.who_can_play(card.get('cost'))]

        return sum(self.cards_matching_conditions(*conditions).values())

    # Cards of a particular type name that are playable in a particular faction
    def show_type_counts(self, faction_type, card_type='creature'):
        faction_list = mtg.Faction.get_factions(faction_type)
        print("{}Cards of type {} playable per {} in:{}".format(Style.BRIGHT,
                                                                card_type,
                                                                mtg.Faction.fsh[faction_type],
                                                                Style.RESET_ALL))

        for faction in sorted(faction_list):
            cd = self.conditional_curve(lambda card: card_type in
                                        card['types'], lambda card: faction in
                                        mtg.Faction.
                                        who_can_play(card.get('cost')))

            print("{:12}{}".format(faction, sum(cd.values())))

    def show_card_counts(self, faction_type):
        faction_list = mtg.Faction.get_factions(faction_type)
        print("{}Total cards playable in:{}".format(Style.BRIGHT,
                                                    Style.RESET_ALL))
        for f in sorted(faction_list):
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
            thecube.show_card_counts(faction_type)
            thecube.show_type_counts(faction_type, args.t)
            thecube.print_curve(faction_type, curve_type=args.t)

            if args.plot:
                thecube.show_curve_plots(faction_type, curve_type=args.t)
