from abc import ABC, abstractmethod
from Utils import *

import Entities as Entity

class Tile(ABC):
	def __init__(self, pos, zpos=1):
		self.pos = pos
		self.zpos = zpos

	def __eq__(self, other):
		# Old legacy code I am trying to get rid of
		from inspect import getframeinfo, stack
		caller = getframeinfo(stack()[1][0])
		print("%s:%d - BEING CALLED" % (caller.filename, caller.lineno)) # python3 syntax print

		if isinstance(other, Entity):
			# Is the entity on top of this tile?
			for pos in other.get_positions():
				if self.pos == pos and self.zpos == other.zpos:
					return True
		if isinstance(other, int):
			return self.pos == other
		return False

	@abstractmethod
	def __repr__(self):
		pass

	@abstractmethod
	def interact(self, entity):
		pass

class Ground(Tile):
	def __init__(self, pos, zpos=1):
		super().__init__(pos, zpos)

	def __repr__(self):
		if self.zpos > 1:
			return '#'
		else:
			return '.'

	def interact(self, entity):
		pass # Do nothing


class Grill(Tile):
	def __init__(self, pos, zpos=1):
		super().__init__(pos, zpos)

	def __repr__(self):
		return 'x'

	def interact(self, entity):
		if isinstance(entity, Entity.Sausage):
			sausage = entity
			positions = sausage.get_positions()
			first = positions[0]
			second = positions[1]

			if first == self.pos:
				sausage.cook(0)
			elif second == self.pos:
				sausage.cook(1)

			return
		elif isinstance(entity, Entity.Player):
			player = entity
			body, fork = player.get_positions()
			if body == self.pos:
				forces = [opposite_force(player.last_movement)]
				forces_coords = [player.position]
				return forces, forces_coords
