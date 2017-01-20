import hlt
from hlt import NORTH, EAST, SOUTH, WEST, STILL, Move, Square
import random


myID, game_map = hlt.get_init()
hlt.send_init("MyPythonBot")


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


def assign_move(square):
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


# def assign_move(square):
#     for direction, neighbor in enumerate(game_map.neighbors(square)):
#         if neighbor.owner != myID and neighbor.strength < square.strength:
#             return Move(square, direction)
#
#     if square.strength < 5 * square.production:
#         return Move(square, STILL)
#     else:
#         return Move(square, random.choice((NORTH, WEST)))

while True:
    game_map.get_frame()
    moves = [assign_move(square) for square in game_map if square.owner == myID]
    hlt.send_frame(moves)
