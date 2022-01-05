from abc import ABC, abstractmethod
from Utils import *

import Map
import Tiles as Tile

class Entity(ABC):
	def __init__(self, pos, zpos=1, id = -1):
		self.id = id
		self.pos = pos
		self.zpos = zpos
		self.symbol = '?'
		self.game = None
		self.in_water = False

	# Must be called after map loads all entities
	def set_map(self, game : Map):
		self.game = game

	def pos_move(self, pos, force) -> int:
		return calc_move(pos, force, self.game.width)

	def world_collision(self, pos):
		# Need to do zpos handling
		tile = self.game.find_tile(pos)
		if not tile:
			return False
		if isinstance(tile, Tile.Ground):
			if tile.zpos > 1:
				return True
		return False

	def water_check(self, pos):
		tile = self.game.find_tile(pos)
		return not tile

	def push(self, pos, force, check=False, ignore_player=False):
		entity = self.game.find_entity_with_position(pos, ignore_player=ignore_player)
		if entity:
			return entity.move(force, check=check, ignore_player=ignore_player)
		return True

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
	def __init__(self, pos, direction : Orientation, zpos=1, id = -1):
		super().__init__(pos, zpos=zpos, id=id)
		self.direction = direction
		self.flip_side = 0
		self.disable_turn = False
		self.sides = "0000" # Uncooked = 0000; Cooked = 1111; Burned contains >2
		self.burned = False # Set when burned

	def get_symbols(self):
		if self.in_water:
			symbols = 'zz'
		elif self.direction == Orientation.HORIZONTAL:
			symbols = '><'
		elif self.direction == Orientation.VERTICAL:
			symbols = 'v^'

		positions = self.get_positions()
		symbols = [letter for letter in symbols]
		return symbols, positions

	def get_tail_position(self):
		if self.direction == Orientation.HORIZONTAL:
			move = Move.RIGHT
		elif self.direction == Orientation.VERTICAL:
			move = Move.DOWN
		return self.pos_move(self.pos, move)

	def get_positions(self):
		return [self.pos, self.get_tail_position()]

	def get_corners(self):
		"""
		TopLeft / TopRight / BotLeft / BotRight
		"""
		corners = [self.pos - 1 - self.game.width]

		if self.direction == Orientation.HORIZONTAL:
			corners.append(self.pos + 2 - self.game.width)
			corners.append(self.pos - 1 + self.game.width)
			corners.append(self.pos + 2 + self.game.width)

		elif self.direction == Orientation.VERTICAL:
			corners.append(self.pos + 1 - self.game.width)
			corners.append(self.pos - 1 + (self.game.width * 2))
			corners.append(self.pos + 1 + (self.game.width * 2))

		return corners

	def get_edges(self):
		"""
		Clockwise around the sausage. 6 in total.
		"""
		edges = [self.pos - self.game.width] # Top part
		if self.direction == Orientation.HORIZONTAL:
			edges.append(self.pos - self.game.width + 1)
			edges.append(self.pos + 2)
			edges.append(self.pos + self.game.width + 1)
			edges.append(self.pos + self.game.width)
			edges.append(self.pos - 1)
		elif self.direction == Orientation.VERTICAL:
			edges.append(self.pos + 1)
			edges.append(self.pos + self.game.width + 1)
			edges.append(self.pos + (self.game.width * 2))
			edges.append(self.pos + self.game.width - 1)
			edges.append(self.pos - 1)
		return edges


	def score(self):
		# TODO - DO PROPER PADDING
		parity = self.flip_side
		score = int(f"{self.pos}{parity}{self.sides}")
		return score

	def flip(self):
		if self.disable_turn:
			return
		self.flip_side = self.flip_side ^ 1

	def cook(self, index):
		"""
		index is either: 0, 1 to indicate HEAD/TAIL
		0 - FLIP 0 (HEAD)
		1 - FLIP 0 (TAIL)
		2 - FLIP 1 (HEAD)
		3 - FLIP 1 (TAIL)
		"""
		if self.flip_side == 1:
			index += 2

		values = [int(letter) for letter in self.sides]
		values[index] += 1
		# Rebuild string and check whether burned
		out_string = ""
		for number in values:
			if number > 1:
				self.burned = True
			out_string += str(number)
		self.sides = out_string

	def interact(self):
		water_counter = 0
		for i, pos in enumerate(self.get_positions()):
			tile = self.game.find_tile(pos)
			if not tile:
				water_counter += 1
				continue
			if isinstance(tile, Tile.Grill):
				self.cook(i)
		if water_counter == 2:
			self.in_water = True

	def two_move(self, force, check=False, ignore_player=False):
		# Need to verify that the move is allowed first
		head_move = self.pos_move(self.pos, force)
		tail_move = self.pos_move(self.get_tail_position(), force)

		if self.world_collision(head_move) or self.world_collision(tail_move):
			return False

		# Allowed to push both squares at the same time
		head_pushed = self.push(head_move, force, check=True, ignore_player=ignore_player)
		tail_pushed = self.push(tail_move, force, check=True, ignore_player=ignore_player)
		if head_pushed == False or tail_pushed == False:
			return False
		elif check:
			return True

		head_pushed = self.push(head_move, force=force, ignore_player=ignore_player)
		tail_pushed = self.push(tail_move, force=force, ignore_player=ignore_player)

		# UPDATE
		if not check:
			self.pos = head_move
			self.flip()
			self.interact()

		return True

	def move(self, force : Move, check=False, ignore_player=False):
		if force == Move.LEFT or force == Move.RIGHT:
			if self.direction == Orientation.VERTICAL:
				return self.two_move(force, check, ignore_player)
		if force == Move.DOWN or force == Move.UP:
			if self.direction == Orientation.HORIZONTAL:
				return self.two_move(force, check=check, ignore_player=ignore_player)

		# Simple move
		if force == Move.LEFT or force == Move.UP:
			head_adj_pos = self.pos_move(self.pos, force)
			if self.world_collision(head_adj_pos):
				return False

			moved = self.push(head_adj_pos, force, check, ignore_player)
			if not moved:
				return False

		else: # RIGHT / DOWN
			tail_pos = self.get_tail_position()
			tail_adj_pos = self.pos_move(tail_pos, force)
			
			if self.world_collision(tail_adj_pos):
				return False

			moved = self.push(tail_adj_pos, force, check, ignore_player)
			if not moved:
				return False

		# UPDATE
		if not check:
			self.pos = self.pos_move(self.pos, force)
			self.interact()

		return True

