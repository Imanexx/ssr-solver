from Utils import *

import BaseMap
import Engine as Eng
import Tiles as Tile

from copy import deepcopy

class Graph():
	def __init__(self, filename):
		self.basemap = BaseMap.LoadMap(filename)
		self.nodes = {}
		self.warshall_buffer = {}
	
	def generate_states(self):
		queue = [self.basemap.scores()]
		visited = []
		
		counter = 0
		while queue:
			state = queue.pop(0)
			if str(state) in visited:
				continue
			counter += 1
			visited.append(str(state))

			loadgame = Eng.Engine(self.basemap, state)
			node = str(loadgame.position[1:])
			self.nodes[node] = []

			for move in list(Move):
				for i, sausage in enumerate(loadgame.entities):
					game = Eng.Engine(self.basemap, state)
					game.apply_forces([move], [sausage.pos])
					if game.loss():
						continue

					new_state = deepcopy(game.position)
					new_state[i+1] = game.entities[i].score()
					queue.append(new_state)

					self.nodes[node].append(((i, move), str(new_state[1:]), game.win()))

	def walk_graph(self):
		queue = [(self.basemap.scores(), [])]
		visited = []
		
		counter = 0
		while queue:
			# CURRENTLY AT GAME STATE WITH AVAILABLE SAUSAGE PUSH COMMANDS
			fullstate, commands = queue.pop(0) 	# Full state has player info
			state = str(fullstate[1:])			# Only sausage info matters
			print(state)
			if state in visited:
				continue
			visited.append(state)
			print(state)
			state_game = Eng.Engine(graph.basemap, fullstate)
			print(state_game)

			counter += 1
			# CONSIDER EACH SAUSAGE PUSH COMMAND AND SEE IF PLAYER IS ABLE TO FULFILL
			for action, next_state, winning in self.nodes[state]:
				if winning:
					print(commands, action)
				
				print(action, next_state, winning)
				sausage_index, push_direction = action
				# Find positions next to sausage that get you there
				positions = graph.get_game_positions(graph.basemap.entities[sausage_index], push_direction, state_game.player.pos, state_game.player.facing)
				print(positions)
				
				# TODO
				# TAKE ABOVE POSITIONS AND SIMULATE THE GAME.
				# AFTER SIMULATE GAME FIND POSITION IN LOOK UP TABLE - POSSIBLE PLAYER PUSH TWO SAUSAGES???
				# TAKE THAT POSITION AND PUT IN QUEUE
				# PQ THE STATE BASED ON LENGTH OF PLAYER MOVES

				# TODO: NOTE THIS 'NEXT_STATE' should include the new player position which is fullstate
				queue.append((next_state, commands + [action]))

			exit(1)

	def replace_entities_with_walls(self, state):
		wall_positions = []
		game = Eng.Engine(self.basemap, state)
		for ent in game.entities:
			for pos in ent.get_positions():
				wall_positions.append(pos)
		return wall_positions

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

	#=================
	# HELPER FUNCTIONS
	#=================

	def load_index(self, sausage, indices):
		positions = []
		edges = sausage.get_edges()
		for i in indices:
			positions.append(edges[i])
		return positions

	def load_extended(self, sausage, indices, direction):
		positions = []
		edges = sausage.get_edges()
		for i in indices:
			positions.append(direction.walk(edges[i], sausage.width))
		return positions

	def get_positions_for_push_direction(self, sausage, push):
		if sausage.orientation == Orientation.VERTICAL:
			if push == Move.UP: 
				indices = [2, 3, 11, 16, 24, 29]
			if push == Move.DOWN: 
				indices = [0, 1, 8, 19, 21, 26]
			if push == Move.LEFT: 
				indices = [5, 7, 9, 10, 14, 15, 22, 23, 27, 28]
			if push == Move.RIGHT: 
				indices = [4, 6, 12, 13, 17, 18, 20, 25, 30, 31]
		elif sausage.orientation == Orientation.HORIZONTAL:
			if push == Move.UP: 
				indices = [2, 3, 11, 12, 16, 17, 24, 25, 29, 30]
			if push == Move.DOWN: 
				indices = [0, 1, 8, 9, 14, 19, 21, 22, 26, 27]
			if push == Move.LEFT: 
				indices = [5, 7, 10, 15, 23, 28]
			if push == Move.RIGHT: 
				indices = [4, 6, 13, 18, 20, 31]

		all_positions = self.find_target_positions(sausage)
		positions = []
		for i in indices:
			positions.append(all_positions[i])

		return positions

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

	def create_player_score(self, position, facing):
		padding = len(str(self.basemap.width * self.basemap.height))
		return f"10{facing.value}{position:0>{padding}}" # Assume player is no holding anything

	#=====================
	# END HELPER FUNCTIONS
	#=====================

	def get_game_positions(self, sausage, push_towards, ppos, pdir):
		wgraph, wpositions = graph.warshall(graph.basemap.scores())
		push_positions = graph.get_positions_for_push_direction(sausage, push_towards)

		# Get list of valid player standing positions
		valid_player_positions = []
		for i, entry in enumerate(push_positions):
			pos, facing, force = entry
			if (pos, facing) in wpositions:
				valid_player_positions.append((pos, facing, force))

		# Get the sequence of player moves from graph
		player_index = wpositions.index((ppos, pdir))
		player_moves = []
		for pos, facing, force in valid_player_positions:
			info = wgraph[player_index][wpositions.index((pos,facing))], force.letter()
			# print(info)
			moves = info[0][1] + force.letter()
			force = info[1]
			player_moves.append((self.create_player_score(pos, facing), Move[force], moves))

		return player_moves


graph = Graph('maps/test')
print(graph.basemap)
graph.generate_states()
graph.walk_graph()
# print(valid_pos)
# print(graph.basemap.scores())

positions = graph.get_game_positions(graph.basemap.entities[0], Move.LEFT, graph.basemap.player.pos, graph.basemap.player.facing)

for playerpos, force, moves in positions:
	print(playerpos, force, moves)
	game = Eng.Engine(graph.basemap, [playerpos] + graph.basemap.scores()[1:])
	game.play(force)
	print(game)
	# break


# wgraph, wpositions = graph.warshall(graph.basemap.scores())
# print(wpositions)

# print(wpositions)
# down_positions = graph.get_positions_for_push_direction(graph.basemap.entities[0], Move.UP)
# print(down_positions)


# valid_positions = []
# for i, entry in enumerate(down_positions):
# 	pos, facing, force = entry
# 	print(pos, facing, force)
# 	if (pos, facing) in wpositions:
# 		valid_positions.append((pos, facing, force))
# print(valid_positions)

# for pos, facing, force in valid_positions:
# 	print(wgraph[wpositions.index((41, Move.UP))][wpositions.index((pos,facing))], force.letter())

# # print(graph.basemap)
# # print(graph.states[str(graph.basemap.scores()[1:])])


