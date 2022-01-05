import heapq

from Utils import *

import Map as Load
import Entities as Entity
import Tiles as Tile

def is_water(game, pos):
	tile = game.find_tile(pos)
	if not tile:
		return True
	return False

def run_deadlock(game):
	can_push = sausage_push_reachable_by_player(game)
	if not can_push:
		return True
	return False

def sausage_push_reachable_by_player(game):
	over_water = find_sausages_over_water(game)
	if not over_water:
		return True

	# list of sausages
	for sausage, pos in over_water:
		overhang_direction = sausage_overhang_direction(game, sausage)
		# Check that sausage overhangs over water only
		result = water_along_direction_only(pos, overhang_direction, game)
		if result == True:
			return False

	return True

def find_sausages_over_water(game):
	over_water = []
	for entity in game.entities:
		if isinstance(entity, Entity.Sausage):
			sausage = entity
			positions = sausage.get_positions()
			head_position = positions[0]
			tail_position = positions[1]
			if is_water(game, head_position):
				if sausage.sides[0] != '1' and sausage.sides[2] != '1':
					over_water.append((sausage, head_position))
			if is_water(game, tail_position):
				if sausage.sides[1] != '1' and sausage.sides[3] != '1':
					over_water.append((sausage, tail_position))

	return over_water

def sausage_overhang_direction(game, sausage):
	positions = sausage.get_positions()
	
	# The direction of the overhang sausage
	direction = sausage_direction(sausage)
	head = positions[0]
	tail = positions[1]
	if is_water(game, head):
		direction = opposite_force(direction)

	return direction

def sausage_direction(sausage):
	if sausage.direction == Orientation.VERTICAL:
		return Move.DOWN
	elif sausage.direction == Orientation.HORIZONTAL:
		return Move.RIGHT

