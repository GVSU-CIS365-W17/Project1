import random

import hlt
from hlt import NORTH, EAST, SOUTH, WEST, STILL, Move, Square
from math import sqrt


myID, game_map = hlt.get_init()
hlt.send_init("LowDash_v2")

#Minimum strength / production ratio
strength = 2
max_strength = 7
game_map.get_frame()
map_size = game_map.width + game_map.height
increment = 5/(10 * sqrt(map_size))*.1

# Defines a heuristic for overkill bot
def heuristic(square):
    if square.owner == 0 and square.strength > 0:
        return square.production / square.strength
    else:
        total_damage = 0
        for direction, neighbor in enumerate(game_map.neighbors(square)):
            if neighbor.owner != 0 and neighbor.owner != myID:
                total_damage += neighbor.strength
        return total_damage


# Returns true if the square is a boarder, else false
def check_is_border(square):
    for direction, neighbor in enumerate(game_map.neighbors(square)):
        if neighbor.owner != myID:
            return True

    return False


# Checks if the square is strong enough to attack its target.
# True by default if not a border piece.
def check_strong_enough(square):
    direction, target = find_max_heuristic_neighbor(square)
    if target is None or square.strength > target.strength:
        return True
    return False


# Finds the direction of the closest border breaks ties based
# based on heuristic sum scores
def find_nearest_enemy_direction(square):
    direction = NORTH
    max_distance = min(game_map.width, game_map.height) / 2
    max_heuristic = 0

    for d in (NORTH, EAST, SOUTH, WEST):
        distance = 0
        neighbor = game_map.get_target(square, d)
        while neighbor.owner == myID and distance < max_distance:
            distance += 1
            neighbor = game_map.get_target(neighbor, d)

        score = sum_heuristic_neighbors(neighbor)
        if distance < max_distance:
            direction = d
            max_distance = distance
            max_heuristic = score

        elif distance == max_distance and score > max_heuristic:
            direction = d
            max_heuristic = score

    return direction


# Finds the neighbor with the highest overkill heuristic
def find_max_heuristic_neighbor(square):
    max_heuristic = -1
    max_direction = None
    max_neighbor = None
    for direction, neighbor in enumerate(game_map.neighbors(square)):
        if neighbor.owner != myID and heuristic(neighbor) > max_heuristic:
            max_heuristic = heuristic(neighbor)
            max_direction = direction
            max_neighbor = neighbor
    return max_direction, max_neighbor


# Finds the sum of the heuristic scores of all neighbors of a square
def sum_heuristic_neighbors(square):
    sum = 0
    for direction, neighbor in enumerate(game_map.neighbors(square)):
        if neighbor.owner != myID:
            sum += heuristic(neighbor)
    return sum


# Checks to see if overflow is possible
def check_overflow(move):
    target = game_map.get_target(move.square, move.direction)
    for direction, neighbor in enumerate(game_map.neighbors(target)):
        if neighbor.owner == myID and \
                                neighbor.strength + move.square.strength >= 255 and \
                                neighbor != move.square:

            if neighbor.strength > move.square.strength:
                return True

            elif neighbor.strength == move.square.strength:
                if sum_heuristic_neighbors(neighbor) > sum_heuristic_neighbors(move.square):
                    return True
                elif sum_heuristic_neighbors(neighbor) == sum_heuristic_neighbors(move.square):
                    return bool(random.getrandbits(1))

    if target.owner == myID and \
                            target.strength + move.square.strength >= 255 and \
                            target != move.square:
        if target.strength > move.square.strength:
            return True

        elif target.strength == move.square.strength:
            if sum_heuristic_neighbors(target) > sum_heuristic_neighbors(move.square):
                return True
            elif sum_heuristic_neighbors(target) == sum_heuristic_neighbors(move.square):
                return bool(random.getrandbits(1))

    return False


# Gets a list of possible moves in order from best to worst
def get_move_precedence(square):
    move_precedence = []

    # Attack the enemy if possible
    direction, target = find_max_heuristic_neighbor(square)
    if direction is not None and square.strength > target.strength:
        move_precedence.append(Move(square, direction))

    # Wait if strength is low
    if square.strength < strength * square.production:# and not check_overflow(square):
        move_precedence.append(Move(square, STILL))

    # Check if combining with neighbor makes neighbor strong enough
    for direction, neighbor in enumerate(game_map.neighbors(square)):
        if not check_strong_enough(neighbor) and neighbor.owner == myID and \
                sum_heuristic_neighbors(square) < sum_heuristic_neighbors(neighbor):

            # May want to order these
            move_precedence.append(Move(square, direction))

    # Move towards the closest border if not a border piece
    if not check_is_border(square):
        move_precedence.append(Move(square, find_nearest_enemy_direction(square)))

    # Add all other directions to move_precedence list
    for d in (STILL, NORTH, EAST, SOUTH, WEST):
        if Move(square, d) not in move_precedence:
            move_precedence.append(Move(square, d))

    return move_precedence


# Returns the best move that does not cause an overflow, STILL by default
def check_moves(move_precedence):
    for move in move_precedence:
        target = game_map.get_target(move.square, move.direction)

        if not check_overflow(move):
            return move

        elif target.owner != myID and target.owner != 0:
            return move

    return Move(move_precedence[0].square, STILL)


while True:
    moves = []
    for square in game_map:
        if square.owner == myID:
            move_precedence = get_move_precedence(square)
            move = check_moves(move_precedence)
            moves.append(move)

    if strength + increment <= max_strength:
        strength += increment

    hlt.send_frame(moves)
    game_map.get_frame()
