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
        """Anything with cmc 0 is castable by all factions at the same
        point - zero - in the curve."""
        for ftype in mtg.Faction.fsh:
            self.testcube.update_curve(ftype)
            zero_counts = [self.testcube.curve['creature'][None][ftype][f][0]
                           for f in mtg.Faction.get_factions(ftype)]
            assert zero_counts.count(zero_counts[0]) == len(zero_counts)

    def test_who_can_play(self):
        """Check the factions capable of playing each color combination."""

        who_can_play = {
            'abzan': {'abzan', 'growth', 'aggression'},
            'aggression': {'aggression'},
            'altruism': {'altruism'},
            'artifice': {'artifice'},
            'azorius': {'jeskai', 'bant', 'altruism', 'artifice', 'azorius', 'growth', 'esper'},
            'bant': {'bant', 'growth', 'altruism'},
            'black': {'grixis', 'rakdos', 'abzan', 'dimir', 'black', 'sultai', 'artifice', 'growth', 'golgari', 'orzhov', 'jund', 'chaos', 'mardu', 'esper', 'aggression'},
            'blue': {'grixis', 'jeskai', 'dimir', 'simic', 'blue', 'sultai', 'artifice', 'growth', 'bant', 'chaos', 'altruism', 'izzet', 'temur', 'azorius', 'esper'},
            'boros': {'naya', 'jeskai', 'altruism', 'boros', 'artifice', 'mardu', 'aggression'},
            'chaos': {'chaos'},
            'dimir': {'grixis', 'dimir', 'chaos', 'sultai', 'artifice', 'growth', 'esper'},
            'esper': {'artifice', 'growth', 'esper'},
            'golgari': {'abzan', 'chaos', 'sultai', 'growth', 'jund', 'golgari', 'aggression'},
            'green': {'naya', 'abzan', 'simic', 'selesnya', 'gruul', 'sultai', 'growth', 'jund', 'golgari', 'green', 'bant', 'chaos', 'altruism', 'temur', 'aggression'},
            'grixis': {'artifice', 'grixis', 'chaos'},
            'growth': {'growth'},
            'gruul': {'naya', 'chaos', 'altruism', 'gruul', 'temur', 'jund', 'aggression'},
            'izzet': {'grixis', 'jeskai', 'altruism', 'izzet', 'artifice', 'temur'},
            'jeskai': {'artifice', 'jeskai', 'altruism'},
            'jund': {'chaos', 'jund', 'aggression'},
            'mardu': {'artifice', 'mardu', 'aggression'},
            'naya': {'naya', 'altruism', 'aggression'},
            'orzhov': {'abzan', 'artifice', 'growth', 'orzhov', 'chaos', 'esper', 'mardu', 'aggression'},
            'rakdos': {'grixis', 'rakdos', 'artifice', 'jund', 'mardu', 'aggression'},
            'red': {'naya', 'grixis', 'rakdos', 'jeskai', 'gruul', 'boros', 'artifice', 'jund', 'chaos', 'altruism', 'izzet', 'red', 'temur', 'mardu', 'aggression'},
            'selesnya': {'naya', 'abzan', 'selesnya', 'growth', 'bant', 'chaos', 'altruism', 'aggression'},
            'simic': {'bant', 'simic', 'altruism', 'sultai', 'temur', 'growth'},
            'sultai': {'growth', 'chaos', 'sultai'},
            'temur': {'temur', 'chaos', 'altruism'},
            'white': {'naya', 'white', 'abzan', 'jeskai', 'selesnya', 'boros', 'artifice', 'growth', 'orzhov', 'bant', 'altruism', 'azorius', 'esper', 'aggression', 'mardu'}
        }

        for faction, can_be_played_by in who_can_play.items():
            self.assertEqual(mtg.Faction.who_can_play(faction), can_be_played_by)


    def test_casting_costs(self):
        """Test some strange casting costs"""
        self.assertEqual(mtg.Faction.who_can_play('{8}{C}{C}'), set())
        self.assertEqual(mtg.Faction.who_can_play('{{1}}{{P/C}}'), mtg.Faction.all_factions)


if __name__ == "__main__":
    unittest.main()
