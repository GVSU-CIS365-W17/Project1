import hlt
from hlt import NORTH, EAST, SOUTH, WEST, STILL, Move, Square
import random

myID, game_map = hlt.get_init()
hlt.send_init("LowDash")


# Defines a heuristic for discerning bot
def heuristic(square):
    if square.strength > 0:
        return square.production / square.strength
    else:
        return square.production


# Defines a heuristic for overkill bot
def overkill_heuristic(square):
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
    direction, target = find_max_overkill_neighbor(square)
    if target is None or square.strength > target.strength:
        return True
    return False


# Finds the direction of the closest border
def find_nearest_enemy_direction(square):
    direction = NORTH
    maxDistance = min(game_map.width, game_map.height) / 2

    for d in (NORTH, EAST, SOUTH, WEST):
        distance = 0
        neighbor = game_map.get_target(square, d)
        while neighbor.owner == myID and distance < maxDistance:
            distance += 1
            neighbor = game_map.get_target(neighbor, d)

        if distance < maxDistance:
            direction = d
            maxDistance = distance

    return direction


# Finds the neighbor with the highest production value
def find_max_production_neighbor(square):
    max_production = -1
    max_direction = None
    max_neighbor = None
    for direction, neighbor in enumerate(game_map.neighbors(square)):
        if neighbor.owner != myID and neighbor.production > max_production:
            max_production = neighbor.production
            max_direction = direction
            max_neighbor = neighbor
    return max_direction, max_neighbor


# Finds the neighbor with the highest heuristic score
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


# Fiends the neighbor with the highest overkill heuristic
def find_max_overkill_neighbor(square):
    max_heuristic = -1
    max_direction = None
    max_neighbor = None
    for direction, neighbor in enumerate(game_map.neighbors(square)):
        if neighbor.owner != myID and overkill_heuristic(neighbor) > max_heuristic:
            max_heuristic = overkill_heuristic(neighbor)
            max_direction = direction
            max_neighbor = neighbor
    return max_direction, max_neighbor


# Ambiturner code
def ambi_move(square):
    border = False

    for direction, neighbor in enumerate(game_map.neighbors(square)):
        if neighbor.owner != myID:
            border = True
            if neighbor.strength < square.strength:
                return Move(square, direction)

    if square.strength < 5 * square.production:
        return Move(square, STILL)

    if not border:
        return Move(square, find_nearest_enemy_direction(square))

    return Move(square, STILL)


# Production Bot code
def prod_move(square):
    direction, target = find_max_production_neighbor(square)
    if direction is not None and square.strength > target.strength:
        return Move(square, direction)

    if square.strength < 5 * square.production:
        return Move(square, STILL)

    if not check_is_border(square):
        return Move(square, find_nearest_enemy_direction(square))

    return Move(square, STILL)


# Discerning Bot code
def discerning_move(square):
    direction, target = find_max_heuristic_neighbor(square)
    if direction is not None and square.strength > target.strength:
        return Move(square, direction)

    if square.strength < 5 * square.production:
        return Move(square, STILL)

    if not check_is_border(square):
        return Move(square, find_nearest_enemy_direction(square))

    return Move(square, STILL)


# Overkill Bot code
def overkill_move(square):
    direction, target = find_max_overkill_neighbor(square)
    if direction is not None and square.strength > target.strength:
        return Move(square, direction)

    if square.strength < 5 * square.production:
        return Move(square, STILL)

    if not check_is_border(square):
        return Move(square, find_nearest_enemy_direction(square))

    return Move(square, STILL)


def combine_move(square):
    # Attack the enemy if possible
    direction, target = find_max_overkill_neighbor(square)
    if direction is not None and square.strength > target.strength:
        return Move(square, direction)

    # Wait if strength is low
    if square.strength < 5 * square.production:
        return Move(square, STILL)

    # Check if combining with neighbor makes neighbor strong enough
    for direction, neighbor in enumerate(game_map.neighbors(square)):
        if not check_strong_enough(neighbor) and \
                                neighbor.owner == myID and \
                                neighbor.strength + square.strength <= 255 and \
                                square.strength < neighbor.strength:
            return Move(square, direction)

    # Move towards the closest border if not a border piece
    if not check_is_border(square):
        return Move(square, find_nearest_enemy_direction(square))

    # Otherwise wait
    return Move(square, STILL)


while True:
    game_map.get_frame()
    moves = [combine_move(square) for square in game_map if square.owner == myID]
    hlt.send_frame(moves)
