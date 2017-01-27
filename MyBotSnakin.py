import hlt
from hlt import NORTH, EAST, SOUTH, WEST, STILL, Move, Square
import random
import threading
import logging

LOG_FILENAME = 'initLog.log'

# Set up a specific logger with our desired output level
my_logger = logging.getLogger('InitLogger')
my_logger.setLevel(logging.WARNING)
my_hdlr = logging.FileHandler(LOG_FILENAME)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
my_hdlr.setFormatter(formatter)
my_logger.addHandler(my_hdlr)


myID, game_map = hlt.get_init()
hlt.send_init("LowDash")
prod_mult = 3
ProductionStack = []

def init():
    game_map.get_frame()
    bgWorker(game_map, myID)

#bg thread for production analysis
def bgWorker(board, ID):
    start_square = None
    for square in board:
        if square.owner == ID:
            start_square = square
            break
    bgGetBestMove(board, ID, start_square)

def bgGetBestMove(board, ID, start_square=None):
    global ProductionStack
    production_map = [bgGetValue(board,square,start_square) for square in board if square.owner != ID and square.production > start_square.production]
    ProductionStack = sorted(production_map, key=prod_sort, reverse=True)
    
#get production value of area
def bgGetValue(board, square, start_square=None):
    alpha = 1.5
    beta = 1.5
    if start_square != None:
        distance = board.get_distance(square, start_square)
    else:
        distance = 1
    production = square.production
    for direction, neighbor in enumerate(board.neighbors(square)):
        if direction == NORTH:
            production += board.get_target(neighbor, EAST).production
        if direction == EAST:
            production += board.get_target(neighbor, SOUTH).production
        if direction == SOUTH:
            production += board.get_target(neighbor, WEST).production
        if direction == WEST:
            production += board.get_target(neighbor, NORTH).production
        production += neighbor.production
    production *= alpha
    distance /= beta
    return (production/distance, square.x, square.y)

#need in order to sort by best tiles
def prod_sort(item):
    return item[0]

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


def find_max_heuristic_border_direction(square):
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


def check_overflow(square):
    for direction, neighbor in enumerate(game_map.neighbors(square)):
        if neighbor.strength + square.strength > 255:
            return True
    return False

def find_nearest_production(square):
    global ProductionStack
    if ProductionStack[len(ProductionStack)-1] != None:
        #Used hlt.py for insparation here
        dx = min(abs(square.x - ProductionStack[len(ProductionStack)-1][1]), square.x + game_map.width - ProductionStack[len(ProductionStack)-1][1], ProductionStack[len(ProductionStack)-1][1] + game_map.width - square.x)
        dy = min(abs(square.y - ProductionStack[len(ProductionStack)-1][2]), square.y + game_map.height - ProductionStack[len(ProductionStack)-1][2], ProductionStack[len(ProductionStack)-1][2] + game_map.height - square.y)
        if dx > dy:
            if ProductionStack[len(ProductionStack)-1][1] < square.x and (game_map.width + ProductionStack[len(ProductionStack)-1][1] - square.x) > (square.x - ProductionStack[len(ProductionStack)-1][1]):
                return WEST
            else:
                return EAST
        else:
            if ProductionStack[len(ProductionStack)-1][2] < square.y and (game_map.height + ProductionStack[len(ProductionStack)-1][2] - square.y) > (square.y - ProductionStack[len(ProductionStack)-1][2]):
                return SOUTH
            else:
                return NORTH
    return STILL

def assess_movePost(square):
    global ProductionStack
    global prod_mult
    my_logger.debug("len %d" % len(ProductionStack))
    if square.x == ProductionStack[len(ProductionStack)-1][0] and square.y == ProductionStack[len(ProductionStack)-1][1]:
        ProductionStack.pop()

    # Attack the enemy if possible
    direction, target = find_max_heuristic_neighbor(square)
    if direction is not None and square.strength > target.strength:
        return Move(square, direction)

    # Wait if strength is low
    if square.strength < 3 * square.production and not check_overflow(square):
        return Move(square, STILL)

    # Check if combining with neighbor makes neighbor strong enough
    for direction, neighbor in enumerate(game_map.neighbors(square)):
        if not check_strong_enough(neighbor) and \
                                neighbor.owner == myID and \
                                neighbor.strength + square.strength <= 255 and \
                                sum_heuristic_neighbors(square) < sum_heuristic_neighbors(neighbor):
            return Move(square, direction)

    # Move towards the closest border if not a production piece
    if not check_is_border(square):
        return Move(square, find_nearest_production(square))

    # Otherwise wait
    return Move(square, STILL)

##def assess_move(square):
##    #Once processesing is done switch huristics
##    global prod_mult
##    # Attack the enemy if possible
##    direction, target = find_max_heuristic_neighbor(square)
##    if direction is not None and square.strength > target.strength:
##        prod_mult = 5
##        return Move(square, direction)
##
##    # Wait if strength is low
##    if square.strength < prod_mult * square.production and not check_overflow(square):
##        return Move(square, STILL)
##
##    # Check if combining with neighbor makes neighbor strong enough
##    for direction, neighbor in enumerate(game_map.neighbors(square)):
##        if not check_strong_enough(neighbor) and \
##                                neighbor.owner == myID and \
##                                neighbor.strength + square.strength <= 255 and \
##                                sum_heuristic_neighbors(square) < sum_heuristic_neighbors(neighbor):
##            return Move(square, direction)
##
##    # Move towards the closest border if not a border piece
##    if not check_is_border(square):
##        return Move(square, find_nearest_enemy_direction(square))
##
##    # Otherwise wait
##    return Move(square, STILL)

init()

while True:
    moves = [assess_movePost(square) for square in game_map if square.owner == myID]
    hlt.send_frame(moves)
    game_map.get_frame()
