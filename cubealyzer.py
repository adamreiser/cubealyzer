#!/usr/bin/env python3

import argparse
import atexit
import os.path
import csv
import logging
from collections import Counter
from colorama import init, Style
import matplotlib.pyplot as plt
import mtg
# import mtgtests
# TODO
#
# Should recognize that lands are playable in any color (Dryad Arbor)

# Finish subtype code

# Delete unused card info from JSON caches

# colorama init() (only called in __main__)

# Cube.get(name)


class Cube():

    def __init__(self, csv_file, json_file):
        """Loads cube data from CSV file. Saves card data to JSON file."""

        # factiontype[faction][type][subtype]
        self.curve = dict()

        # name: num cards in cube
        self.contents = Counter()

        # Card info
        self.cards = mtg.Cards(json_file)

        # Save downloaded card data as a JSON file on exit
        atexit.register(self.cards.save)

        # Read cube CSV file into self.contents
        with open(csv_file, newline='') as cube_file:

            # Card names in cubes, with repeats
            for name in [row[0] for row in csv.reader(cube_file,
                                                      escapechar='\\') if
                         len(row) > 0]:

                # Download any uncached card data from public API
                self.cards.add_card(name)

                self.contents[name] += 1

        # Remember the cube identity
        self.csv_file = csv_file

    def conditional_curve(self, *conditions):
        """Returns a collections.Counter of the form {cmc: num} for the given
        condition functions. This represents a mana curve."""

        curve = Counter()

        for name in self.contents:
            card = self.cards.get(name)
            if all(condition(card) for condition in conditions):
                curve[card.get('cmc', 0)] += self.contents[name]

        return curve

    def faction_curve(self, faction, card_type='creature', sub_type=None):
        """Constructs and executes the required conditions as described by
        types. If card_type is none it is assumed to mean "any nonland
        permanent; if sub_type is None, it is ignored."""

        if faction is not None:
            condition_list = [lambda card: faction in mtg.Faction.who_can_play(card.get('cost'))]
        else:
            condition_list = []

        if card_type is None:
            def is_permanent(card):
                return any(t in {'creature', 'enchantment', 'artifact',
                                 'planeswalker'} for t in card.get('types'))
            condition_list.append(is_permanent)

        else:
            condition_list.append(lambda card: card_type in card.get('types'))

        if sub_type is not None:
            condition_list.append(lambda card: sub_type in card.get('subtypes'))

        return self.conditional_curve(*condition_list)

    def cards_matching_conditions(self, *conditions):
        """Returns a collections.Counter of card names in the cube object that
        meet the specified condition functions. Example:
        cube.cards_matching_conditions(lambda c: c.get('cmc') == 1"""

        results = Counter()
        for name, num in self.contents.items():
            if all(condition(self.cards.get(name)) for condition in
                   conditions):
                results[name] = num

        return results

    def update_curve(self, faction_type, card_type='creature', sub_type=None):
        """Updates the curve dictionary of cards with a particular type and
        optional subtype, broken down by the faction type given - 'c' colors,
        's' shards, 'w' wedges, and 'n' nephilim (four color combinations.)"""

        self.curve.update({card_type: {sub_type: {faction_type: {}}}})

        for faction in mtg.Faction.get_factions(faction_type):
            self.curve[card_type][sub_type][faction_type][faction] =\
                self.faction_curve(faction,
                                   card_type=card_type,
                                   sub_type=sub_type)

    def print_curve(self, faction_type, card_type='creature', sub_type=None):
        """Displays the curves for a faction type. Requires calculating curves
        for all the factions of that type."""

        self.update_curve(faction_type, card_type, sub_type)

        print("{}Cards of type {} at each cost in:{}".format(Style.BRIGHT,
                                                             card_type,
                                                             Style.RESET_ALL))

        for faction in sorted(self.curve[card_type][sub_type][faction_type]):
            print(faction.ljust(12), end='')
            for mana, num in sorted(self.curve[card_type][sub_type][faction_type][faction].items()):
                print("{}{:.0f}{}:{:2} ".format(Style.BRIGHT, mana,
                                                Style.RESET_ALL, num), end='')
            print()

    def plot_curve(self, faction_type, faction, card_type='creature', sub_type=None):
        """Plot the curve for the given parameters."""

        d = self.curve[card_type][sub_type][faction_type][faction].items()

        x = [k for k, v in sorted(d)]
        y = [v for k, v in sorted(d)]

        # Plot colors
        if faction in mtg.Faction.pc:
            plt.plot(x, y, color=mtg.Faction.pc[faction], label=faction)
        else:
            plt.plot(x, y, label=faction)

    def show_curve_plots(self, faction_type, card_type='creature', sub_type=None):
        """Display graphical plots of the desired curves."""

        for faction in mtg.Faction.get_factions(faction_type):
            self.plot_curve(faction_type, faction, card_type, sub_type)
        plt.title("{} mana curves ({}) for "
                  "{}".format(mtg.Faction.fsh[faction_type], card_type,
                              self.csv_file))
        plt.legend()
        plt.show()

    def card_count(self, faction):
        """Returns the total number of cards playable in decks of only a
        particular faction. Duplicates count."""
        conditions = [lambda card: faction in mtg.Faction.who_can_play(card.get('cost'))]

        return sum(self.cards_matching_conditions(*conditions).values())

    def show_type_counts(self, faction_type, card_type='creature'):
        """Display cards of a particular type broken down by playability in
        factions - 'c' colors, 's' shards, 'w' wedges, and 'n' nephilim (four
        color combinations.)"""

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
        """Display the total number of cards playable in decks of all factions
        of a particular type ('c' colors, 's' shards, 'w' wedges, and 'n'
        nephilim (four color combinations.)"""

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

    parser.add_argument('--subtype', metavar='subtype', dest='subtype',
                        type=str, nargs='?', default=None,
                        help='The card subtype \
                        to calculate curves for (default: none)')

    parser.add_argument('-c', dest='faction_types', const='c',
                        action='append_const', default=[], help='Calculate \
                        curves for colors')

    parser.add_argument('-g', dest='faction_types', const='g',
                        action='append_const', default=[], help='Calculate \
                        curves for guilds')

    parser.add_argument('-s', dest='faction_types', const='s',
                        action='append_const', default=[], help='Calculate \
                        curves for shards')

    parser.add_argument('-w', dest='faction_types', const='w',
                        action='append_const', default=[], help='Calculate \
                        curves for wedges')

    parser.add_argument('-n', dest='faction_types', const='n',
                        action='append_const', default=[], help='Calculate \
                        curves for nephilim')

    parser.add_argument('--plot', action='store_true',
                        help='Display plots of generated curves')

    parser.add_argument('--test', action='store_true',
                        help='Generate tests')

    parser.add_argument('-d', '--debug', action='store_const', dest="loglevel",
                        const=logging.DEBUG, default=logging.WARNING,
                        help='Generate debug messages')

    parser.add_argument('-v', '--verbose', action='store_const', dest="loglevel",
                        const=logging.INFO, default=logging.WARNING,
                        help='Generate verbose (but not debug) messages')

    args = parser.parse_args()

    logger = logging.getLogger()
    logging.basicConfig(level=args.loglevel, format='%(asctime)s - %(levelname)s - %(message)s')

    # colorama
    init()

    thecube = Cube(args.cubefile, "{}.json".
                   format(os.path.splitext(args.cubefile)[0]))

    if args.test:
        mtg.create_tests()

    for faction_type in args.faction_types:
        thecube.show_card_counts(faction_type)
        thecube.show_type_counts(faction_type, args.t)
        thecube.print_curve(faction_type, card_type=args.t, sub_type=args.subtype)

        if args.plot:
            thecube.show_curve_plots(faction_type, card_type=args.t)
