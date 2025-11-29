from flask import Flask, render_template, jsonify
import random

app = Flask(__name__)

# Sudoku Generation Logic
def is_valid(board, row, col, num, size):
    # Check row
    for x in range(size):
        if board[row][x] == num:
            return False

    # Check column
    for x in range(size):
        if board[x][col] == num:
            return False

    # Check box
    start_row = row - row % int(size**0.5)
    start_col = col - col % int(size**0.5)
    for i in range(int(size**0.5)):
        for j in range(int(size**0.5)):
            if board[i + start_row][j + start_col] == num:
                return False
    return True

def solve_sudoku(board, size):
    for r in range(size):
        for c in range(size):
            if board[r][c] == 0:
                for num in random.sample(range(1, size + 1), size):
                    if is_valid(board, r, c, num, size):
                        board[r][c] = num
                        if solve_sudoku(board, size):
                            return True
                        board[r][c] = 0 # Backtrack
                return False
    return True

def generate_solved_sudoku(size):
    board = [[0 for _ in range(size)] for _ in range(size)]
    solve_sudoku(board, size)
    return board

def remove_cells(board, difficulty):
    if difficulty == 'easy':
        cells_to_remove = int(len(board) * len(board) * 0.4) # ~40% for easy
    elif difficulty == 'medium':
        cells_to_remove = int(len(board) * len(board) * 0.5) # ~50% for medium
    elif difficulty == 'hard':
        cells_to_remove = int(len(board) * len(board) * 0.6) # ~60% for hard
    else:
        cells_to_remove = int(len(board) * len(board) * 0.4) # Default to easy

    puzzle = [row[:] for row in board] # Create a copy
    removed_count = 0

    all_coords = [(r, c) for r in range(len(board)) for c in range(len(board))]
    random.shuffle(all_coords)

    for r, c in all_coords:
        if removed_count >= cells_to_remove:
            break

        if puzzle[r][c] != 0:
            temp = puzzle[r][c]
            puzzle[r][c] = 0
            # We could add a check here to ensure the puzzle still has a unique solution
            # For simplicity, we skip this for now.
            removed_count += 1

    return puzzle

# Flask Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_puzzle/<int:size>/<string:difficulty>')
def generate_puzzle_route(size, difficulty):
    if size not in [4, 9]:
        return jsonify({'error': 'Invalid size. Must be 4 or 9.'}), 400
    if difficulty not in ['easy', 'medium', 'hard']:
        return jsonify({'error': 'Invalid difficulty. Must be easy, medium, or hard.'}), 400

    solved_board = generate_solved_sudoku(size)
    puzzle_board = remove_cells(solved_board, difficulty)

    return jsonify({'puzzle': puzzle_board, 'solution': solved_board})

if __name__ == '__main__':
    app.run(debug=True)
