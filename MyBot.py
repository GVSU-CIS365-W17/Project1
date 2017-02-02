import random
from itertools import chain

import hlt
from hlt import NORTH, EAST, SOUTH, WEST, STILL, Move, Square


myID, game_map = hlt.get_init()
hlt.send_init("LowDash_v2")

# Minimum strength / production ratio
min_strength = 5


class MySquare:
    def __init__(self, production=0, strength=0, owner=0, x=0, y=0):
        self.production = production
        self.strength = strength
        self.owner = owner
        self.x = x
        self.y = y


class MyGameMap:
    def __init__(self, game_map):
        self.contents = [[MySquare() for x in range(game_map.width)] for y in range(game_map.height)]
        self.height = game_map.height
        self.width = game_map.width

        for x in range(game_map.height):
            for y in range(game_map.width):
                self.contents[x][y].strength = game_map.contents[x][y].strength
                self.contents[x][y].production = game_map.contents[x][y].strength
                self.contents[x][y].owner = game_map.contents[x][y].strength
                self.contents[x][y].x = game_map.contents[x][y].x
                self.contents[x][y].y = game_map.contents[x][y].y

    def update_map(self, game_map):
        for x in range(game_map.height):
            for y in range(game_map.width):
                self.contents[x][y].strength = game_map.contents[x][y].strength
                self.contents[x][y].production = game_map.contents[x][y].strength
                self.contents[x][y].owner = game_map.contents[x][y].strength
                self.contents[x][y].x = game_map.contents[x][y].x
                self.contents[x][y].y = game_map.contents[x][y].y

    def __iter__(self):
        return chain.from_iterable(self.contents)

    def neighbors(self, square, n=1, include_self=False):
        assert isinstance(include_self, bool)
        assert isinstance(n, int) and n > 0
        if n == 1:
            combos = ((0, -1), (1, 0), (0, 1), (-1, 0), (0,
                                                         0))  # NORTH, EAST, SOUTH, WEST, STILL ... matches indices provided by enumerate(game_map.neighbors(square))
        else:
            combos = ((dx, dy) for dy in range(-n, n + 1) for dx in range(-n, n + 1) if abs(dx) + abs(dy) <= n)
        return (self.contents[(square.y + dy) % self.height][(square.x + dx) % self.width] for dx, dy in combos if
                include_self or dx or dy)

    def get_target(self, square, direction):
        "Returns a single, one-step neighbor in a given direction."
        dx, dy = ((0, -1), (1, 0), (0, 1), (-1, 0), (0, 0))[direction]
        return self.contents[(square.y + dy) % self.height][(square.x + dx) % self.width]

    def get_distance(self, sq1, sq2):
        "Returns Manhattan distance between two squares."
        dx = min(abs(sq1.x - sq2.x), sq1.x + self.width - sq2.x, sq2.x + self.width - sq1.x)
        dy = min(abs(sq1.y - sq2.y), sq1.y + self.height - sq2.y, sq2.y + self.height - sq1.y)
        return dx + dy

    # Defines a heuristic for overkill bot
    def heuristic(self, square):
        if square.owner == 0 and square.strength > 0:
            return square.production / square.strength
        else:
            total_damage = 0
            for direction, neighbor in enumerate(self.neighbors(square)):
                if neighbor.owner != 0 and neighbor.owner != myID:
                    total_damage += neighbor.strength
            return total_damage

    # Returns true if the square is a boarder, else false
    def check_is_border(self, square):
        for direction, neighbor in enumerate(self.neighbors(square)):
            if neighbor.owner != myID:
                return True

        return False

    # Finds the neighbor with the highest overkill heuristic
    def find_max_heuristic_neighbor(self, square):
        max_heuristic = -1
        max_direction = None
        max_neighbor = None
        for direction, neighbor in enumerate(self.neighbors(square)):
            if neighbor.owner != myID and self.heuristic(neighbor) > max_heuristic:
                max_heuristic = self.heuristic(neighbor)
                max_direction = direction
                max_neighbor = neighbor
        return max_direction, max_neighbor

    # Checks if the square is strong enough to attack its target.
    # True by default if not a border piece.
    def check_strong_enough(self, square):
        direction, target = self.find_max_heuristic_neighbor(square)
        if target is None or square.strength > target.strength:
            return True
        return False

    # Finds the direction of the closest border breaks ties based
    # based on heuristic sum scores
    def find_nearest_enemy_direction(self, square):
        direction = NORTH
        max_distance = min(self.width, self.height) / 2
        max_heuristic = 0

        for d in (NORTH, EAST, SOUTH, WEST):
            distance = 0
            neighbor = self.get_target(square, d)
            while neighbor.owner == myID and distance < max_distance:
                distance += 1
                neighbor = self.get_target(neighbor, d)

            score = self.sum_heuristic_neighbors(neighbor)
            if distance < max_distance:
                direction = d
                max_distance = distance
                max_heuristic = score

            elif distance == max_distance and score > max_heuristic:
                direction = d
                max_heuristic = score

        return direction

    # Finds the sum of the heuristic scores of all neighbors of a square
    def sum_heuristic_neighbors(self, square):
        sum = 0
        for direction, neighbor in enumerate(self.neighbors(square)):
            if neighbor.owner != myID:
                sum += self.heuristic(neighbor)
        return sum

    # Gets a list of possible moves in order from best to worst
    def get_move_precedence(self, square):
        move_precedence = []

        # Attack the enemy if possible
        direction, target = self.find_max_heuristic_neighbor(square)
        if direction is not None and square.strength > target.strength:
            move_precedence.append(Move(square, direction))

        # Wait if strength is low
        if square.strength < min_strength * square.production:  # and not check_overflow(square):
            move_precedence.append(Move(square, STILL))

        # Check if combining with neighbor makes neighbor strong enough
        for direction, neighbor in enumerate(game_map.neighbors(square)):
            if not self.check_strong_enough(neighbor) and neighbor.owner == myID and \
                            self.sum_heuristic_neighbors(square) < self.sum_heuristic_neighbors(neighbor):
                # May want to order these
                move_precedence.append(Move(square, direction))

        # Move towards the closest border if not a border piece
        if not self.check_is_border(square):
            move_precedence.append(Move(square, self.find_nearest_enemy_direction(square)))

        # Add all other directions to move_precedence list
        for d in (NORTH, EAST, SOUTH, WEST, STILL):
            if Move(square, d) not in move_precedence:
                move_precedence.append(Move(square, d))

        return move_precedence

    # Checks to see if overflow is possible
    def check_overflow(self, move):
        target = game_map.get_target(move.square, move.direction)
        for direction, neighbor in enumerate(game_map.neighbors(target)):
            if neighbor.owner == myID and \
                                    neighbor.strength + move.square.strength >= 255 and \
                                    neighbor != move.square:

                if neighbor.strength > move.square.strength:
                    return True

                # elif neighbor.strength == move.square.strength:
                #     if self.sum_heuristic_neighbors(neighbor) > self.sum_heuristic_neighbors(move.square):
                #         return True
                #     elif self.sum_heuristic_neighbors(neighbor) == self.sum_heuristic_neighbors(move.square):
                #         return bool(random.getrandbits(1))

        if target.owner == myID and \
                                target.strength + move.square.strength >= 255 and \
                                target != move.square:
            if target.strength > move.square.strength:
                return True

            # elif target.strength == move.square.strength:
            #     if self.sum_heuristic_neighbors(target) > self.sum_heuristic_neighbors(move.square):
            #         return True
            #     elif self.sum_heuristic_neighbors(target) == self.sum_heuristic_neighbors(move.square):
            #         return bool(random.getrandbits(1))

        return False


    # Returns the best move that does not cause an overflow, STILL by default
    def check_moves(self, move_precedence):
        for move in move_precedence:
            target = self.get_target(move.square, move.direction)

            if not self.check_overflow(move):
                return move

            elif target.owner != myID and target.owner != 0:
                return move

        return Move(move_precedence[0].square, STILL)

