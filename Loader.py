import re
from Utils import *
from Tiles import *

import Entities as Entity


PADDING = 3

def _preprocess(line : str):
	line = re.sub(r'//.*', '', line) # Remove simple // comments
	line = line.strip()
	return line

def read_tiles(lines):

	mapping = {
		'0' : None,
		'1' : 'ground',
		'2' : 'grill',
	}

	width = ((len(lines[0]) + 1) // 2) + (PADDING * 2)
	tiles = [None] * (width * PADDING)
	for i, line in enumerate(lines):
		if not line:
			height = i + PADDING * 2

			for _ in range(0, (width * PADDING)):
				tiles.append(None)
			return tiles, width, height, i

		for SPACE in range(0, PADDING):
			tiles.append(None)

		row = line.split(" ")
		for j, tile in enumerate(row):
			x = j + PADDING
			y = i + PADDING

			if int(tile) > 2:
				zheight = int(tile) - 1
				tiles.append(Ground(calc_pos(y, x, width), zpos=zheight))
				continue

			ti = mapping[tile]
			if not ti:
				tiles.append(None)
				continue # water
			if ti == 'ground':
				tiles.append(Ground(calc_pos(y, x, width)))
			elif ti == 'grill':
				tiles.append(Grill(calc_pos(y, x, width)))
		for SPACE in range(0, PADDING):
			tiles.append(None)

def read_entities(read_index, width, lines):
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
			
			# ZPOS for stacked sausages???
			
			sausage = Entity.Sausage(position, placement)
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

			# ZPOS???

			player = Entity.Player(position, face_direction)
			entities.append(player)



	return entities


def load_map(file_name):
	with open(file_name, 'r') as f:
		# Quick preprocess of map file
		lines = f.readlines()
		lines = [_preprocess(line) for line in lines if not re.match(r'//', line)]

		tiles, width, height, read_index = read_tiles(lines)
		entities = read_entities(read_index, width, lines)

	return tiles, entities, width, height

if __name__ == '__main__':
	load_map('inlet_shore')