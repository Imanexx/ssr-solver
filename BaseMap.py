import Loader
import Entities as Entity

class LoadMap():
	def __init__(self, map_name):
		tiles, entities, width, height = Loader.load_map(map_name)
		self.tiles = tiles
		self.width = width
		self.height = height

		self.player = None
		self.entities = []

		# Seperate entities
		for ent in entities:
			if isinstance(ent, Entity.Player):
				self.player = ent
			else:
				self.entities.append(ent)
		
		# SET ENTITY IDs
		self.player.id = 0
		for i, ent in enumerate(self.entities):
			ent.id = i + 1

		self.win_pos = self.player.pos
		self.win_dir = self.player.facing

	def dimensions(self):
		return self.width, self.height

	def copy(self):
		return self.tiles, self.width, self.height, self.win_pos, self.win_dir

	def state(self):
		print(self.player.score())
		for ent in self.entities:
			print(ent.score())

	def scores(self):
		game_score = [self.player.score()]
		for ent in self.entities:
			game_score.append(ent.score())
		return game_score

	def __repr__(self):
		import re
		from Utils import calc_pos

		symbols = []
		positions = []
		psym, ppos = self.player.get_symbols()
		symbols += psym
		positions += ppos
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

		space_width = ' ' * self.width + '\n'
		output = re.sub(space_width, '', output)
		return output

if __name__ == '__main__':
	basemap = LoadMap('maps/seafinger')
	# tiles, width, height = basemap.copy()
	# print(tiles, width, height)
	basemap.state()
	print(basemap)
	# print(basemap.entities[1].id)