import hlt
from hlt import NORTH, EAST, SOUTH, WEST, STILL, Move, Square
import random


myID, game_map = hlt.get_init()
hlt.send_init("LowDash")

border_list = []

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


# Finds the direction of the closest border breaks ties based
# based on heuristic sum scores
def find_heuristic_enemy_direction(square):
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


# Finds the direction to the closest border in terms of
# Manhattan distance
def find_nearest_border(square):
    direction = NORTH
    max_distance = min(game_map.width, game_map.height) / 2
    nearest_border = border_list[0]

    #Find closest border
    for border_square in border_list:
        distance = game_map.get_distance(square, border_square)
        if distance < max_distance:
            max_distance = distance
            nearest_border = border_square

    # Find shortest path to closest border
    for d in (NORTH, EAST, SOUTH, WEST):
        neighbor = game_map.get_target(square, d)
        distance = game_map.get_distance(neighbor, nearest_border)
        if distance < max_distance:
            max_distance = distance
            direction = d

    return direction


# Finds the direction to the closest border in terms of
# Manhattan distance with the highest heuristic sum
def find_max_heuristic_border_direction(square):
    direction = NORTH
    # max_distance = max(game_map.width, game_map.height)
    # max_heuristic = 0
    max_heuristic_score = 0
    max_heuristic_border = border_list[0]

    # Find border square with the highest heuristic score
    for border_square in border_list:
        distance = game_map.get_distance(square, border_square)
        score = sum_heuristic_neighbors(border_square)
        if score / distance > max_heuristic_score:
            max_distance = distance
            max_heuristic_score = score / distance
            max_heuristic_border = border_square

    # Find shortest path to closest border
    for d in (NORTH, EAST, SOUTH, WEST):
        neighbor = game_map.get_target(square, d)
        distance = game_map.get_distance(neighbor, max_heuristic_border)
        if distance < max_distance:
            max_distance = distance
            direction = d

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


# Checks if a neighbor is big enough to cause overflow
def check_overflow(square):
    for direction, neighbor in enumerate(game_map.neighbors(square)):
        if neighbor.strength + square.strength > 255:
            return True
    return False


# Creates a list of all squares that are on the player's borders
def find_borders():
    for square in game_map:
        if square.owner == myID and check_is_border(square):
            border_list.append(square)


def assess_move(square):
    # Attack the enemy if possible
    direction, target = find_max_heuristic_neighbor(square)
    if direction is not None and square.strength > target.strength:
        return Move(square, direction)

    # Wait if strength is low
    if square.strength < 5 * square.production and not check_overflow(square):
        return Move(square, STILL)

    # Check if combining with neighbor makes neighbor strong enough
    for direction, neighbor in enumerate(game_map.neighbors(square)):
        if not check_strong_enough(neighbor) and \
                                neighbor.owner == myID and \
                                neighbor.strength + square.strength <= 255 and \
                                sum_heuristic_neighbors(square) < sum_heuristic_neighbors(neighbor):
            return Move(square, direction)

    # Move towards the closest border if not a border piece
    if not check_is_border(square):
        return Move(square, find_nearest_enemy_direction(square))
        # return Move(square, find_nearest_border(square))
        # return Move(square, find_max_heuristic_border_direction(square))

    # Otherwise wait
    return Move(square, STILL)


while True:
    game_map.get_frame()
    # find_borders()
    moves = [assess_move(square) for square in game_map if square.owner == myID]
    # border_list = []
    hlt.send_frame(moves)
