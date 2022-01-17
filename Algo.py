from Utils import *
from collections import deque
import heapq

import BaseMap
import Engine as Eng
import Tiles as Tile

class MinHeap(str):
	def __init__(self, s):
		self.moves = s[0]
		self.score = s[1]

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

	def heap_score(self):
		return self.score

class Algo():
	def __init__(self, filename):
		self.basemap = BaseMap.LoadMap(filename)
		self.warshall_buffer = {}

	def list_moves(self, moves):
		move_letters = ""
		for move in moves:
			move_letters += move.letter()
		return move_letters

	def BFS(self, starting_state=None, stats=True):
		if not starting_state:
			# Default to the beginning of the map
			starting_state = self.basemap.scores()
			print(self.basemap)
			print("STARTING")

		visited = []
		queue = deque()
		queue.append((starting_state, []))

		#### STAT TRACKER ####
		if stats:
			print("Checking 1 move")
			max_moves = 1
			considered = 0
		#### STAT TRACKER ####

		while queue:
			state, moves = queue.popleft()
			if str(state) in visited:
				continue
			visited.append(str(state))

			#### STAT TRACKER ####
			if stats:
				considered += 1
				if len(moves) + 1 > max_moves:
					print(f'\tTotal considered: {considered}')
					considered = 0
					print(f"Checking {len(moves) + 1} moves")
					max_moves = len(moves) + 1
			#### STAT TRACKER ####

			try:
				for move in list(Move):
					game = Eng.Engine(self.basemap, state)
					if not game.play(move):
						continue

					if game.loss():
						continue
					if game.complete():
						# Found end
						break

					queue.append((game.position, moves + [move]))
				else:
					continue
				break
			except Exception as e:
				print("\n\nRANDOM CRASH HAPPENED")
				print(state)
				print(moves)
				print(move)
				print(e)
				exit(1)
		else:
			# Ended search
			print("No solution")
			return False

		all_moves = moves + [move]
		if stats:
			print(f"Length: {len(all_moves)} - Moves: {self.list_moves(all_moves)}")
		return all_moves

	def Dijkstra(self):
		heap = []
		visited = []	# Dijk visited
		played_moves = {}

		heapq.heappush(heap, MinHeap(('', self.basemap.scores())))

		#### STAT TRACKER ####
		considerations = {}
		max_moves = len(heap[0].heap_move())
		lowest = max_moves
		print(f"Checking {max_moves} moves")
		#### STAT TRACKER ####

		minimum_found = None
		upper_bound = None
		while heap:
			entry = heapq.heappop(heap)
			state = entry.heap_score()
			
			if state in visited:
				continue
			visited.append(state)
			state_path = entry.heap_move()

			#### STAT TRACKER ####
			considerations[len(state_path)] = considerations.get(len(state_path), 0) + 1
			if len(state_path) != lowest:
				print(f'\tConsidered: {considerations[lowest]}')
				print(f'\tMax Depth: {max_moves}')
				lowest = len(state_path)
				print(f"Checking {lowest} moves...")
			#### STAT TRACKER ####

			if state is None:
				print(f"Length: {len(state_path)} - Moves: {state_path}")
				return state_path
				break

			game = Eng.Engine(self.basemap, state)
			if game.win():
				path = self.BFS(game.position, stats=False)
				if path is False:
					continue
				state_path += "".join([move.letter() for move in path])
				heapq.heappush(heap, MinHeap((state_path, None)))
				if not minimum_found:
					minimum_found = len(state_path)
				elif len(state_path) < minimum_found:
					minimum_found = len(state_path)
				continue

			all_moves = self.reachable(state)
			for moves, tpos in all_moves:
				if minimum_found and len(state_path + moves) > minimum_found:
					continue
				if upper_bound and len(state_path + moves) > upper_bound:
					continue

				player_state = game.position[0][0:2] + tpos
				ngame = Eng.Engine(self.basemap, [player_state] + game.position[1:])
				if not ngame.play(Move[moves[-1]]):
					continue
				if ngame.loss():
					continue
				# if ngame.win():
				# 	print(f"UPPER BOUND TRIGGER: {len(state_path + moves)}")
				# 	if not upper_bound:
				# 		upper_bound = len(state_path + moves)
				# 	elif len(state_path + moves) < upper_bound:
				# 		upper_bound = len(state_path + moves)

				# Only get here if valid play
				heapq.heappush(heap, MinHeap((state_path + moves, ngame.position)))

				#### STAT TRACKER ####
				if len(state_path + moves) > max_moves:
					max_moves = len(state_path + moves)
				#### STAT TRACKER ####

	def find_target_positions(self, sausage):
		width = self.basemap.width
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
		if sausage.orientation == Orientation.HORIZONTAL:
			edge_directions = [
				Move.UP, Move.UP, Move.RIGHT, Move.DOWN, Move.DOWN, Move.LEFT, # Normals
				Move.RIGHT, Move.RIGHT, Move.DOWN, Move.LEFT, Move.LEFT, Move.UP,
				Move.LEFT, Move.LEFT, Move.UP, Move.RIGHT, Move.RIGHT, Move.DOWN
			]
			edge_forces = [
				Move.DOWN, Move.DOWN, Move.LEFT, Move.UP, Move.UP, Move.RIGHT,
			] * 3
		elif sausage.orientation == Orientation.VERTICAL:
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
			extended.append(normal.walk(pos, width))
			extended_directions.append(normal.opposite())
			extended_forces.append(normal.opposite())

		all_positions = corners + edges + extended
		all_face_directions = corner_directions + edge_directions + extended_directions
		all_forces = corner_forces + edge_forces + extended_forces
		return list(zip(all_positions, all_face_directions, all_forces))

	def replace_entities_with_walls(self, state):
		wall_positions = []
		game = Eng.Engine(self.basemap, state)
		for ent in game.entities:
			for pos in ent.get_positions():
				wall_positions.append(pos)
		return wall_positions

	def reachable(self, state):
		game = Eng.Engine(self.basemap, state)
		graph, valid_positions = self.warshall(state)
		player_index = valid_positions.index((game.player.pos, game.player.facing))
		
		plays = []
		# plays = set()
		for sausage in game.entities:
			results = self.find_target_positions(sausage)
			for target, facing, push in results:
				if (target, facing) in valid_positions:
					move_index = valid_positions.index((target, facing))
					moves = graph[player_index][move_index][1]
					if moves is None:
						continue
					moves += push.letter()
					# plays.add(moves)
					# print(valid_positions)
					# print(len(str(self.basemap.width * self.basemap.height)))
					# print(f'{target:0>{len(str(self.basemap.width * self.basemap.height))}}')
					# exit(1)
					plays.append((moves, f'{facing.value}{target:0>{len(str(self.basemap.width * self.basemap.height))}}'))

		return plays

	def warshall(self, state):
		if str(state[1:]) in self.warshall_buffer:
			return self.warshall_buffer[str(state[1:])]

		# DESTRUCTIVE WALL CHANGE - NEED TO UNDO AT END OF FUNCTION
		extra_walls = self.replace_entities_with_walls(state)
		save_tiles = [self.basemap.tiles[wall] for wall in extra_walls]
		for wall in extra_walls:
			self.basemap.tiles[wall] = Tile.Ground(wall, zpos=2)

		# Find all walls and tiles the player can stand on
		width = self.basemap.width
		walls = [i for i, tile in enumerate(self.basemap.tiles) if isinstance(tile, Tile.Ground) and tile.zpos > 1]
		ground = [i for i, tile in enumerate(self.basemap.tiles) if isinstance(tile, Tile.Ground) and tile.zpos == 1]

		# Get all the valid tiles that the player can stand on without fork bonks
		valid_positions = []
		for pos in ground:
			for move in list(Move):
				new_pos = move.walk(pos, width)
				if new_pos not in walls:
					valid_positions.append((pos, move))


		# Create the graph of valid player moves for each position
		graph = []
		for y in range(len(valid_positions)):
			row = [[100000, None] for x in range(len(valid_positions))]
			row[y] = [0, ""]


			for move in list(Move):
				game = Eng.Engine(self.basemap, state)

				p_pos, p_dir = valid_positions[y]
				game.player.pos = p_pos
				game.player.facing = p_dir

				res = game.play(move)
				if not res:
					continue
				if p_pos == game.player.pos and p_dir == game.player.facing:
					continue

				index = (valid_positions.index((game.player.pos, game.player.facing)))
				row[index] = [1, move.letter()]

			graph.append(row)

		# UNDO DESTRUCTIVE
		for wall, tile in zip(extra_walls, save_tiles):
			self.basemap.tiles[wall] = tile

		# Warshall algo
		for k in range(len(valid_positions)):
			for i in range(len(valid_positions)):
				for j in range(len(valid_positions)):
					if graph[i][j][0] > graph[i][k][0] + graph[k][j][0]:
						graph[i][j][0] = graph[i][k][0] + graph[k][j][0]
						graph[i][j][1] = graph[i][k][1] + graph[k][j][1]

		self.warshall_buffer[str(state[1:])] = (graph, valid_positions)
		return graph, valid_positions

if __name__ == '__main__':
	run = Algo('maps/twisty_farm')
	# run = Algo('maps/the_clover')
	# run = Algo('maps/inlet_shore')
	# run.Dijkstra()
	run.BFS()
	# print(run.basemap)