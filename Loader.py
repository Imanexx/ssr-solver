import re
from Utils import *

import Tiles as Tile
import Entities as Entity

# GLOBAL
PADDING = 3

def _preprocess(line : str):
	line = re.sub(r'//.*', '', line) # Remove simple // comments
	line = line.strip()
	return line

def read_tiles(lines):
	def map_above_padding(width):
		return [None] * (width * PADDING)

	def map_below_padding(tiles, width):
		for _ in range(0, (width * PADDING)):
			tiles.append(None)

	def map_side_padding(tiles, padding):
		for _ in range(0, padding):
			tiles.append(None)

	mapping = {
		'0' : None,
		'1' : 'ground',
		'2' : 'grill',
	}

	# Height of the map with padding included
	width = ((len(lines[0]) + 1) // 2) + (PADDING * 2)
	tiles = map_above_padding(width)
	
	for i, line in enumerate(lines):
		# END CONDITION - End of map
		if not line:
			map_below_padding(tiles, width)
			height = i + PADDING * 2 # Height of the map with padding included
			return tiles, width, height, i

		map_side_padding(tiles, PADDING)

		row = line.split(" ")
		for j, tile in enumerate(row):
			# Accurate positioning with padding included
			x = j + PADDING
			y = i + PADDING

			# WALL
			if int(tile) > 2:
				zheight = int(tile) - 1
				tiles.append(Tile.Ground(calc_pos(y, x, width), zpos=zheight))
				continue

			tile_mapping = mapping[tile]
			if not tile_mapping:
				tiles.append(None)
				continue # water
			if tile_mapping == 'ground':
				tiles.append(Tile.Ground(calc_pos(y, x, width)))
			elif tile_mapping == 'grill':
				tiles.append(Tile.Grill(calc_pos(y, x, width)))
		
		map_side_padding(tiles, PADDING)

def read_entities(read_index, width, lines, map_dim):
	entities = []
	for line in lines[read_index:]:
		if not line:
			continue
		
		# Load entities
		info = line.split(",")
		info = [x.strip() for x in info]
		
		name = info[0]
		if name[0] == 's':
			dy, dx = info[1], info[2]
			y = int(dy) + PADDING
			x = int(dx) + PADDING
			position = calc_pos(y, x, width)
			placement = None
			if name[1] == 'h':
				placement = Orientation.HORIZONTAL
			elif name[1] == 'v':
				placement = Orientation.VERTICAL
			
			# TODO: ZPOS for stacked sausages???
			
			sausage = Entity.Sausage(map_dim, position, placement)
			entities.append(sausage)
		if name[0] == 'p':
			dy, dx = info[1], info[2]
			y = int(dy) + PADDING
			x = int(dx) + PADDING
			position = calc_pos(y, x, width)

			face_direction = None
			dir = name[1]
			if dir == 'u':
				face_direction = Move.UP
			elif dir == 'd':
				face_direction = Move.DOWN
			elif dir == 'l':
				face_direction = Move.LEFT
			elif dir == 'r':
				face_direction = Move.RIGHT

			# TODO: ZPOS for stacked sausages???

			player = Entity.Player(map_dim, position, face_direction)
			entities.append(player)

	return entities

def load_map(file_name):
	with open(file_name, 'r') as f:
		# Quick preprocess of map file - Remove all comments
		lines = f.readlines()
		lines = [_preprocess(line) for line in lines if not re.match(r'//', line)]

		"""
		read_index: The line number to continue reading from
		"""
		tiles, width, height, read_index = read_tiles(lines)
		entities = read_entities(read_index, width, lines, map_dim=(width, height))

	return tiles, entities, width, height

if __name__ == '__main__':
	tiles, entities, width, height = load_map('maps/inlet_shore')
	print(f"{tiles=}")
	print(f"{entities=}")
	print(f"{width=} {height=}")