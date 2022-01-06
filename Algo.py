import heapq

from Utils import *

import Map as Load
import Entities as Entity
import Tiles as Tile

transpose_skip = 0
warshall_buffer = {}
warshall_repeated = 0

def output(str_out, supress=False):
	if not supress:
		print(str_out)

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
		self.moves = s

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


	def heap_move(self):
		return self.moves

class Algo():
	def __init__(self, filename):
		self.filename = filename

	def play_moves(self, moves : str, debug=False):
		game = Load.Map(self.filename)
		for move in moves:
			move = letter_to_move(move)
			game.play(move)
			if debug:
				print(game.score())
				print(str(game))
				print(f"Won? : {game.win()}")
				print(f"Lost?: {game.lost()}\n")

		return game

	def BFS(self, starting_pos="", supress_output=False):
		combinations = ['L', 'U', 'R', 'D']
		initial_game =  self.play_moves(starting_pos)
		if initial_game.win():
			return ""
		starting_score = initial_game.score()

		visited = {str(starting_score) : []}
		output("Checking 1 move", supress=supress_output)

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
				output(f'\tTotal considered: {considered}', supress=supress_output)
				considered = 0
				output(f"Checking {len(moves)} moves", supress=supress_output)
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
			print(f"\nLeast Moves: {len(moves) - 1}")
			for moves in winning:
				print('\t', moves)

			return winning[0] 

		return False

	def play_and_record(self, moves, move_table, score_table):
		game = Load.Map(self.filename)
		move_seq = ""
		for move in moves:
			move_seq += move
			move = letter_to_move(move)
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
		moves = search.reachable(initial_game.player.pos, initial_game.player.face_direction)
		print(sorted(moves,key=lambda x : len(x)))
		heap = []
		for m in moves:
			heapq.heappush(heap, MinHeap(m))
		considerations = {}
		max_moves = len(heap[0].heap_move())
		lowest = max_moves
		print(f"Checking {max_moves} moves")

		print(f"{heap=}")

		while heap:
			moves = heapq.heappop(heap).heap_move()
			tally = len(moves)
			considerations[tally] = considerations.get(tally, 0) + 1
			
			if tally != lowest:
				print(f'\tConsidered: {considerations[lowest]}')
				print(f'\tMax Depth: {max_moves}')
				print("")
				lowest = tally
				
				if completed_best and completed_best < lowest:
					continue

				print(f"Checking {lowest} moves...")

			game = self.play_and_record(moves, move_table, score_table)
			if not game:
				continue
			
			# TODO: HACKY
			if game.win():
				print("Completed search - Full stats:")
				for length, total in considerations.items():
					print(f"\tMove(s): {length} Considered: {total}")
				print("")

				print(f"Least moves ({len(moves)}): {moves}")
				print(f"\t{transpose_skip=}")
				print(f"\t{warshall_repeated=}")
				return moves
			elif completed_best and len(moves) >= completed_best:
				print("No way to win with this because a prior sequence was better.")
				continue

			if not game:
				continue

			score = game.score()
			if game.all_cooked():
				print("\tFound a cooked position: BFS to end...")
				print(f"\t\t{moves}")
				print('\n======= BFS SECTION ===========')
				result = self.BFS(moves, supress_output=True)
				print('\n======= BFS ENDED ===========\n')
				print(f"Checking {lowest} moves...")
				if result == False:
					continue
				# TODO: Hacky end condition
				heapq.heappush(heap, MinHeap(result))
				completed_best = len(result)

			if score in visited:
				print("\tDijk - Skip")
				exit(1)
				continue
			if game.lost():
			# if game.lost() or run_deadlock(game):
				continue

			visited.append(score)

			search = NextAction(moves, self.filename)
			next_moves = search.reachable(game.player.pos, game.player.face_direction)
			# print(f"{next_moves=}")
			# print(f"{heap=}")
			
			for next_move in next_moves:
				new_move = moves + next_move
				if len(new_move) > max_moves:
					max_moves = len(new_move)
				heapq.heappush(heap, MinHeap(new_move))
				
				# print(f"\t\t{new_move=}")
			# print(f"{heap=}")
			# exit(1)

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
		success = True
		for move in moves:
			move = letter_to_move(move)
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

	def reachable(self, p_pos, p_face):
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
					moves += move_to_letter(push)
					plays.add(moves)

		return plays

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

		warshall_buffer[game_str] = (graph, valid_positions)
		return graph, valid_positions

