from enum import Enum

def calc_pos(y, x, w):
	return w * y + x

def decode_pos(pos, w):
	x = pos % w
	y = pos // w
	return y, x

class Orientation(Enum):
	HORIZONTAL 	= 0
	VERTICAL	= 1

	def walk(self, pos, width):
		if self.name == "HORIZONTAL":
			return pos + 1
		elif self.name == "VERTICAL":
			return pos + width

class Action(Enum):
	WALK = 0
	ROTATE = 1
	STRAFE = 2

class Failure(Enum):
	NONE 		= 0
	COLLISION 	= 1
	DROWNED 	= 2

class Move(Enum):
	LEFT 	= 0
	RIGHT 	= 1
	UP 		= 2
	DOWN 	= 3
	# Alias values -> Move[letter]
	L = 0
	R = 1
	U = 2
	D = 3

	def shift(self, width):
		if self.name == 'LEFT':
			return -1
		if self.name == 'RIGHT':
			return 1
		if self.name == 'UP':
			return -width
		if self.name == 'DOWN':
			return width

	def walk(self, pos, width):
		return pos + self.shift(width)

	def opposite(self):
		if self.name == 'LEFT':
			return Move.RIGHT
		if self.name == 'RIGHT':
			return Move.LEFT
		if self.name == 'UP':
			return Move.DOWN
		if self.name == 'DOWN':
			return Move.UP

	def letter(self):
		return self.name[0]

	def perpendicular(self):
		if self.name == 'LEFT' or self.name == 'RIGHT':
			return Move.DOWN
		return Move.RIGHT
