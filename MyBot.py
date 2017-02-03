"""
CIS 365 W17
Project 1: Halite Bot
Team LowDash: Mark Jannenga, Tanner Gibson, Sierra Ellison

This is a bot built to play Halite (halite.io).
"""

import random

import hlt
from hlt import NORTH, EAST, SOUTH, WEST, STILL, Move, Square


myID, game_map = hlt.get_init()
hlt.send_init("LowDash")

# Minimum strength / production ratio
min_strength = 5


def heuristic(square):
    """Defines a heuristic with which to measure the value of a square.
    :param square: The square to be evaluated
    :return: The heuristic value of the square
    """
    if square.owner == 0 and square.strength > 0:
        return square.production / square.strength
    else:
        total_damage = 0
        for direction, neighbor in enumerate(game_map.neighbors(square)):
            if neighbor.owner != 0 and neighbor.owner != myID:
                total_damage += neighbor.strength
        return total_damage


def check_is_border(square):
    """Checks if a given square is on the border of the player's territory.
    :param square: The square to check
    :return: True if on the border, else False
    """
    for direction, neighbor in enumerate(game_map.neighbors(square)):
        if neighbor.owner != myID:
            return True
    return False


def check_strong_enough(square):
    """Checks if a square is strong enough to capture the best available
    enemy neighbor square.
    :param square: The square to check
    :return: True if the square is strong enough, else False
    """
    direction, target = find_max_heuristic_neighbor(square)
    if target is None or square.strength > target.strength:
        return True
    return False


def find_nearest_enemy_direction(square):
    """Finds the closest border to the square. Breaks ties based on heuristic scores.
    :param square: The square to check
    :return: The direction to the nearest border
    """
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


def find_max_heuristic_neighbor(square):
    """Finds the neighbor with the highest heuristic score.
    :param square: The square to check
    :return: The direction of the max heuristic neighbor, and the neighbor itself
    """
    max_heuristic = -1
    max_direction = None
    max_neighbor = None
    for direction, neighbor in enumerate(game_map.neighbors(square)):
        if neighbor.owner != myID and heuristic(neighbor) > max_heuristic:
            max_heuristic = heuristic(neighbor)
            max_direction = direction
            max_neighbor = neighbor
    return max_direction, max_neighbor


def sum_heuristic_neighbors(square):
    """Finds the sum of the heuristics of all the unowned neighboring squares.
    :param square: The square to check
    :return: The heuristic sum of the neighbors
    """
    sum = 0
    for direction, neighbor in enumerate(game_map.neighbors(square)):
        if neighbor.owner != myID:
            sum += heuristic(neighbor)
    return sum


def check_overflow(move):
    """Takes a move and checks to see if that move could possibly cause an overflow
    (i.e. a strength sum >255).
    :param move: The move to check
    :return: True if the move could cause an overflow, else False
    """
    target = game_map.get_target(move.square, move.direction)
    for direction, neighbor in enumerate(game_map.neighbors(target, 1, True)):
        # If the square and a neighbor of the target sum to more than 255, give the
        # stronger of the two the right-of-way (i.e. return True for the weaker of
        # the two. Break ties with the heuristic score sums. If the heuristic score
        # sums are also tied, give one the right-of-way at random
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

    return False


def get_move_precedence(square):
    """Creates a list of moves in order from best to worst for a given square.
    :param square: The square to check
    :return: The list of moves
    """
    move_precedence = []

    # Attack the enemy if possible
    direction, target = find_max_heuristic_neighbor(square)
    if direction is not None and square.strength > target.strength:
        move_precedence.append(Move(square, direction))

    # Wait if strength is low
    if square.strength < min_strength * square.production:
        move_precedence.append(Move(square, STILL))

    # Check if combining with neighbor makes neighbor strong enough
    for direction, neighbor in enumerate(game_map.neighbors(square)):
        if not check_strong_enough(neighbor) and neighbor.owner == myID and \
                sum_heuristic_neighbors(square) < sum_heuristic_neighbors(neighbor):
            move_precedence.append(Move(square, direction))

    # Move towards the closest border if not a border piece
    if not check_is_border(square):
        move_precedence.append(Move(square, find_nearest_enemy_direction(square)))

    # Add all other directions to move_precedence list
    for d in (STILL, NORTH, EAST, SOUTH, WEST):
        if Move(square, d) not in move_precedence:
            move_precedence.append(Move(square, d))

    return move_precedence


def check_moves(move_precedence):
    """Goes through a list of possible moves and returns the first one that
    doesn't potentially cause an overflow.
    :param move_precedence: The list of moves
    :return: A move that won't cause overflow
    """
    for move in move_precedence:
        target = game_map.get_target(move.square, move.direction)

        if not check_overflow(move):
            return move

        elif target.owner != myID and target.owner != 0:
            return move

    return Move(move_precedence[0].square, STILL)


while True:
    game_map.get_frame()

    moves = []
    for square in game_map:
        if square.owner == myID:
            move_precedence = get_move_precedence(square)
            move = check_moves(move_precedence)
            moves.append(move)

    hlt.send_frame(moves)
