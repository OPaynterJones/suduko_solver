import solver
import copy
import os

print(os.getcwd())
problem_path = r"test_problems/magictourtop1465.txt"

with open(problem_path, "r") as f:
    puzzles = f.read().splitlines()

for puzzle in puzzles:
    solver.show_puzzle(puzzle)
    start = copy.deepcopy(solver.candidate_layers)
    initial_state = solver.parse_puzzle(start, puzzle)
    print("initialise state:")
    solver.show_puzzle(solver.layers_to_grid(initial_state))

    print("\n\nsolving now")
    solved = solver.search(initial_state)
    solver.show_puzzle(solver.layers_to_grid(solved))