f = open('logfile.log', 'w')
while True:
    game_map.get_frame()

# for x in range(game_map.height):
#     for y in range(game_map.width):
#         f.write(str(game_map.contents[x][y].x))
#         f.write(',')
#         f.write(str(game_map.contents[x][y].y))
#         f.write('\t')
#     f.write('\n')
#
    local_map = MyGameMap(game_map)
    local_map.update_map(game_map)

    # f = open('logfile.log', 'w')

    moves = []
    for square in game_map:
        if square.owner == myID:
            local_square = local_map.contents[square.x][square.y]
            move_precedence = local_map.get_move_precedence(local_square)
            local_move = local_map.check_moves(move_precedence)
            move = Move(square, local_move.direction)
            moves.append(move)

    for m in moves:
        output = ('Square at ', m.square.x, ' ', m.square.y, ' moves ', m.direction, '\n')
        s = str(output)
        # f.write(s)
        f.write('Square at ')
        f.write(str(m.square.x))
        f.write(' ')
        f.write(str(m.square.y))
        f.write(' moves ')
        # f.write(str(m.direction))
        if m.direction == NORTH:
            f.write('NORTH')
        elif m.direction == SOUTH:
            f.write('SOUTH')
        elif m.direction == WEST:
            f.write('WEST')
        elif m.direction == EAST:
            f.write('EAST')
        elif m.direction == STILL:
            f.write('STILL')
        f.write('\n\n')

    hlt.send_frame(moves)
