from abc import ABC, abstractmethod
from Utils import *

class Entity(ABC):
	def __init__(self, map_dim, pos, zpos=1, id = -1):
		self.width = map_dim[0]
		self.height = map_dim[1]
		self.pos = pos
		self.id = id
		self.zpos = zpos
		self.in_water = False

	def act(self, force):
		return force.walk(self.pos, self.width)

	def observe(self, force, pos):
		return force.walk(pos, self.width)

	@abstractmethod
	def get_symbols(self):
		""" Gets the ascii symbols and positions of ents"""
		pass

	@abstractmethod
	def get_positions(self) -> list:
		""" Get all the points that the current entity is taking up """
		pass

	@abstractmethod
	def move(self, force : Move):
		"""
		returns
			forces				: What forces does it apply on surrounding squares?
			forces_positions	: The positions that experience the above forces
			Note: forces and forces_positions can be zipped together to get require information
		"""
		pass

	@abstractmethod
	def score(self):
		""" returns a 'state' score """
		pass

class Sausage(Entity):
	def __init__(self, map_dim, pos, orientation, zpos=1, id = -1, flip_side=0, sides="0000", disable_turn=False):
		super().__init__(map_dim, pos, zpos=zpos, id=id)
		self.orientation = orientation
		self.flip_side = flip_side
		self.sides = sides # Uncooked = 0000; Cooked = 1111; Burned contains >2
		self.burned = False # Set when burned
		self.disable_turn = disable_turn

	def is_cooked(self):
		if self.burned:
			return False
		for value in self.sides:
			if value != '1':
				return False
		return True

	def flip(self):
		if self.disable_turn:
			return
		self.flip_side = self.flip_side ^ 1

	def disable(self):
		self.disable_turn = True

	def enable(self):
		self.disable_turn = False

	def get_symbols(self):
		# TODO: In water?
		if self.in_water:
			symbols = 'zz'
		elif self.orientation == Orientation.HORIZONTAL:
			symbols = '><'
		elif self.orientation == Orientation.VERTICAL:
			symbols = 'v^'

		positions = self.get_positions()
		symbols = [letter for letter in symbols]
		return symbols, positions

	def get_corners(self):
		"""
		TopLeft / TopRight / BotLeft / BotRight
		"""
		corners = [self.pos - 1 - self.width]

		if self.orientation == Orientation.HORIZONTAL:
			corners.append(self.pos + 2 - self.width)
			corners.append(self.pos - 1 + self.width)
			corners.append(self.pos + 2 + self.width)

		elif self.orientation == Orientation.VERTICAL:
			corners.append(self.pos + 1 - self.width)
			corners.append(self.pos - 1 + (self.width * 2))
			corners.append(self.pos + 1 + (self.width * 2))

		return corners

	def get_edges(self):
		"""
		Clockwise around the sausage. 6 in total.
		"""
		edges = [self.pos - self.width] # Top part
		if self.orientation == Orientation.HORIZONTAL:
			edges.append(self.pos - self.width + 1)
			edges.append(self.pos + 2)
			edges.append(self.pos + self.width + 1)
			edges.append(self.pos + self.width)
			edges.append(self.pos - 1)
		elif self.orientation == Orientation.VERTICAL:
			edges.append(self.pos + 1)
			edges.append(self.pos + self.width + 1)
			edges.append(self.pos + (self.width * 2))
			edges.append(self.pos + self.width - 1)
			edges.append(self.pos - 1)
		return edges

	def get_positions(self):
		return [self.pos, self.orientation.walk(self.pos, self.width)]

	def update_pos(self, pos):
		self.pos = pos

	def cook(self, index):
		if self.flip_side == 1:
			index += 2
		values = [int(letter) for letter in self.sides]
		values[index] += 1

		# Rebuild string and check whether burned
		cook_status_string = ""
		for number in values:
			if number > 1:
				self.burned = True
			cook_status_string += str(number)
		self.sides = cook_status_string

	def move(self, force):
		update_pos = self.act(force)
		if self.orientation == Orientation.HORIZONTAL:
			if force == Move.LEFT:
				return [force], [update_pos], update_pos
			elif force == Move.RIGHT:
				return [force], [self.observe(force, update_pos)], update_pos
			else:
				self.flip()
				return [force, force], [update_pos, self.observe(force.perpendicular(), update_pos)], update_pos
		elif self.orientation == Orientation.VERTICAL:
			if force == Move.UP:
				return [force], [update_pos], update_pos
			elif force == Move.DOWN:
				return [force], [self.observe(force, update_pos)], update_pos
			else:
				self.flip()
				return [force, force], [update_pos, self.observe(force.perpendicular(), update_pos)], update_pos

	def score(self):
		largest_pos = self.width * self.height
		padding = len(str(largest_pos))
		return f"2{self.orientation.value}{self.flip_side}{self.sides}{self.pos:0>{padding}}"

class Player(Entity):
	def __init__(self, map_dim, pos, facing, zpos=1, id = -1, holding=0):
		super().__init__(map_dim, pos, zpos=zpos, id=id)
		self.facing = facing
		self.holding = holding			# Entity Reference: 0 means none
		self.prior_move = facing		# May not be important

	def get_symbols(self):
		# TODO: In water?
		symbols = "PF"
		positions = self.get_positions()
		symbols = [letter for letter in symbols]
		return symbols, positions

	def get_fork_position(self):
		return self.act(self.facing)

	def get_positions(self):
		return [self.pos, self.act(self.facing)]

	def move_walk(self, force):
		self.pos = self.act(force)
		self.prior_move = force
		if force == self.facing:
			return [force], [self.act(force)], Action.WALK
		else:
			return [force], [self.pos], Action.WALK

	def move_rotate(self, force):
		fork_pos = self.act(self.facing)
		first_hit_pos = self.observe(force, fork_pos)
		second_hit_pos = self.act(force)

		forces = [force, self.facing.opposite()]
		forces_pos = [first_hit_pos, second_hit_pos]

		# Update player position
		self.facing = force

		return forces, forces_pos, Action.ROTATE

	def strafe_walk(self, force):
		self.pos = self.act(force)
		if force == self.facing:
			return [], [], Action.STRAFE
		return [force], [self.pos], Action.STRAFE

	def move(self, force):
		if self.holding:
			# print("Strafe move")
			return self.strafe_walk(force)
		if force == self.facing or force.opposite() == self.facing:
			# print("Move")
			return self.move_walk(force)
		else:
			# print("Rotate")
			return self.move_rotate(force)

	def score(self):
		largest_pos = self.width * self.height
		padding = len(str(largest_pos))
		return f"1{self.holding}{self.facing.value}{self.pos:0>{padding}}"