import heapq

from Utils import *

import Map as Load
import Entities as Entity
import Tiles as Tile

transpose_skip = 0
flood_fill_skip = 0
patterns = {}
repeat_patterns = 0
pattern_ignore_player = {}
repeat_patterns_ignore_player = 0

warshall_buffer = {}
warshall_repeated = 0

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
		if initial_game.win():
			return ""
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

		if winning:
			print("\nMOVES THAT WIN")
			for moves in winning:
				print('\t', moves)

			return winning[0] 

		return False

	def play_and_record(self, moves, move_table, score_table):
		game = Load.Map(self.filename)
		move_seq = ""
		for move in moves:
			move_seq += move
			move = self.give_move(move)
			game.play(move)
			
			if move_seq not in move_table:
				move_table.append(move_seq)
				score = str(game.score())
				if score in score_table:
					# This is leading to a game that happened earlier
					global transpose_skip
					transpose_skip += 1					
					return False
				score_table.append(score)

		return game

	def Dijkstra(self):
		initial_game =  self.play_moves("")
		starting_score = initial_game.score()

		visited = [starting_score]	# Dijkstra visited
		move_table = []
		score_table = []
		completed_best = None


		search = NextAction('', self.filename)
		# moves = search.reachable(initial_game)
		moves = search.next_actions(initial_game.player.pos, initial_game.player.face_direction)
		# print(moves)
		heap = []
		for m in moves:
			heapq.heappush(heap, MinHeap(m))
		
		considerations = {}
		max_moves = len(heap[0].moves_force()[0]) + 1
		lowest = max_moves
		print(f"Checking {max_moves} moves")

		while heap:
			item = heapq.heappop(heap)
			moves, force = item.moves_force()

			# TODO: HACKY
			if force is None:
				print("Completed search - Full stats:")
				for length, total in considerations.items():
					print(f"\tMove(s): {length} Considered: {total}")
				print("")

				print(f"Least moves ({len(moves)}): {moves}")
				print(f"\t{transpose_skip=}")
				print(f"\t{flood_fill_skip=}")
				print(f"\t{repeat_patterns=}")
				print(f"\t{repeat_patterns_ignore_player=}")
				print(f"\t{warshall_repeated=}")
				return moves

			tally = len(moves) + 1
			considerations[tally] = considerations.get(tally, 0) + 1
			
			if tally != lowest:
				print(f'\tConsidered: {considerations[lowest]}')
				print(f'\tMax Depth: {max_moves}')
				print("")
				lowest = tally
				
				if completed_best and completed_best < lowest:
					continue

				print(f"Checking {lowest} moves...")

			if force == Move.UP:
				moves += "U"
			elif force == Move.DOWN:
				moves += "D"
			elif force == Move.LEFT:
				moves += "L"
			elif force == Move.RIGHT:
				moves += "R"

			game = self.play_and_record(moves, move_table, score_table)
			if not game:
				continue
			# print(f"\t{moves=}")

			score = game.score()
			if game.all_cooked():
				print("\tFound a cooked position: BFS to end...")
				print(f"\t\t{moves}")
				print('\n======= BFS SECTION ===========')
				result = self.BFS(moves)
				print('======= BFS ENDED ===========\n')
				print(f"Checking {lowest} moves...")
				if result == False:
					continue
				# TODO: Refactor code so the force is not provided and it's just moves
				# TODO: Hacky end condition
				heapq.heappush(heap, MinHeap((result, None)))
				completed_best = len(result)

			if score in visited:
				print("\tDijk - Skip")
				continue
			if game.lost():
			# if game.lost() or run_deadlock(game):
				continue

			visited.append(score)

			search = NextAction(moves, self.filename)
			# next_moves = search.reachable(game, score_table)
			next_moves = search.next_actions(game.player.pos, game.player.face_direction)
			for next_move, next_force in next_moves:
				new_move = moves + next_move
				if len(new_move) + 1 > max_moves:
					max_moves = len(new_move) + 1
				heapq.heappush(heap, MinHeap((new_move, next_force)))

	def run(self):		
		# return self.BFS() # Select Algo
		return self.Dijkstra() # Select algo

