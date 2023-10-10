import timeit
from functools import reduce
import copy

global guesses
guesses = 0
row_column = [(cell // 9, cell % 9) for cell in range(81)]

cell_to_box = [((cell // 9) // 3) * 3 + ((cell % 9) // 3) for cell in range(81)]


def get_connected_cells(cell):  # TODO hardcode this
    row, column = row_column[cell]
    box = cell_to_box[cell]

    row_cells = list(range(row_start := row * 9, row_start + 9))
    column_cells = list(range(column, column + 73, 9))
    box_start = ((box // 3) * 27) + (box % 3) * 3
    box_cells = [[left_most, left_most + 1, left_most + 2] for left_most in range(box_start, box_start + 27, 9)]
    box_cells = [cell for group_of_cells in box_cells for cell in group_of_cells]
    return list(set(row_cells + column_cells + box_cells))


peers = [get_connected_cells(cell) for cell in range(81)]

kill_all_9 = 0b000000000
all_set = 0b111111111111111111111111111111111111111111111111111111111111111111111111111111111
candidate_layers = [
    0b111111111111111111111111111111111111111111111111111111111111111111111111111111111,
    0b111111111111111111111111111111111111111111111111111111111111111111111111111111111,
    0b111111111111111111111111111111111111111111111111111111111111111111111111111111111,
    0b111111111111111111111111111111111111111111111111111111111111111111111111111111111,
    0b111111111111111111111111111111111111111111111111111111111111111111111111111111111,
    0b111111111111111111111111111111111111111111111111111111111111111111111111111111111,
    0b111111111111111111111111111111111111111111111111111111111111111111111111111111111,
    0b111111111111111111111111111111111111111111111111111111111111111111111111111111111,
    0b111111111111111111111111111111111111111111111111111111111111111111111111111111111
]

row_bitmasks = [
    0b111111111000000000000000000000000000000000000000000000000000000000000000000000000,
    0b000000000111111111000000000000000000000000000000000000000000000000000000000000000,
    0b000000000000000000111111111000000000000000000000000000000000000000000000000000000,
    0b000000000000000000000000000111111111000000000000000000000000000000000000000000000,
    0b000000000000000000000000000000000000111111111000000000000000000000000000000000000,
    0b000000000000000000000000000000000000000000000111111111000000000000000000000000000,
    0b000000000000000000000000000000000000000000000000000000111111111000000000000000000,
    0b000000000000000000000000000000000000000000000000000000000000000111111111000000000,
    0b000000000000000000000000000000000000000000000000000000000000000000000000111111111
]

column_bitmasks = [
    0b100000000100000000100000000100000000100000000100000000100000000100000000100000000,
    0b010000000010000000010000000010000000010000000010000000010000000010000000010000000,
    0b001000000001000000001000000001000000001000000001000000001000000001000000001000000,
    0b000100000000100000000100000000100000000100000000100000000100000000100000000100000,
    0b000010000000010000000010000000010000000010000000010000000010000000010000000010000,
    0b000001000000001000000001000000001000000001000000001000000001000000001000000001000,
    0b000000100000000100000000100000000100000000100000000100000000100000000100000000100,
    0b000000010000000010000000010000000010000000010000000010000000010000000010000000010,
    0b000000001000000001000000001000000001000000001000000001000000001000000001000000001
]

box_bitmasks = [
    0b111000000111000000111000000000000000000000000000000000000000000000000000000000000,
    0b000111000000111000000111000000000000000000000000000000000000000000000000000000000,
    0b000000111000000111000000111000000000000000000000000000000000000000000000000000000,
    0b000000000000000000000000000111000000111000000111000000000000000000000000000000000,
    0b000000000000000000000000000000111000000111000000111000000000000000000000000000000,
    0b000000000000000000000000000000000111000000111000000111000000000000000000000000000,
    0b000000000000000000000000000000000000000000000000000000111000000111000000111000000,
    0b000000000000000000000000000000000000000000000000000000000111000000111000000111000,
    0b000000000000000000000000000000000000000000000000000000000000111000000111000000111,
]

positive_cell_masks = [1 << 80 - bit for bit in range(81)]

row_column_box_elimination_negative_bitmasks = [
    ~(box_bitmasks[(row // 3) * 3 + (column // 3)] | column_bitmasks[column] | row_bitmasks[row]) for row in
    range(9)
    for column in range(9)]

row_column_box_positive_bitmasks = [(box_bitmasks[(row // 3) * 3 + (column // 3)] | column_bitmasks[column] | row_bitmasks[row]) for row in
                                    range(9)
                                    for column in range(9)]


def eliminate_cell_from_layer(layer, cell):
    layer &= ~positive_cell_masks[cell]
    return layer


def assign_candidate_to_layer_cell(layer, cell):
    layer &= row_column_box_elimination_negative_bitmasks[cell]
    layer = set_bit(layer, cell)  # TODO see if this can be done with modification of layers instead of reassignment
    return layer


def is_solved(layers):
    if not layers:
        return False
    for candidate_layer in layers:
        if int.bit_count(candidate_layer) != 9:
            return False
    if int.bit_count(reduce(lambda a, b: a | b, layers)) == 81:
        return True
    return False


def set_bit(layer, cell):  # TODO standardise where you are indexing from you fucking idiot
    """Sets the bit, indexed from 0 from the right"""
    positive_mask = positive_cell_masks[cell]  # TODO not sure if this is the right number
    return layer | positive_mask


def check_for_empty_cells(layers):
    super_layer = reduce(lambda a, b: a | b, layers)
    if int.bit_count(super_layer) < 81:
        return True
    return False


def check_for_singles(layers, layers_to_check, cell):  # TODO see if passing a list instead of list indexes and bigger list is
    # more
    # efficient
    # TODO apply mask to layer to check, record indexes of set bits
    # TODO go to next number, apply mask, check if indexes
    row, column = row_column[cell]
    box = cell_to_box[cell]
    row_mask = row_bitmasks[row]
    column_mask = column_bitmasks[column]
    box_mask = box_bitmasks[box]

    single_candidates = []
    locations_of_single_candidates = []

    for constraint in [row_mask, column_mask, box_mask]:
        while constraint != 0:  # bits are still set to check TODO check for speed ups here
            rightmost_cell_to_check = constraint & -constraint  # get set bit to check for singles at
            if candidates := get_candidates(layers, cell=get_index_of_least_significant_bit(rightmost_cell_to_check),
                                            cell_mask=rightmost_cell_to_check) == 1:  # TODO clean this up
                # only one candidate exists in cell_i, and that candidate is candidates
                if candidates in layers_to_check:
                    single_candidates.append(candidates)
                    locations_of_single_candidates.append(get_index_of_least_significant_bit(rightmost_cell_to_check))
            constraint ^= rightmost_cell_to_check

    return single_candidates, locations_of_single_candidates


def parse_puzzle(layers, puzzle_string):
    for cell, candidate in enumerate(puzzle_string):
        if candidate != ".":
            candidate = int(candidate) - 1
            layers = assign_and_propagate(layers, cell, candidate)
            if layers is False:
                print("puzzle is not valid instantiation")
                return
    return layers


def show_layers(layers, target_layer=None):
    if layers is not False:
        for i, layer in enumerate(layers):
            if target_layer is None or target_layer == i:
                print(i + 1)
                layer = format(layer, '081b')
                rows = [layer[row: row + 9] for row in range(0, 81, 9)]
                for row in rows:
                    print(row)
                print()


def get_candidates(layers, cell, cell_mask=None):
    if cell_mask is None:
        cell_mask = positive_cell_masks[cell]
    return [candidate for candidate, layer in enumerate(layers) if layer & cell_mask != 0]  # might be able to use >1 here


def show_binary_number(number, padding=True):
    if padding:
        print(format(number, '081b'))
    else:
        print(bin(number))


def get_index_of_least_significant_bit(n):
    index_of_positive_bit = (n & -n).bit_length() - 1
    if index_of_positive_bit < 0:
        index_of_positive_bit = 0

    index_of_positive_bit = 80 - index_of_positive_bit
    return index_of_positive_bit


def check_for_unsatisfiable_clause(layers, cell):
    row, column = row_column[cell]
    box = cell_to_box[cell]
    row_mask = row_bitmasks[row]
    column_mask = column_bitmasks[column]
    box_mask = box_bitmasks[box]

    for constraint in [row_mask, column_mask, box_mask]:
        for layer in layers:
            if layer & constraint == 0:
                # candidate cannot go in any cell in that clause
                return True
    return False


def assign_and_propagate(layers, cell, candidate):
    other_candidates = get_candidates(layers, cell)
    other_candidates.remove(candidate)
    """ works by eliminating candidate from surrounding cells, checking for validity, then propagating"""
    layers = [eliminate_cell_from_layer(layer, cell) if c != candidate else assign_candidate_to_layer_cell(layer, cell) for c, layer in
              enumerate(layers)]

    if check_for_empty_cells(layers) or check_for_unsatisfiable_clause(layers, cell):  # a cell has no possible candidates and hasn't been
        # filled TODO can probably use
        # other_candidates to
        # reduce iteration
        return False
    #
    # by assigning given candidate to given cell, you eliminate all other candidates that could have been placed in that cell
    # see if this
    single_locations, singles = check_for_singles(layers, other_candidates, cell)
    if singles:
        for single_candidate, cell in zip(singles, single_locations):
            layers = assign_and_propagate(layers, cell, single_candidate)  # make sure this is updating and feeding back
            return layers

    single_locations, singles = check_for_hidden_singles(layers, other_candidates, cell)
    if singles:
        for single_candidate, cell in zip(singles, single_locations):
            layers = assign_and_propagate(layers, cell, single_candidate)  # not updating properly
            return layers
    return layers


def check_for_hidden_singles(layers, other_candidates, cell):
    row, column = row_column[cell]
    box = cell_to_box[cell]
    row_mask = row_bitmasks[row]
    column_mask = column_bitmasks[column]
    box_mask = box_bitmasks[box]

    single_candidates = []
    single_locations = []

    for constraint in [row_mask, column_mask, box_mask]:
        for candidate in other_candidates:
            if int.bit_count(mod := layers[candidate] & constraint) == 1:
                # candidate can only go in single cell in this constraint
                single_candidates.append(candidate)
                single_locations.append(get_index_of_least_significant_bit(mod))

    return single_locations, single_candidates


def layers_to_grid(layers):
    string = ''
    for cell in range(81):
        if len(cands := get_candidates(layers, cell)) == 1:
            string += str(cands[0] + 1)
        else:
            string += '.'
    return string


# ============== MAIN ==============
def search(modified_layer):
    global guesses
    if modified_layer is False:
        # assigment ended badly - some sort of unsatisfactory layers
        # go back a step, try different possible value
        return False
    if is_solved(modified_layer):
        # solved, back up
        return modified_layer
    ## get the cell with the fewest candidates
    open_cells = [(cell, get_candidates(modified_layer, cell)) for cell in range(81) if len(get_candidates(modified_layer, cell)) > 1]
    most_constrained_cell, possible_candidates = min(open_cells, key=lambda a: len(a[1]))  # TODO check this is working, making way too
    # many guesses
    # propagation has stopped - need to continue by searching - pick a value and
    for candidate_to_fill_most_constrained_cell in possible_candidates:
        guesses += 1
        # pick value to put in most constrained cell, propagate as far as possible,
        layers = search(assign_and_propagate(copy.deepcopy(modified_layer), most_constrained_cell, candidate_to_fill_most_constrained_cell))
        # at least one of the candidates must go in the cell, or some previous candidate choice was incorrect
        if layers:
            return layers
    # some previous choice was wrong - no candidate in the most constrained cell could satisfy the puzzle, backup and try another value
    return False


def show_puzzle(puzzle):
    print("+" + "---+" * 9)
    rows = [puzzle[row: row + 9] for row in range(0, 81, 9)]
    for i, row in enumerate(rows):
        print(("|" + " {}   {}   {} |" * 3).format(*[x if x != "." else " " for x in row]))
        if i % 3 == 2:
            print("+" + "---+" * 9)
        else:
            print("+" + "   +" * 9)
