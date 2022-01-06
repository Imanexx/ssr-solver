from enum import Enum

class Orientation(Enum):
	HORIZONTAL 	= 0
	VERTICAL	= 1

class Move(Enum):
	UP = 0
	DOWN = 1
	LEFT = 2
	RIGHT = 3

class Action(Enum):
	WALK = 0
	ROTATE = 1

def calc_move(pos, direction : Move, width):
	if direction == Move.UP:
		return pos - width
	if direction == Move.DOWN:
		return pos + width
	if direction == Move.LEFT:
		return pos - 1
	if direction == Move.RIGHT:
		return pos + 1

def calc_pos(y, x, w):
	return w * y + x

def decode_pos(pos, w):
	x = pos % w
	y = pos // w
	return y, x

def opposite_force(force : Move):
	if force == Move.RIGHT:
		return Move.LEFT

	if force == Move.LEFT:
		return Move.RIGHT

	if force == Move.UP:
		return Move.DOWN

	if force == Move.DOWN:
		return Move.UP

def move_to_letter(move):
	if move == Move.UP:
		return 'U'
	if move == Move.DOWN:
		return 'D'
	if move == Move.LEFT:
		return 'L'
	if move == Move.RIGHT:
		return 'R'

def letter_to_move(letter):
	if letter == 'L':
		return Move.LEFT

	if letter == 'U':
		return Move.UP

	if letter == 'R':
		return Move.RIGHT

	if letter == 'D':
		return Move.DOWN

def perpendicular_force(force : Move):
	if force == Move.RIGHT or force == Move.LEFT:
		return Move.DOWN
	return Move.RIGHT

def euclidean_moves(pos, width):
	moves = [Move.UP, Move.DOWN, Move.LEFT, Move.RIGHT]
	positions = []
	for move in moves:
		pnew = calc_move(pos, move, width)
		positions.append(pnew)
		if move == Move.UP or move == Move.DOWN:
			positions.append(pnew - 1)
			positions.append(pnew + 1)
	return positions