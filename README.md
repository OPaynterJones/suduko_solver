Please note that this was a task issued as a part of my Artificial Intelligence module, so the task specification, test code, etc. have been ommited per university requirements.


# The fastest solver

to my knowledge, the fastest solver for sudukos, of all calibers, is Tom Dillon's solver [**Tduko**](https://github.com/t-dillon/tdoku). As
outlined in a [post](https://t-dillon.github.io/tdoku/#PracticalPerformance) authored by him, he
approaches the puzzles as constraint satisfaction problems.

Omitting a good deal of techniques that Tom uses to make approach the fastest, the solver uses the DPLL algorithm to
attempt to find states for all the literals that satisfy a given set of clauses.\
It should be noted that the
"conventional" Sudoku constraints - only one candidate per row|column|box - are not represented explicitly, but implicitly through
the use of what
Tom calls "triads" which, to reduce them substantially, group up some literals and help to make the application of techniques like
_locked-candidates_ quicker and simpler.

All that said, a propositional approach to Sudoku like Tduko's only reduces the amount of "guessing" a solver does; the propositional
approach, triads and all, is still slow compared to the other solvers out there, like JCZsolve for example. The key to the speed of Tduko,
is in C's
bitvectors and
the SIMD operations that can process bitvectors unbelievably fast.

Representing all of the above using bitvectors and restricting operations on these bitvectors to exclusively SIMD operations, Tduko has
both the reduced search length as a result of the quick and accurate guessing, but also the speed to dominate all the other solvers.

Unfortunately... Python does not have the finesse of a langauge like C that would make a propositional approach to Sudoko solving
feasible.

# Another approach

Taking a step back from this therefor, the next best thing would be something a little more simple, like backtracking search or more
specifically the Dancing Links algorithm. Whilst DLX is fast, to my knowledge, when pitted against a slightly modified backtracking
search, it won't perform quite as well. Peter Norvig [demonstrated](http://norvig.com/sudoku.html) that a solver need not be complicated 
or use an algorithm like DLX,
nor written in a "lower-level"
of a language like C to perform aptly. I tested this solver, and it was able to solve most puzzles in less than a second, with some 
notable exceptions where it took 60x as long. Peter discussed this issue, and the various methods that could be used to navigate the 
issue.

## My code

My approach therefor, is a simple algorithm - an implementation of the "solver-basic" solution as proposed by
Tom [here](https://t-dillon.github.io/tdoku/#TheReallyBasicSolver) - backtracking, combined
with a
simple
search heuristic
optimised for
Python and all it's
nitpicks:

Storing each of the rows, columns, and blocks as a 9 bit integer, where a set bit represents that a candidate has yet to be
placed in that row|column|box. For example, at the least significant bit on the far right of the integer, a set bit means that a 1 has 
yet to be placed there. The only 
operations 
required to 
complete the search in a timely manner, namely picking the next cell and
candidate to
propagate with and eliminating the candidate from other cells, can be done using bitwise operations exclusively,
which is
thankfully something Python can just about manage.

Each iteration of the search, we sort the "cells left to fill" by the number of candidates that can be placed in said cells - this is the
part of the
search which takes place the most, and also takes the longest - thankfully, storing cells in terms of their row, column, and box
candidates with binary integers lend themselves to this
process quite nicely. \
Next, we take the first item in the cell-todo list (_note that this means we propagate on any singles here - other
solvers might look for these cells explicitly, whereas here it's a natural byproduct of the sorting process_) before assigning a
possible candidate to that
cell, "marking" it as done in the todo list, and then calling the search function recursively on this new puzzle state. If puzzle reaches a
point where the first item in that sorted list of cells to fill has 0 candidates, it can be deduced that some assignment up the call
stack was wrong - backup and try a different candidate. Otherwise, the search continues until the todo list is completed and a
solution has been found.

### Implementation

Implementing this approach in Python, I tested a good variety of tweaks, very few of which actually served to improve anything. \
For
example, the
arrays were never big enough to warrant using Numpy arrays with their O(1) lookup times considering the overhead associated with using
them;
strings were sometimes preferable to
lists as
their "deepcopy" was infinitely more efficient, as can be seen [implemented](http://norvig.com/sudoku.html) by Peter with a fairly
similar approach. This means however, that I would be restricted exclusively to string manipulation as an operation, which would inevitably
result in more instances of iteration than desired; a significant time boost could be yielded through the use of C coded python extension 
modules like
GMPY, but alas that is outside the
scope of this project as such modules are not part of the standard Python library.

I also tried various heuristic approaches: used in conjunction with the row-column-block data structure, sure, things like searching for
hidden-singles or locked-cells are _possible_, but those tasks are not remotely practical as the data structure just does not lend to 
the 
approach
whatsoever. The only alteration that could be made to the search heuristic without compromising on its speed, would be to look for full,
or
almost-full,
houses - a
column|row|box only has one or two cells left to place, providing an ample opportunity for speedy propagation. It would only make sense
to search for these situations if every cell had ~3 candidates at minimum per the preliminary sort (therefor finding a full or almost-full
house would provide
some actual benefit), which happens *some* of the time. Having that happen in conjunction with having a row|column|box in the
aforementioned state however... Over thousands of the hardest puzzles, just it just doesn't happen. **At all.** This
potential modification to the
heuristic can be written off.

Some changes did make a difference though: using lookup tables in the form of a dictionary were far superior a Numpy list, regular list, 
or the builtin method for counting the set bits in a binary integer:
```python
# Fastest
pop_counts = dict(zip([x for x in range(2 ** 9)], [int.bit_count(x) for x in range(2 ** 9)]))

# Fast
pop_counts = [int.bit_count(x) for x in range(2 ** 9)]

# Pointless
pop_counts = Numpy.array([int.bit_count(x) for x in range(2 ** 9)])
```
Additionally, as attractive as the prospect may seem, using classes to represent cells to link them to rows, columns, and boxes in the 
style of OOP only 
slows things down. The solver can be distilled down to a few functions and I noticed a significant solve-time decrease in making some a 
lot of the variables global to avoid passing more than one or two parameters between methods and just "updating" those variables instead.

To conclude, it seems to me that what makes fast-solvers fast, is not the search itself or what they use as a heuristic, but
the use of
datastructure(s)
implemented in a
langauge that makes sense given the context, which in turn gives the programmer a little leeway in regard to how they guide the search -
hidden-singles or otherwise.
 
## Code

Import the basic modules for faster C maths:
```python
import math
import numpy as np
```

Set up the presets, global variables, and lookup tables.
```python
full = 0b111111111

row_col_box = [(cell // 9, cell % 9, ((cell // 9) // 3) * 3 + (cell % 9) // 3) for cell in range(81)]

candidate_masks = [1 << candidate for candidate in range(9)]

pop_counts = dict(zip([x for x in range(2 ** 9)], [int.bit_count(x) for x in range(2 ** 9)]))

cells_to_search_on, rows, columns, boxes = [], [], [], []
solution = [-1] * 81
last_cell_index = 0
```

Loads the puzzle in to the arrays
```python
def load_into_arrays(puzzle):
    global cells_to_search_on, rows, columns, boxes, solution
    puzzle = puzzle.flatten()
    for cell, value in enumerate(puzzle):
        row, column, box = row_col_box[cell]
        if value != 0:
            # cell is populated
            row, column, box = row_col_box[cell]
            # get mask to use to eliminate from the layers
            candidate_mask = candidate_masks[value - 1]
            if int.bit_count(rows[row] & candidate_mask) == 0 or int.bit_count(columns[column] & candidate_mask) == 0 or int.bit_count(
                    boxes[box] & candidate_mask) == 0:
                # bit has already been set in that row, bad load
                return False
            # eliminate candidates from relevant row & column & box
            candidate_negative = ~candidate_mask
            rows[row] &= candidate_negative
            columns[column] &= candidate_negative
            boxes[box] &= candidate_negative

            solution[row * 9 + column] = value

        else:
            # cell will need to be filled, empty currently
            cells_to_search_on.append((row, column, box))
    return True
```
Main recursive assign and search method:
```python
def assign_and_search(current_cell):
    global cells_to_search_on, rows, columns, boxes, solution, last_cell_index
```
- Sort the cells that need to be filled by the number of candidates each cell has
- AND tbe rows, columns, and boxes together to get the combination of candidates that might be placed in that cell. If 
  `possible_candidates = 0` then there are no candidates remaining.
- Get the row, column, and box of the next cell to be sorted (has the least available candidates)
```python
    cells_to_search_on[current_cell:] = sorted(cells_to_search_on[current_cell:], key=get_number_of_candidates)

    r, c, b = cells_to_search_on[current_cell]

    possible_candidate_mask = rows[r] & columns[c] & boxes[b]
```
- If candidates exist, start looping through possible options:
  - Get the mask of the least significant bit - I.e the smallest candidate. 
  - Remove that candidate from row, column and box.
  - Call the method recursively to continue the search - if either this is the last cell to fill, or the search has returned `True` fill 
    in the cell in the solution, and backup
  - If the search does not return True, return the candidate as a possibility and backup.
```python
    while possible_candidate_mask:
        # the cell has at least one candidate
        # get candidate to propagate on - the smallest candidate
        candidate_mask = get_least_significant_set_bit(possible_candidate_mask)

        # eliminate candidate from cells row, column, and box
        # can use XOR as will always be positive and quicker than AND'ing the negative
        rows[r] ^= candidate_mask
        columns[c] ^= candidate_mask
        boxes[b] ^= candidate_mask

        # try and find solution with this assignment
        if current_cell == last_cell_index or assign_and_search(current_cell + 1):
            # solution has been found, backtrack
            solution[r * 9 + c] = get_index_of_least_significant_bit(candidate_mask) + 1
            return True

        # candidate was wrong, reset
        rows[r] |= candidate_mask
        columns[c] |= candidate_mask
        boxes[b] |= candidate_mask

        # candidate does not work here, remove from possible candidate assignments to get next one in next iteration
        possible_candidate_mask = unset_least_significant_bit(possible_candidate_mask)

    # solution couldn't be found with for any value in this todo_cell, therefor previous assignment must be wrong
    return False
```
Utility methods:
```python
def get_least_significant_set_bit(n):
    return n & -n


def unset_least_significant_bit(n):
    return n & (n - 1)


def get_number_of_candidates(cell):
    global pop_counts, rows, columns, boxes
    r, c, b = cell
    return pop_counts[rows[r] & columns[c] & boxes[b]]

def get_index_of_least_significant_bit(n):
    return int(math.log2(n))


def reset_arrays():
    """ Resets rows, columns, boxes and cell-todo list to prepare for a new puzzle."""
    global cells_to_search_on, rows, columns, boxes, solution, last_cell_index

    def UPDATE_fill_units():
        """ Updates rows, columns, and boxes to represent a fresh board with all candidates populated. """
        for _ in range(9):
            rows.append(full)
            columns.append(full)
            boxes.append(full)

    cells_to_search_on, rows, columns, boxes = [], [], [], []
    solution = [-1] * 81
    last_cell_index = 0
    UPDATE_fill_units()


def is_already_solved(puzzle):
    if 0 not in puzzle:
        return True
    return False
```

## Testing

A bit of googling led me to the [_Sudoku
Enjoyers_](http://forum.enjoysudoku.com/3-77us-solver-2-8g-cpu-testcase-17sodoku-t30470-210.html#p249309) forum thread where various
contributors developed Tduko's main competition JCZsolve, as well as compiled thousands upon
thousands of the hardest puzzles that strained Sudoku solvers the most.

Running these puzzles past my solver allowed me to gradually tweak and test the aforementioned adjustments across thousands of
test-cases. On average, my solver would solve the puzzles in ~0.04 (+-0.02) seconds, with some taking ~0.5 seconds at worst - I assume
these were just puzzles that had suboptimal guessing paths, where the solver might propagate down a path to a great depth, find an issue,
backtrack and do it all over again, many, _many_ times until coming to the actual solution. This might be fixed by adjusting the heuristic
somewhat, but 0.5 seconds is more than acceptable, so I left it as is.
