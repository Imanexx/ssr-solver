from Utils import *
import Entities as Entity
import Tiles as Tile

class Engine():
	def __init__(self, basemap, scores):
		tiles, width, height, win_pos, win_dir = basemap.copy()
		self.width = width
		self.height = height
		self.tiles = tiles
		self.player = None # Gets set below
		self.entities = [] # Gets populated below 
		self.decode(scores)
		self.position = scores	# Used for reverting
		self.win_pos = win_pos
		self.win_dir = win_dir

	def complete(self):
		if self.player.pos != self.win_pos:
			return False
		if self.player.facing != self.win_dir:
			return False
		return self.win()

	def win(self):
		""" NOTE: DOES NOT CONSIDER PLAYER POSITION """
		for ent in self.entities:
			if ent.in_water:
				return False
			if isinstance(ent, Entity.Sausage):
				if ent.is_cooked() == False:
					return False
		return True

	def loss(self):
		# Assumption is sausages
		for ent in self.entities:
			if ent.in_water:
				return True
			if ent.burned:
				return True
		return False

	def revert(self):
		self.player = None
		self.entities = []
		self.decode(self.position)
		return False

	def rescore(self):
		self.position = [self.player.score()]
		for ent in self.entities:
			self.position.append(ent.score())

	def decode(self, scores):
		map_dim = (self.width, self.height)
		
		# Init player
		pscore = scores[0]
		holding = int(pscore[1])
		facing = Move(int(pscore[2]))
		position = int(pscore[3:])
		self.player = Entity.Player(map_dim, position, facing, holding=holding)

		# Init entities
		for id, escore in enumerate(scores[1:]):
			if escore[0] == '2': # Sausage
				orientation = Orientation(int(escore[1]))
				flip = int(escore[2])
				sides = str(escore[3:7])
				position = int(escore[7:])

				# TODO: This has some hacky effects with revert()
				disable_turn = False
				if holding == id + 1:
					disable_turn = True
				self.entities.append(Entity.Sausage(map_dim, position, orientation, id=id+1, flip_side=flip, sides=sides, disable_turn=disable_turn))
			else:
				print(f"{id+1} Unknown score: {escore}")
				exit(1)

	def __repr__(self):
		import re
		symbols = []
		positions = []
		if self.player is not None:
			psym, ppos = self.player.get_symbols()
			symbols += psym
			positions += ppos
		for entity in self.entities:
			chars, pos = entity.get_symbols()
			symbols += chars
			positions += pos

		output = ""
		for y in range(self.height):
			for x in range(self.width):
				pos = calc_pos(y, x, self.width)
				
				# Check table of symbols first
				if pos in positions:
					index = positions.index(pos)
					output += symbols[index]
				else:
					tile = self.tiles[pos]
					if not tile:
						output+= ' ' # water
					else:
						output += str(self.tiles[pos])
			output+= '\n'

		space_width = ' ' * self.width + '\n'
		output = re.sub(space_width, '', output)
		return output


	def entity_collides_with_world(self, entity):
		for pos in entity.get_positions():
			tile = self.tiles[pos]
			if not tile:
				continue
			# Wall
			if tile.zpos > 1:
				return True
		return False

	def entity_in_water(self, entity):
		if isinstance(entity, Entity.Player):
			if self.tiles[entity.pos] is None:
				return True
			return False
		# TODO: HACKY
		if entity.disable_turn:
			return False
		positions = entity.get_positions()
		for pos in positions:
			if self.tiles[pos]:
				return False
		return True

	def find_entity(self, pos):
		for ent in self.entities:
			if pos in ent.get_positions():
				return ent
		return None

	def grill_interact(self, entity):
		for index, pos in enumerate(entity.get_positions()):
			tile = self.tiles[pos]
			if isinstance(tile, Tile.Grill):
				result = tile.interact(entity, index)

				if isinstance(entity, Entity.Player) and result:
					# Better move the object the player is holding too
					if self.player.holding:
						sausage = self.entities[self.player.holding - 1]
						_, __, pos = sausage.move(self.player.prior_move)
						sausage.update_pos(pos)

	def apply_forces(self, forces, fpos):
		failures = []	# Failure buffer - collision is more important than drowning
		for force, pos in zip(forces, fpos):
			entity = self.find_entity(pos)
			if entity is None:
				# No entities on tile - ignore
				continue

			# Move entity - Apply forces on new square - Then update entity position
			nforces, npos, entity_pos = entity.move(force) # n = new
			failure = self.apply_forces(nforces, npos)	# Recurse
			entity.update_pos(entity_pos)
			
			# Did entities moved by entity cause failures
			if failure.value:
				failures.append(failure)
			
			# World collision
			if self.entity_collides_with_world(entity):
				return Failure.COLLISION
			if self.entity_in_water(entity):
				entity.in_water = True
				return Failure.DROWNED

			# Entity moved w/o problems - interact with tiles
			self.grill_interact(entity)


		# All entities moved without problems
		if not failures:
			return Failure.NONE
		
		# TODO: Entities caused collisions - Need to revert if sausage stab
		if failure.COLLISION in failures:
			return failure.COLLISION

		# TODO: Presumption
		return failure.DROWNED

	def play(self, move):
		forces, fpos, action = self.player.move(move)
		# General world collision
		if self.entity_in_water(self.player):
			return self.revert()
		if self.entity_collides_with_world(self.player):
			if action != action.ROTATE:
				return self.revert()
			# else rotate and then allow bonk
			self.revert()
		
		# Special Player considerations
		# Avoid fork phase
		if action == Action.ROTATE:
			tile = self.tiles[fpos[0]]
			if tile and tile.zpos > 1:
				return self.revert()
		elif action == Action.STRAFE:
			# Move the entity
			sausage = self.entities[self.player.holding - 1]
			collides = self.apply_forces([move], [sausage.pos])
			if collides.value:
				if move == self.player.facing.opposite():
					# UNSTICK
					self.revert()			# Ignore sausage move
					sausage = self.entities[self.player.holding - 1] # Note: Revert changes reference to sausage. See TODO in engine if it hasn't been addressed differently
					sausage.enable()
					self.player.holding = 0
					self.player.move(move)	# Move player
				else: # COLLISION
					return self.revert()
			# print(sausage)

		# Apply forces influenced by the player
		failure = self.apply_forces(forces, fpos)

		# What are the reactions from this movement
		if failure == failure.COLLISION:
			if action == Action.WALK:
				# Sausage Stab
				if self.player.facing == move:
					self.revert()
					self.player.move(move)
					fork_pos = self.player.get_fork_position()
					entity = self.find_entity(fork_pos)
					entity.disable()
					self.player.holding = entity.id
				# Backed into entities that can't move
				else:
					return self.revert()
			elif action == Action.ROTATE:			
				# Try BONK force action only
				self.revert()
				failure = self.apply_forces([forces[0]], [fpos[0]])
				if failure.value:
					# Still failed
					return self.revert()
				# Else valid bonk action
			else:
				# Collided
				return self.revert()
		elif failure == failure.DROWNED:
			# print("Entity Drowned")
			return self.revert()

		# Make player interact with tiles
		self.grill_interact(self.player)


		# TODO HACKY
		# t_fork_pos = self.player.get_fork_position()
		# if action == action.STRAFE and self.player.holding == 0 and self.find_entity(t_fork_pos):
		# 	print(self.find_entity(t_fork_pos).pos, t_fork_pos)
		# 	print("UNSTICK ENTITY - STEPPED ON GRILL - RESTUCK")
		# 	exit(1)
		# Success
		self.rescore()
		return True

