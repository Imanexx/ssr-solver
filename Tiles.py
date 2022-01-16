from abc import ABC, abstractmethod
from Utils import *

import Entities as Entity

class Tile(ABC):
	def __init__(self, pos, zpos=1):
		self.pos = pos
		self.zpos = zpos

	@abstractmethod
	def __repr__(self):
		pass

	@abstractmethod
	def interact(self, entity, index):
		pass

class Ground(Tile):
	def __init__(self, pos, zpos=1):
		super().__init__(pos, zpos)

	def __repr__(self):
		if self.zpos > 1:
			return '#'
		else:
			return '.'

	def interact(self, entity, index):
		pass # Do nothing


class Grill(Tile):
	def __init__(self, pos, zpos=1):
		super().__init__(pos, zpos)

	def __repr__(self):
		return 'x'

	def interact(self, entity, index):
		if isinstance(entity, Entity.Sausage):
			entity.cook(index)
			return
		elif isinstance(entity, Entity.Player):
			if index == 0: # Player's body on grill
				# TODO: This is currently an assumption
				# If a player has a sausage on their head. Steps forwards such that the sausage falls off their head behind them
				# And THEN steps on a grill, when they step backwards they should push the sausage... Currently that does NOT happen
				entity.move(entity.prior_move.opposite())
			return