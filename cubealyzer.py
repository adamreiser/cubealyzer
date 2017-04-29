#!/usr/bin/env python3

import argparse
import re
import matplotlib.pyplot as plt
import atexit
import mtg
import mtgtests
import os.path


class Cube():
    pt = re.compile(r'"(.+)","(.+)","(.+)","(.+)"')

    def __init__(self, fname, db_name):
        """Load card data and calculate creature curve"""
        self.curve = dict()
        # database of card info
        self.cards = mtg.Cards(db_name)
        # list of cards in cube (length should be number of cards in cube)
        self.contents = list()

        atexit.register(self.cards.save)  # save the card data on exit

        with open(fname) as cube_file:
            for line in cube_file.readlines():
                m = re.search(Cube.pt, line)
                assert(len(m.groups()) == 4)
                name, color, kind, cost = m.groups()

                # Normalize split card names
                if ' // ' in name:
                    name = name.split(' // ')[0]

                # Fetch card data from API
                self.cards.add_card(name)
                self.contents.append(name)

    def calculate_curve(self, card_type):
        # card type curve
        curve = dict()

        for name in self.contents:
            card = self.cards.db[name]

            # only the requested type
            if card_type not in card['types']:
                continue

            cost = card['cmc']
            who_can_play = mtg.Faction.who_can_play(card['cost'])

            if who_can_play == mtg.Faction.all_factions:
                # print("debug: ignoring {} (anyone can play)".format(name))
                continue

            for faction in who_can_play:
                if faction not in curve.keys():
                    curve[faction] = {cost: 1}
                else:
                    nc = curve[faction].get(cost, 0)
                    curve[faction][cost] = nc + 1

        # the curve we've been working with is for a particular card type
        self.curve[card_type] = curve

    def print_curve(self, faction_list, card_type='creature'):
        """Displays the curve for a type"""
        if card_type not in self.curve.keys():
            self.calculate_curve(card_type)

        print("Cards of type {} at each cost in:".format(card_type))
        for k, v in sorted(self.curve[card_type].items()):
            if k in faction_list:
                print(k.ljust(12), end='')
                for c in sorted(v.keys()):
                    print("{}:{:2} ".format(c, v[c]), end='')
                print()

    def plot_curve(self, faction, card_type):
        d = thecube.curve['creature']
        x = [k for k, v in sorted(d.get(faction, {}).items())]
        y = [v for k, v in sorted(d.get(faction, {}).items())]

        # match colors
        if faction in mtg.Faction.pc.keys():
            plt.plot(x, y, color=mtg.Faction.pc[faction], label=faction)
        else:
            plt.plot(x, y, label=faction)

    def show_curve_plots(self, faction_list, card_type):
        for f in faction_list:
            self.plot_curve(f, card_type)
        plt.title("Mana curves ({})".format(card_type))
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
        if card_type not in self.curve.keys():
            self.calculate_curve(card_type)

        return sum(self.curve.get(card_type, dict()).
                   get(faction, dict()).values())

    def show_type_counts(self, faction_type, card_type):
        print("Cards of type {} playable in:".format(card_type))
        for f in faction_type:
            print("{:12}{}".format(f, self.count(card_type, f)))

    def show_card_counts(self, faction_type):
        print("Total cards playable in:")
        for f in faction_type:
            print("{:12}{}".format(f, self.card_count(f)))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Curve analysis tool \
                                     for Magic: the Gathering cubes.')

    parser.add_argument('cubefile', metavar='[FILE]', type=str,
                        help='The cube file (cubetutor CSV export)')

    parser.add_argument('-t', metavar='type', dest='t', type=str, nargs='?',
                        default='creature', help='The card type \
                        to calculate curves for (default: creature)')

    parser.add_argument('-c', dest='curves', const='c',
                        action='append_const', help='Calculate \
                        curves for individual colors')

    parser.add_argument('-g', dest='curves', const='g',
                        action='append_const', help='Calculate \
                        curves for guilds')

    parser.add_argument('-s', dest='curves', const='s',
                        action='append_const', help='Calculate \
                        curves for shards')

    parser.add_argument('-w', dest='curves', const='w',
                        action='append_const', help='Calculate \
                        curves for wedges')

    parser.add_argument('--plot', action='store_true',
                        help='Display plots of generated curves')

    parser.add_argument('--test', action='store_true',
                        help='Generate tests')

    args = parser.parse_args()

    thecube = Cube(args.cubefile, "{}.json".
                   format(os.path.splitext(args.cubefile)[0]))

    if args.test:
        mtg.create_tests()

    if args.curves:
        for t in args.curves:
            f = mtg.Faction.__dict__.get(t)
            thecube.show_card_counts(f)
            thecube.show_type_counts(f, args.t)
            thecube.print_curve(f, args.t)
            if args.plot:
                thecube.show_curve_plots(f, args.t)