if __name__ == '__main__':
	import BaseMap
	basemap = BaseMap.LoadMap('maps/twisty_farm')
	engine = Engine(basemap, basemap.scores())
	print(engine)
	for i, move in enumerate([Move.DOWN, Move.DOWN, Move.LEFT, Move.RIGHT, Move.DOWN, Move.DOWN, Move.RIGHT, Move.LEFT, Move.UP, Move.UP, Move.RIGHT, Move.RIGHT, Move.RIGHT, Move.LEFT, Move.LEFT, Move.UP, Move.RIGHT, Move.RIGHT, Move.UP, Move.UP, Move.LEFT, Move.UP, Move.LEFT, Move.UP, Move.UP, Move.RIGHT, Move.RIGHT, Move.UP, Move.RIGHT, Move.UP, Move.RIGHT, Move.RIGHT, Move.RIGHT, Move.UP, Move.RIGHT, Move.RIGHT, Move.RIGHT, Move.RIGHT, Move.RIGHT, Move.RIGHT, Move.RIGHT, Move.RIGHT, Move.RIGHT, Move.DOWN, Move.RIGHT, Move.DOWN, Move.UP, Move.LEFT, Move.LEFT, Move.DOWN, Move.LEFT, Move.LEFT, Move.LEFT, Move.LEFT, Move.DOWN, Move.DOWN, Move.RIGHT, Move.RIGHT, Move.RIGHT, Move.UP, Move.RIGHT, Move.UP, Move.RIGHT, Move.RIGHT, Move.UP, Move.RIGHT, Move.RIGHT, Move.DOWN, Move.DOWN, Move.DOWN, Move.DOWN, Move.DOWN, Move.DOWN, Move.DOWN, Move.DOWN, Move.DOWN, Move.DOWN, Move.DOWN, Move.DOWN, Move.DOWN]):
		print(f"{i} {move=}")
		print(engine.play(move))
		print(f"{engine.position} {engine.win()=} {engine.complete()=}")
		# print(engine)
		if i == 32:
			break
		# engine = Engine(basemap, engine.position)

	print(engine)
	print(engine.position)


	# basemap = BaseMap.LoadMap('maps/twisty_farm')
	# engine = Engine(basemap, ['101230', '2100000200', '2010000232'])
	# print(engine)
	# print(engine.play(Move.RIGHT))
	# print(engine)
