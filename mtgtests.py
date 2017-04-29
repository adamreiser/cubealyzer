import mtg

assert(mtg.Faction.who_can_play('bant') == {'bant'})
assert(mtg.Faction.who_can_play('golgari') == {'abzan', 'sultai', 'golgari', 'jund'})
assert(mtg.Faction.who_can_play('boros') == {'mardu', 'boros', 'jeskai', 'naya'})
assert(mtg.Faction.who_can_play('blue') == {'sultai', 'izzet', 'esper', 'simic', 'bant', 'azorius', 'jeskai', 'blue', 'grixis', 'temur', 'dimir'})
assert(mtg.Faction.who_can_play('orzhov') == {'abzan', 'mardu', 'esper', 'orzhov'})
assert(mtg.Faction.who_can_play('grixis') == {'grixis'})
assert(mtg.Faction.who_can_play('temur') == {'temur'})
assert(mtg.Faction.who_can_play('sultai') == {'sultai'})
assert(mtg.Faction.who_can_play('red') == {'rakdos', 'izzet', 'naya', 'gruul', 'red', 'mardu', 'boros', 'jeskai', 'jund', 'grixis', 'temur'})
assert(mtg.Faction.who_can_play('selesnya') == {'abzan', 'bant', 'selesnya', 'naya'})
assert(mtg.Faction.who_can_play('izzet') == {'grixis', 'temur', 'jeskai', 'izzet'})
assert(mtg.Faction.who_can_play('naya') == {'naya'})
assert(mtg.Faction.who_can_play('white') == {'esper', 'naya', 'bant', 'abzan', 'white', 'azorius', 'mardu', 'boros', 'orzhov', 'jeskai', 'selesnya'})
assert(mtg.Faction.who_can_play('gruul') == {'temur', 'gruul', 'naya', 'jund'})
assert(mtg.Faction.who_can_play('azorius') == {'azorius', 'esper', 'jeskai', 'bant'})
assert(mtg.Faction.who_can_play('mardu') == {'mardu'})
assert(mtg.Faction.who_can_play('jeskai') == {'jeskai'})
assert(mtg.Faction.who_can_play('jund') == {'jund'})
assert(mtg.Faction.who_can_play('dimir') == {'sultai', 'grixis', 'esper', 'dimir'})
assert(mtg.Faction.who_can_play('rakdos') == {'rakdos', 'mardu', 'grixis', 'jund'})
assert(mtg.Faction.who_can_play('esper') == {'esper'})
assert(mtg.Faction.who_can_play('simic') == {'sultai', 'temur', 'simic', 'bant'})
assert(mtg.Faction.who_can_play('black') == {'rakdos', 'sultai', 'esper', 'black', 'golgari', 'abzan', 'mardu', 'orzhov', 'jund', 'grixis', 'dimir'})
assert(mtg.Faction.who_can_play('abzan') == {'abzan'})
assert(mtg.Faction.who_can_play('green') == {'sultai', 'simic', 'naya', 'bant', 'golgari', 'abzan', 'green', 'gruul', 'selesnya', 'jund', 'temur'})
assert(mtg.Faction.who_can_play('{8}{C}{C}') == set())
assert(mtg.Faction.who_can_play('{1}{P/C}') == frozenset({'bant', 'golgari', 'boros', 'blue', 'orzhov', 'grixis', 'temur', 'sultai', 'red', 'selesnya', 'izzet', 'naya', 'white', 'gruul', 'azorius', 'mardu', 'jeskai', 'jund', 'dimir', 'rakdos', 'esper', 'simic', 'black', 'abzan', 'green'}))