def water_along_direction_only(pos, overhang_direction, game):
	direction = perpendicular_force(overhang_direction)
	if direction == Move.RIGHT or direction == Move.LEFT:
		start = (pos // game.width) * game.width
		for position in range(start, start + game.width):
			if not is_water(game, position):
				return False
			if not is_water(game, calc_move(position, overhang_direction, game.width)):
				return False
	if direction == Move.UP or direction == Move.DOWN:
		start = pos % game.width
		for position in range(start, game.width * game.height, game.width):
			if not is_water(game, position):
				return False
			if not is_water(game, calc_move(position, overhang_direction, game.width)):
				return False
	return True

class MinHeap(str):
	def __init__(self, s):
		self.moves = s[0]
		self.force = s[1]

	# Overloads to make it a min-heap
	def __lt__(self, s):
		return len(self.moves) < len(s.moves)

	def __le__(self, s):
		return len(self.moves) <= len(s.moves)

	def __eq__(self, s):
		return len(self.moves) == len(s.moves)

	def __ne__(self, s):
		return len(self.moves) != len(s.moves)

	def __gt__(self, s):
		return len(self.moves) > len(s.moves)

	def __ge__(self, s):
		return len(self.moves) >= len(s.moves)


	def moves_force(self):
		return self.moves, self.force

class Algo():
	def __init__(self, filename):
		self.filename = filename

	def give_move(self, letter):
		if letter == 'L':
			return Move.LEFT

		if letter == 'U':
			return Move.UP

		if letter == 'R':
			return Move.RIGHT

		if letter == 'D':
			return Move.DOWN

	def play_moves(self, moves : str, debug=False):
		game = Load.Map(self.filename)
		for move in moves:
			move = self.give_move(move)
			game.play(move)
			if debug:
				print(game.score())
				print(str(game))
				print(f"Won? : {game.win()}")
				print(f"Lost?: {game.lost()}\n")

		return game

	def BFS(self, starting_pos=""):
		combinations = ['L', 'U', 'R', 'D']
		initial_game =  self.play_moves(starting_pos)
		starting_score = initial_game.score()

		visited = {str(starting_score) : []}
		print("Checking 1 move")

		winning = []
		queue = [starting_pos + move for move in combinations]
		max_moves = 1
		considered = -1
		while queue:
			considered += 1
			moves = queue.pop(0)
			if winning and len(moves) > len(winning[0]):
				break

			if len(moves) > max_moves:
				print(f'\tTotal considered: {considered}')
				considered = 0
				print(f"Checking {len(moves)} moves")
				max_moves = len(moves)

			game = self.play_moves(moves)
			score = game.score()
			losing = game.lost()
			win = game.win()
			if str(score) in visited:
				visited[str(score)].append(moves)
				continue
			if losing:
				continue
			if win:
				winning.append(moves)
				visited[str(score)] = [moves]
				continue

			visited[str(score)] = [moves]
			for letter in combinations:
				queue.append(moves + letter)

		print("\nMOVES THAT WIN")
		for moves in winning:
			print('\t', moves)

		return winning[0] 

	def Dijkstra(self):
		initial_game =  self.play_moves("")
		starting_score = initial_game.score()

		visited = [starting_score]
		search = NextAction('', self.filename)
		moves = search.reachable()
		# print(moves)
		heap = []
		for m in moves:
			heapq.heappush(heap, MinHeap(m))
		
		considered = 0
		max_moves = len(heap[0].moves_force()[0]) + 1
		print(f"Checking {max_moves} moves")

		while heap:
			considered += 1
			item = heapq.heappop(heap)
			moves, force = item.moves_force()
			if force == Move.UP:
				moves += "U"
			elif force == Move.DOWN:
				moves += "D"
			elif force == Move.LEFT:
				moves += "L"
			elif force == Move.RIGHT:
				moves += "R"

			if len(moves) > max_moves:
				print(f'\tTotal considered: {considered}')
				considered = 0
				print(f"Checking {len(moves)} moves")
				max_moves = len(moves)

			game = self.play_moves(moves)
			score = game.score()


			if game.all_cooked():
				print("\tFound a cooked position: BFS to end...")
				print(f"\t\t{moves}")
				result = self.BFS(moves)
				if not result:
					continue
				return result
			if score in visited:
				continue
			if game.lost():
				continue

			visited.append(score)

			search = NextAction(moves, self.filename)
			next_moves = search.reachable()
			for next_move, next_force in next_moves:
				new_move = moves + next_move
				heapq.heappush(heap, MinHeap((new_move, next_force)))

	def run(self):		
		# return self.BFS() # RDDLLULRDURURLULRU
		return self.Dijkstra() # RDDLLULDURRURLULRU

class NextAction():
	def __init__(self, start_board, filename):
		self.start_board = start_board
		self.filename = filename

	def load_game(self):
		game = Load.Map(self.filename)
		self.play_moves(game, self.start_board)

		for sausage in game.entities:
			if isinstance(sausage, Entity.Player):
				continue

		return self.replace_entities_with_walls(game)

	def replace_entities_with_walls(self, game):
		for ent in game.entities:
			if isinstance(ent, Entity.Player):
				continue
			for pos in ent.get_positions():
				game.tiles[pos] = Tile.Ground(pos, zpos=2)
		game.entities = [game.player]
		return game

	def play_moves(self, game, moves):
		def give_move(letter):
			if letter == 'L':
				return Move.LEFT

			if letter == 'U':
				return Move.UP

			if letter == 'R':
				return Move.RIGHT

			if letter == 'D':
				return Move.DOWN
		
		for move in moves:
			move = give_move(move)
			game.play(move)
		return game

	def reachable(self):
		game = Load.Map(self.filename)
		self.play_moves(game, self.start_board)
		plays = []
		for sausage in game.entities:
			if isinstance(sausage, Entity.Player):
				continue
			
			to_try = self.find_target_positions(game, sausage)
			for pos, face_direction, force in to_try:
				moves = self.reach_target(pos, face_direction)
				if moves:
					plays.append((moves, force))
				elif moves == "":
					# Already on correct position. Hence; Moves == ""
					plays.append((moves, force))

		return plays

	def reach_target(self, tpos, direction):
		combinations = ['L', 'U', 'R', 'D']
		
		game = self.load_game()
		# Possible that you are already there
		if game.player.pos == tpos and game.player.face_direction == direction:
			return ""

		visited = [game.player.score()]
		queue = [letter for letter in combinations]
		found = False
		while queue:
			moves = queue.pop(0)
			game = self.load_game()
			game_state = self.play_moves(game, moves)
			if game_state.player.score() in visited:
				continue
			if game_state.lost():
				continue
			if game_state.player.pos == tpos and game_state.player.face_direction == direction:
				found = True
				break

			visited.append(game_state.player.score())
			
			for letter in combinations:
				queue.append(moves + letter)

		if not found:
			return None

		return moves

	def find_target_positions(self, sausage, width):
		# def add(list_positions, pos, moves_towards, width, face_in, push_direction):
		# 	for move in moves_towards:
		# 		pos = calc_move(pos, move, width)
			
		# 	# Can player even stand there?
		# 	stand_tile = game.find_tile(pos)
		# 	if not stand_tile:
		# 		return
		# 	if not isinstance(stand_tile, Tile.Ground):
		# 		return
		# 	if stand_tile.zpos > 1:
		# 		return

		# 	# Can player face there?
		# 	face_pos = calc_move(pos, face_in, width)
		# 	face_tile = game.find_tile(face_pos)
		# 	if not face_tile:
		# 		pass # Fork over water is fine
		# 	elif isinstance(face_tile, Tile.Ground) and face_tile.zpos > 1:
		# 		return # Fork would be in wall
			
		# 	if face_in == push_direction or opposite_force(face_in) == push_direction:
		# 		# Is player able to push?
		# 		push_pos = calc_move(pos, push_direction, width)
		# 		push_tile = game.find_tile(push_pos)
		# 		if not push_tile:
		# 			return
		# 	else:
		# 		# Can player rotate?
		# 		rotate_pos = calc_move(pos, face_in, width)
		# 		rotate_pos = calc_move(rotate_pos, push_direction, width)
		# 		rotate_tile = game.find_tile(rotate_pos)
		# 		if not rotate_tile:
		# 			pass
		# 		elif isinstance(rotate_tile, Tile.Ground):
		# 			if rotate_tile.zpos > 1:
		# 				return

		# 	list_positions.append((pos, face_in, push_direction))

		# Corners are defined the same for both sausages
		corners = sausage.get_corners() * 2
		corner_directions = [
			Move.RIGHT, Move.LEFT, Move.RIGHT, Move.LEFT,
			Move.DOWN, Move.DOWN, Move.UP, Move.UP
		]
		corner_forces = [
			Move.DOWN, Move.DOWN, Move.UP, Move.UP,
			Move.RIGHT, Move.LEFT, Move.RIGHT, Move.LEFT
		]

		# Edges are slightly different depending on the orientation
		edges = sausage.get_edges() * 3
		print(f"{edges=}")
		if sausage.direction == Orientation.HORIZONTAL:
			edge_directions = [
				Move.UP, Move.UP, Move.RIGHT, Move.DOWN, Move.DOWN, Move.LEFT, # Normals
				Move.RIGHT, Move.RIGHT, Move.DOWN, Move.LEFT, Move.LEFT, Move.UP,
				Move.LEFT, Move.LEFT, Move.UP, Move.RIGHT, Move.RIGHT, Move.DOWN
			]
			edge_forces = [
				Move.DOWN, Move.DOWN, Move.LEFT, Move.UP, Move.UP, Move.RIGHT,
			] * 3
		elif sausage.direction == Orientation.VERTICAL:
			edge_directions = [
				Move.UP, Move.RIGHT, Move.RIGHT, Move.DOWN, Move.LEFT, Move.LEFT, # Normals
				Move.RIGHT, Move.DOWN, Move.DOWN, Move.LEFT, Move.UP, Move.UP,
				Move.LEFT, Move.UP, Move.UP, Move.RIGHT, Move.DOWN, Move.DOWN
			]
			edge_forces = [
				Move.DOWN, Move.LEFT, Move.LEFT, Move.UP, Move.RIGHT, Move.RIGHT
			] * 3

		# Extended positions
		extended = []
		extended_directions = []
		extended_forces = []
		for pos, normal in zip(edges[:6], edge_directions[:6]):
			extended.append(calc_move(pos, normal, width))
			opposite = opposite_force(normal)
			extended_directions.append(opposite)
			extended_forces.append(opposite)

		all_positions = corners + edges + extended
		all_face_directions = corner_directions + edge_directions + extended_directions
		all_forces = corner_forces + edge_forces + extended_forces
		print(f"{len(all_positions)=} {len(all_face_directions)=} {len(all_forces)=}")
		return list(zip(all_positions, all_face_directions, all_forces))