class NextAction():
	def __init__(self, start_board, filename):
		self.start_board = start_board
		self.filename = filename

	def load_game(self):
		game = Load.Map(self.filename)
		self.do_moves(game, self.start_board)

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

	def do_moves(self, game, moves, table=None):
		def give_move(letter):
			if letter == 'L':
				return Move.LEFT

			if letter == 'U':
				return Move.UP

			if letter == 'R':
				return Move.RIGHT

			if letter == 'D':
				return Move.DOWN
		success = True
		for move in moves:
			move = give_move(move)
			move_success = game.play(move)
			# print(f"\t{move_success=}")
			if table and str(game.score()) in table:
				success = False
				# print("\tFound position in table:")
				# print(game)

		if not success:
			return False
		if table:
			return True

		return game

	def reachable(self, game, score_table=None):
		# game = Load.Map(self.filename)
		# self.do_moves(game, self.start_board)
		
		visited_scores, all_moves = self.flood_fill(score_table)
		visited = []
		for score in visited_scores:
			pos = game.player.descore_position(score)
			direction = game.player.descore_direction(score)
			visited.append((pos, direction))

		plays = set()
		for sausage in game.entities:
			if isinstance(sausage, Entity.Player):
				continue

			results = self.find_target_positions(sausage, game.width)
			for target, facing, push in results:
				if (target, facing) in visited:
					index = visited.index((target, facing))
					moves = all_moves[index]
					plays.add((moves, push))

		return plays

	def next_actions(self, p_pos, p_face):
		graph, valid_positions = self.warshall()
		player_index = valid_positions.index((p_pos, p_face))
		game = Load.Map(self.filename)
		self.do_moves(game, self.start_board)
		
		plays = set()
		for sausage in game.entities[1:]:
			results = self.find_target_positions(sausage, game.width)
			for target, facing, push in results:
				if (target, facing) in valid_positions:
					move_index = valid_positions.index((target, facing))
					moves = graph[player_index][move_index][1]
					if moves is None:
						continue
					plays.add((moves, push))

		# for x in sorted(plays, key=lambda x : x[0]):
		# 	print(x)

		return plays

	def flood_fill(self, score_table=None):
		combinations = ['L', 'U', 'R', 'D']
		
		game = self.load_game()
		# print(game)
		global patterns
		global repeat_patterns
		game_str = str(game)
		if game_str in patterns:
			# print("repeat pattern")
			repeat_patterns += 1
			return patterns[game_str]
		player_score = game.player.score()

		# print("Floodfill for following:")
		visited = [game.player.score()]
		visited_moves = [""]
		queue = [letter for letter in combinations]

		global pattern_ignore_player
		global repeat_patterns_ignore_player
		game.entities = game.entities[1:]
		game_str_wo_player = str(game)
		# # THIS GIVES THE WRONG ANSWER
		# if game_str_wo_player in pattern_ignore_player:
		# 	if player_score in pattern_ignore_player[game_str_wo_player][0]:
		# 		# print("REPEAT")
		# 		repeat_patterns_ignore_player += 1
		# 		# print(game_str)
		# 		# print(game)
		# 		# print(player_score)
		# 		# print(sorted(pattern_ignore_player[game_str_wo_player][0]))
		# 		# exit(1)
		# 		return pattern_ignore_player[game_str_wo_player]

		while queue:
			moves = queue.pop(0)
			game = self.load_game()
			# print(f"Moves to floodfill - {moves}")
			# print(game)
			game_state = self.do_moves(game, moves)
			if score_table:
				# Attempt to reduce floodfill in subsequent runs
				copy_game = Load.Map(self.filename)
				copy_game = self.do_moves(copy_game, self.start_board)
				# print(f"\tCopy game, {self.start_board}: Moves to play: {moves}")
				# print(copy_game)
				result = self.do_moves(copy_game, moves, table=score_table)
				if result == False:
					global flood_fill_skip
					flood_fill_skip += 1
					# print(f"\t\tfloodskip - {moves}")
					# print(copy_game)
					continue

			if game_state.player.score() in visited:
				continue
			if game_state.lost():
				continue

			visited.append(game_state.player.score())
			visited_moves.append(moves)
			# print(f"\t{game_state.player.score()} {moves}")
			for letter in combinations:
				queue.append(moves + letter)

		# Global memory
		patterns[game_str] = (visited, visited_moves)
		pattern_ignore_player[game_str_wo_player] = (visited, visited_moves)
		return visited, visited_moves

	def find_target_positions(self, sausage, width):
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
		return list(zip(all_positions, all_face_directions, all_forces))

	def warshall(self):
		# Load map without the player
		game = self.load_game()
		game.entities = game.entities[1:]
		
		global warshall_buffer
		game_str = str(game)
		if game_str in warshall_buffer:
			global warshall_repeated
			# print("Already calculated")
			warshall_repeated += 1
			return warshall_buffer[game_str]

		width = game.width

		# Find all walls and tiles the player can stand on
		walls = [i for i, tile in enumerate(game.tiles) if isinstance(tile, Tile.Ground) and tile.zpos > 1]
		ground = [i for i, tile in enumerate(game.tiles) if isinstance(tile, Tile.Ground) and tile.zpos == 1]

		# Get all the valid tiles that the player can stand on without fork bonks
		possibilities = [Move(i) for i in range(4)]
		valid_positions = []
		for pos in ground:
			for move in possibilities:
				new_pos = calc_move(pos, move, width)
				if new_pos not in walls:
					valid_positions.append((pos, move))

		# for pos in valid_positions:
		# 	print(pos)

		# Create the graph of valid player moves for each position
		graph = []
		for y in range(len(valid_positions)):
			row = [[100000, None] for x in range(len(valid_positions))]
			row[y] = [0, ""]

			for move in possibilities:
				sim_game = self.load_game()
				p_pos, p_dir = valid_positions[y]
				sim_game.player.pos = p_pos
				sim_game.player.face_direction = p_dir
				sim_game.entities[0] = sim_game.player

				res = sim_game.play(move)
				if not res:
					continue
				if p_pos == sim_game.player.pos and p_dir == sim_game.player.face_direction:
					continue

				index = (valid_positions.index((sim_game.player.pos, sim_game.player.face_direction)))
				row[index] = [1, move_to_letter(move)]

			graph.append(row)

		# Warshall algo
		for k in range(len(valid_positions)):
			for i in range(len(valid_positions)):
				for j in range(len(valid_positions)):
					if graph[i][j][0] > graph[i][k][0] + graph[k][j][0]:
						graph[i][j][0] = graph[i][k][0] + graph[k][j][0]
						graph[i][j][1] = graph[i][k][1] + graph[k][j][1]

		# print(valid_positions)
		warshall_buffer[game_str] = (graph, valid_positions)
		return graph, valid_positions