class Player(Entity):
	def __init__(self, pos, face_direction : Move, zpos=1, id = -1):
		super().__init__(pos, zpos=zpos, id=id)
		self.face_direction = face_direction
		self.last_movement = None
		self.last_action = None
		self.holding = None # Has reference to the ent it holds

	def get_symbols(self):
		if False:
			pass
		# if self.in_water:
		# 	symbols = 'pf'
		else:
			symbols = "PF"
		positions = self.get_positions()
		symbols = [letter for letter in symbols]
		return symbols, positions

	def fork_position(self):
		return self.pos_move(self.pos, self.face_direction)

	def get_positions(self) -> list:
		return [self.pos, self.fork_position()]

	def score_padding(self):
		return len(str(self.game.height * self.game.width))

	def score(self):
		padding = self.score_padding()

		holding = 0
		if self.holding:
			holding = 1

		# Note: Leading '1' is there so int conversion doesn't throw away leading 0's
		return int(f"1{self.face_direction.value}{holding}{self.pos:0>{padding}}")

	def descore_position(self, score):
		padding = self.score_padding()
		return int(str(score)[-padding:])

	def descore_direction(self, score):
		return Move(int(str(score)[1]))

	def stick_sausage(self, entity):
		self.holding = entity
		self.holding.disable_turn = True

	def unstick_sausage(self):
		self.holding.disable_turn = False
		self.holding = None

	def interact(self, ignore_stuck=False):
		tile = self.game.find_tile(self.pos)
		if isinstance(tile, Tile.Grill):
			self.pos = self.pos_move(self.pos, opposite_force(self.last_movement))
			if self.holding and ignore_stuck == False:
				# Move the sausage back as well
				self.holding.move(opposite_force(self.last_movement), check=False, ignore_player=True)
				
	def move(self, force : Move) -> bool:
		# Need to set appropriate state flags for dude's state
		if self.holding:
			return self.hold_move(force)
		elif force != self.face_direction and force != opposite_force(self.face_direction):
			return self.rotate_move(force)
		else:
			return self.normal_move(force)

	def rotate_move(self, force) -> bool:
		# PHASE ONE
		fork_pos = self.fork_position()
		adj_fork_pos = self.pos_move(fork_pos, force)

		if self.world_collision(adj_fork_pos):
			# No way to turn
			return False

		if not self.push(adj_fork_pos, force):
			# Entity is block the fork
			return False

		# PHASE TWO - Checking for bonks
		adj_player = self.pos_move(self.pos, force)
		adj_force = opposite_force(self.face_direction)

		if self.world_collision(adj_player):
			# This is a bonk movement
			return True # Technically could have moved something???
		
		if not self.push(adj_player, adj_force):
			# Entity that can't move is bonking the fork
			return True # Technically could have moved something???

		# Completed a full turn
		self.face_direction = force
		self.last_action = Action.ROTATE
		self.last_movement = None

		return True

	def normal_move(self, force : Move) -> bool:
		if force == self.face_direction:
			fork_pos = self.fork_position()
			ahead_of_fork = self.pos_move(fork_pos, force)
			if self.water_check(fork_pos):
				return False # Cannot step into water
			if self.world_collision(ahead_of_fork):
				return False
			
			entity = self.game.find_entity_with_position(ahead_of_fork)
			if entity:
				moved = entity.move(force)
				if not moved and isinstance(entity, Sausage):
					# To trigger holding sausage
					self.stick_sausage(entity)
				elif not moved:
					# Some other entity is blocking the way
					return False
				# Else whatever the entity is was pushed

			self.pos = fork_pos
			self.last_movement = force
			self.last_action = Action.WALK

		if force == opposite_force(self.face_direction):
			behind_player = self.pos_move(self.pos, force)
			if self.water_check(behind_player):
				return False # Cannot step into water
			if self.world_collision(behind_player):
				return False

			if not self.push(behind_player, force):
				return False # Entity in the way that can't move

			self.pos = behind_player
			self.last_movement = force
			self.last_action = Action.WALK

		# Interact after taking a step
		self.interact(ignore_stuck=True)

		return True

	def hold_move(self, force : Move) -> bool:
		# Unstuck logic first
		if force == opposite_force(self.face_direction):
			if not self.normal_move(force):
				return False
			# # player collision check
			# behind_player = self.pos_move(self.pos, force)
			# if self.water_check(behind_player):
			# 	return False # Cannot step into water

			# if self.world_collision(behind_player):
			# 	return False

			# if not self.push(behind_player, force):
			# 	return False # Entity in the way that can't move

			# Player is able to move; Move sausage if possible / otherwise unstick
			sausage = self.holding
			can_move = sausage.move(force, check=False, ignore_player=True)
			if not can_move:
				self.unstick_sausage()

			return True

		if force == self.face_direction:
			# See if sausage blocks player movement
			sausage = self.holding
			can_move = sausage.move(force, check=True, ignore_player=True)
			if not can_move:
				return False

			# Sausage can move - Try moving player: Possibly a gap in the way?
			if not self.normal_move(force):
				return False

			# Actually move sausage now
			sausage.move(force, check=False, ignore_player=True)

			return True

		# Strafe Player
		# Player Collision Checks
		player_adj_pos = self.pos_move(self.pos, force)
		if self.water_check(player_adj_pos):
			return False # Cannot step into water
		if self.world_collision(player_adj_pos):
			return False

		# Sausage collision
		sausage = self.holding
		can_move = sausage.move(force, check=False, ignore_player=True)
		if not can_move:
			return False

		# Update
		self.pos = self.pos_move(self.pos, force)
		self.last_movement = force
		self.last_action = Action.WALK

		self.interact()
		return True
