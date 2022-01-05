from Utils import *

import Entities as Entity
from Algo import Algo, NextAction

from Loader import load_map

class Map():
	def __init__(self, file_name):
		tiles, ents, width, height = load_map(file_name)
		self.width = width
		self.height = height
		self.tiles = tiles		# Flattened tilemap of the game
		self.entities = ents	# Entities containing positions
		player_ent = None
		for ent in self.entities:
			ent.set_map(self)	# Give all entities access to map
			# self.gravity(ent)
			if isinstance(ent, Entity.Player):
				player_ent = ent

		self.player = player_ent
		self.start = player_ent.score() # This needs to be changed

	def __repr__(self):
		symbols = []
		positions = []
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

		import re
		space_width = ' ' * self.width + '\n'
		output = re.sub(space_width, '', output)
		return output

	def play(self, force : Move) -> bool:
		""" move the player """
		return self.player.move(force)

	def find_entity_with_position(self, pos, ignore_player=False):
		for ent in self.entities:
			if ignore_player and isinstance(ent, Entity.Player):
				continue
			positions = ent.get_positions()
			if pos in positions:
				return ent
		return None

	def find_tile(self, pos):
		return self.tiles[pos]

	def score(self):
		scores = []
		for ent in self.entities:
			scores.append(ent.score())
		return scores

	def win(self):
		if self.player.score() != self.start:
			return False

		cooked = self.all_cooked()
		if not cooked:
			return False

		return True

	def all_cooked(self):
		for ent in self.entities:
			if isinstance(ent, Entity.Sausage):
				if ent.sides != '1111':
					return False
		return True

	def lost(self):
		for ent in self.entities:
			if isinstance(ent, Entity.Sausage):
				if ent.burned:
					return True
				if ent.in_water:
					return True
		return False

# MAP_NAME = 'maps/beautiful_horizon'
MAP_NAME = 'maps/southjaunt'

if __name__ == "__main__":
	game = Map(MAP_NAME)
	print(game.width)
	print(game.player.score())
	print(game)

	# search = NextAction("", MAP_NAME)
	# visited, moves = search.flood_fill()
	# print(len(visited), len(moves))
	# visited = sorted(list(zip(visited, moves)), key=lambda x : int(str(x[0])[-3:]))
	# print(visited)
	# for pos, moves in visited:
	# 	print(game.player.descore_position(pos), moves)
	
	# print("")

	# moves = search.reachable()
	# print(moves)

	# poss = search.find_target_positions(game.entities[1], game.width)
	# for pos, face, force in (sorted(poss, key=lambda x : x[0])):
	# 	print(f"{pos} {face:10} {force}")

	algo = Algo(MAP_NAME)
	moves = algo.run()
	print(game)
	# score, win, lost = algo.play_moves(moves, debug=True)
	
	# bfs = NextAction('D', MAP_NAME)
	# moves = bfs.reachable()
	# print(moves)

