#!/usr/bin/env python3
"""Unit tests for cubealyzer."""

import unittest
import mtg
import cubealyzer


class Tests(unittest.TestCase):
    """Run some tests."""

    tricky_card_names = ('"Ach! Hans, Run!"',
                         "Cenn's Heir",
                         "Liliana, Heretical Healer")

    testcube_input_csv = 'testcube.csv'
    testcube_output_json = 'testcube.json'

    def setUp(self):
        self.testcube = cubealyzer.Cube(self.testcube_input_csv,
                                        self.testcube_output_json)

    def tearDown(self):
        self.testcube.cards.save()

    def test_lines(self):
        """Number of non-blank lines in the file should be equal to number of
        cards in the cube (blank lines will interfere with this, so remove
        them.)"""

        with open(self.testcube_input_csv) as testfile:
            non_blank_lines = list(filter(None, (line.rstrip() for line in
                                                 testfile.readlines())))
            self.assertEqual(len(non_blank_lines),
                             sum(self.testcube.contents.values()))

    def test_multiples(self):
        """Test multiple copies of a card"""
        self.assertEqual(self.testcube.contents["Pack Rat"], 2)

    def test_card_load(self):
        """Cards with names likely to break the parser are loaded into the card
        database."""
        for card_name in self.tricky_card_names:
            self.assertEqual(self.testcube.cards.get(card_name).get('name'),
                             card_name)

    def test_parser(self):
        """Cards with names likely to break the parser are loaded into the
        cube."""

        for card_name in self.tricky_card_names:
            self.assertTrue(self.testcube.cards.get(card_name).get('name') in
                            self.testcube.contents)

    def test_typelines(self):
        """Typelines are parsed correctly."""

        self.assertTrue({'world', 'enchantment'} ==
                        set(self.testcube.cards.get("Storm "
                                                    "World").get('types')))
        self.assertTrue({'creature', 'land'} ==
                        set(self.testcube.cards.get("Dryad "
                                                    "Arbor").get('types')))

        self.assertTrue({'human', 'cleric', 'soldier'} ==
                        set(self.testcube.cards.get("Goldnight Commander")
                            .get('subtypes')))


    def test_zero_cmc(self):
        """Anything with cmc 0 must be castable by all factions at the same
        point - zero - in the curve."""
        for ftype in mtg.Faction.fsh:
            self.testcube.update_curve(ftype)
            zero_counts = [self.testcube.curve['creature'][None][ftype][f][0]
                           for f in mtg.Faction.get_factions(ftype)]
            assert zero_counts.count(zero_counts[0]) == len(zero_counts)


if __name__ == "__main__":
    unittest.main()
