from flask import Flask, render_template, request, jsonify
import math
import random

def solve_sudoku(grid, size):
    '''Solves a Sudoku puzzle using backtracking.'''
    for r in range(size):
        for c in range(size):
            if grid[r][c] == 0:
                values = list(range(1, size + 1))
                random.shuffle(values)
                for num in values:
                    if is_valid(grid, r, c, num, size):
                        grid[r][c] = num
                        if solve_sudoku(grid, size):
                            return True
                        grid[r][c] = 0
                return False
    return True

def is_valid(grid, r, c, num, size):
    '''Checks if placing num at (r, c) is valid.'''
    for x in range(size):
        if grid[r][x] == num:
            return False
    for x in range(size):
        if grid[x][c] == num:
            return False
    box_size = int(math.sqrt(size))
    start_row = r - r % box_size
    start_col = c - c % box_size
    for i in range(box_size):
        for j in range(box_size):
            if grid[i + start_row][j + start_col] == num:
                return False
    return True

def generate_solved_sudoku(size):
    '''Generates a completely solved Sudoku grid of the specified size.'''
    grid = [[0 for _ in range(size)] for _ in range(size)]
    solve_sudoku(grid, size)
    return grid

def remove_numbers_for_difficulty(grid, difficulty):
    '''Removes numbers from a solved Sudoku grid based on difficulty.
    Attempts to ensure a unique solution (though not foolproof without a robust solver).
    '''
    puzzle = [row[:] for row in grid]
    size = len(puzzle)
    total_cells = size * size
    if size == 4:
        if difficulty == 'easy':
            cells_to_remove = random.randint(4, 6)
        elif difficulty == 'medium':
            cells_to_remove = random.randint(6, 8)
        else: # 'difficult'
            cells_to_remove = random.randint(8, 10)
    else: # size == 9
        if difficulty == 'easy':
            cells_to_remove = random.randint(30, 35)
        elif difficulty == 'medium':
            cells_to_remove = random.randint(35, 40)
        else: # 'difficult'
            cells_to_remove = random.randint(40, 45)

def check_solution(grid, size):
    """Checks if the given Sudoku grid is correctly solved."""
    # Helper function to check a unit (row, column, or box)
    def is_unit_valid(unit):
        unit = [n for n in unit if n != 0] # Exclude empty cells
        return len(unit) == len(set(unit)) # Check for duplicates

    # Check all rows
    for r in range(size):
        if not is_unit_valid(grid[r]):
            return False

    # Check all columns
    for c in range(size):
        column = [grid[r][c] for r in range(size)]
        if not is_unit_valid(column):
            return False

    # Check all boxes
    box_size = int(size**0.5)
    for r_start in range(0, size, box_size):
        for c_start in range(0, size, box_size):
            box = []
            for r in range(r_start, r_start + box_size):
                for c in range(c_start, c_start + box_size):
                    box.append(grid[r][c])
            if not is_unit_valid(box):
                return False

    # Additionally, check if all cells are filled and within valid range (1 to size)
    for r in range(size):
        for c in range(size):
            num = grid[r][c]
            if num == 0 or not (1 <= num <= size): # Puzzle must be fully solved
                return False

    return True

    cells_removed_count = 0
    attempts = 0
    max_attempts = total_cells * 2
    while cells_removed_count < cells_to_remove and attempts < max_attempts:
        r = random.randint(0, size - 1)
        c = random.randint(0, size - 1)

        if puzzle[r][c] != 0:
            original_value = puzzle[r][c]
            puzzle[r][c] = 0

            # Pass a copy for solving check, ensures it's solvable
            temp_grid_for_check = [row[:] for row in puzzle]
            if solve_sudoku(temp_grid_for_check, size): # Make sure solve_sudoku receives a new copy each time
                cells_removed_count += 1
            else:
                puzzle[r][c] = original_value
        attempts += 1
    return puzzle

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_puzzle')
def generate_puzzle():
    size_param = request.args.get('size', '9x9') # Default to 9x9
    difficulty = request.args.get('difficulty', 'medium') # Default to medium

    # Convert size parameter to integer
    if size_param == '4x4':
        size = 4
    elif size_param == '9x9':
        size = 9
    else:
        return jsonify({"error": "Invalid size parameter. Must be '4x4' or '9x9'."}), 400

    if difficulty not in ['easy', 'medium', 'difficult']:
        return jsonify({"error": "Invalid difficulty parameter. Must be 'easy', 'medium', or 'difficult'."}), 400

    # Generate a solved grid
    solved_grid = generate_solved_sudoku(size)
    # Create the puzzle by removing numbers based on difficulty
    puzzle = remove_numbers_for_difficulty(solved_grid, difficulty)

    return jsonify({"puzzle": puzzle, "size": size, "difficulty": difficulty})

@app.route('/check_puzzle', methods=['POST'])
def check_puzzle():
    data = request.get_json()
    if not data or 'puzzle' not in data or 'size' not in data:
        return jsonify({"error": "Invalid request: 'puzzle' and 'size' are required."}), 400

    puzzle = data['puzzle']
    size = data['size']

    if not isinstance(puzzle, list) or not all(isinstance(row, list) and len(row) == size for row in puzzle) or len(puzzle) != size:
        return jsonify({"error": "Invalid puzzle format."}), 400

    is_correct = check_solution(puzzle, size)

    return jsonify({"is_correct": is_correct})

@app.route('/save_game', methods=['POST'])
def save_game():
    data = request.get_json()
    if not data or 'puzzle' not in data or 'time' not in data or 'difficulty' not in data or 'size' not in data:
        return jsonify({"error": "Invalid request: puzzle, time, difficulty, and size are required."}), 400

    game_state = {
        "puzzle": data['puzzle'],
        "time": data['time'],
        "difficulty": data['difficulty'],
        "size": data['size']
    }

    saved_games = []
    if os.path.exists(GAME_DATA_FILE):
        with open(GAME_DATA_FILE, 'r') as f:
            try:
                saved_games = json.load(f)
            except json.JSONDecodeError:
                saved_games = [] # Handle empty or malformed JSON file

    # Assign a simple ID for the saved game (e.g., current number of games + 1)
    game_id = len(saved_games) + 1
    game_state['id'] = game_id
    saved_games.append(game_state)

    with open(GAME_DATA_FILE, 'w') as f:
        json.dump(saved_games, f, indent=4)

    return jsonify({"message": "Game saved successfully!", "id": game_id}), 201

@app.route('/load_game/<int:game_id>', methods=['GET'])
def load_game(game_id):
    if not os.path.exists(GAME_DATA_FILE):
        return jsonify({"error": "No saved games found."}), 404

    with open(GAME_DATA_FILE, 'r') as f:
        try:
            saved_games = json.load(f)
        except json.JSONDecodeError:
            return jsonify({"error": "No saved games found or file is corrupted."}), 404

    for game in saved_games:
        if game.get('id') == game_id:
            return jsonify(game), 200

    return jsonify({"error": f"Game with ID {game_id} not found."}), 404

@app.route('/get_hint', methods=['POST'])
def get_hint():
    data = request.get_json()
    if not data or 'puzzle' not in data or 'size' not in data:
        return jsonify({"error": "Invalid request: 'puzzle' and 'size' are required."}), 400

    current_puzzle = data['puzzle']
    size = data['size']

    # Make a deep copy to find a hint without modifying the original puzzle
    temp_puzzle_for_hint = [row[:] for row in current_puzzle]

    empty_cell_found = False
    hint_row, hint_col, hint_value = -1, -1, -1

    # Find the first empty cell
    for r in range(size):
        for c in range(size):
            if temp_puzzle_for_hint[r][c] == 0:
                empty_cell_found = True
                # Temporarily place a 0 in the original position to allow solve_sudoku to fill it
                temp_puzzle_for_hint[r][c] = 0 
                # Attempt to solve the puzzle from this state
                if solve_sudoku(temp_puzzle_for_hint, size):
                    hint_row, hint_col, hint_value = r, c, temp_puzzle_for_hint[r][c]
                    return jsonify({"row": hint_row, "col": hint_col, "value": hint_value}), 200
                else:
                    # If the puzzle is unsolvable from this state, it means the current user input led to an unsolvable state
                    return jsonify({"error": "Puzzle is currently unsolvable, cannot provide a hint."}), 400
    
    if not empty_cell_found:
        return jsonify({"message": "Puzzle is already completed!"}), 200
    
    # Fallback if no hint found (should not be reached if empty_cell_found is True and solve_sudoku works)
    return jsonify({"error": "Could not find a valid hint."}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_puzzle')
def generate_puzzle():
    size_param = request.args.get('size', '9x9') # Default to 9x9
    difficulty = request.args.get('difficulty', 'medium') # Default to medium

    if size_param == '4x4':
        size = 4
    elif size_param == '9x9':
        size = 9
    else:
        return jsonify({"error": "Invalid size parameter. Must be '4x4' or '9x9'."}), 400

    if difficulty not in ['easy', 'medium', 'difficult']:
        return jsonify({"error": "Invalid difficulty parameter. Must be 'easy', 'medium', or 'difficult'."}), 400

    solved_grid = generate_solved_sudoku(size)
    puzzle = remove_numbers_for_difficulty(solved_grid, difficulty)

    return jsonify({"puzzle": puzzle, "size": size, "difficulty": difficulty})

@app.route('/check_puzzle', methods=['POST'])
def check_puzzle():
    data = request.get_json()
    if not data or 'puzzle' not in data or 'size' not in data:
        return jsonify({"error": "Invalid request: 'puzzle' and 'size' are required."}), 400

    puzzle = data['puzzle']
    size = data['size']

    if not isinstance(puzzle, list) or not all(isinstance(row, list) and len(row) == size for row in puzzle) or len(puzzle) != size:
        return jsonify({"error": "Invalid puzzle format."}), 400

    is_correct = check_solution(puzzle, size)

    return jsonify({"is_correct": is_correct})

@app.route('/save_game', methods=['POST'])
def save_game():
    data = request.get_json()
    if not data or 'puzzle' not in data or 'time' not in data or 'difficulty' not in data or 'size' not in data:
        return jsonify({"error": "Invalid request: puzzle, time, difficulty, and size are required."}), 400

    game_state = {
        "puzzle": data['puzzle'],
        "time": data['time'],
        "difficulty": data['difficulty'],
        "size": data['size']
    }

    saved_games = []
    if os.path.exists(GAME_DATA_FILE):
        with open(GAME_DATA_FILE, 'r') as f:
            try:
                saved_games = json.load(f)
            except json.JSONDecodeError:
                saved_games = []

    game_id = len(saved_games) + 1
    game_state['id'] = game_id
    saved_games.append(game_state)

    with open(GAME_DATA_FILE, 'w') as f:
        json.dump(saved_games, f, indent=4)

    return jsonify({"message": "Game saved successfully!", "id": game_id}), 201

@app.route('/load_game/<int:game_id>', methods=['GET'])
def load_game(game_id):
    if not os.path.exists(GAME_DATA_FILE):
        return jsonify({"error": "No saved games found."}), 404

    with open(GAME_DATA_FILE, 'r') as f:
        try:
            saved_games = json.load(f)
        except json.JSONDecodeError:
            return jsonify({"error": "No saved games found or file is corrupted."}), 404

    for game in saved_games:
        if game.get('id') == game_id:
            return jsonify(game), 200

    return jsonify({"error": f"Game with ID {game_id} not found."}), 404

@app.route('/get_hint', methods=['POST'])
def get_hint():
    data = request.get_json()
    if not data or 'puzzle' not in data or 'size' not in data:
        return jsonify({"error": "Invalid request: 'puzzle' and 'size' are required."}), 400

    current_puzzle = data['puzzle']
    size = data['size']

    temp_puzzle_for_hint = [row[:] for row in current_puzzle]

    empty_cell_found = False
    for r in range(size):
        for c in range(size):
            if temp_puzzle_for_hint[r][c] == 0:
                empty_cell_found = True
                # Call solve_sudoku on the temp_puzzle_for_hint to find a solution
                # solve_sudoku will fill the first empty cell it finds with a valid number if possible.
                if solve_sudoku(temp_puzzle_for_hint, size):
                    # After solving, the temp_puzzle_for_hint will contain the solved value at (r, c)
                    return jsonify({"row": r, "col": c, "value": temp_puzzle_for_hint[r][c]}), 200
                else:
                    return jsonify({"error": "Puzzle is currently unsolvable from this state, cannot provide a hint."}), 400

    if not empty_cell_found:
        return jsonify({"message": "Puzzle is already completed!"}), 200

    return jsonify({"error": "Could not find a valid hint (internal error or no empty cells)."})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_puzzle')
def generate_puzzle():
    size_param = request.args.get('size', '9x9') # Default to 9x9
    difficulty = request.args.get('difficulty', 'medium') # Default to medium

    if size_param == '4x4':
        size = 4
    elif size_param == '9x9':
        size = 9
    else:
        return jsonify({"error": "Invalid size parameter. Must be '4x4' or '9x9'."}), 400

    if difficulty not in ['easy', 'medium', 'difficult']:
        return jsonify({"error": "Invalid difficulty parameter. Must be 'easy', 'medium', or 'difficult'."}), 400

    solved_grid = generate_solved_sudoku(size)
    puzzle = remove_numbers_for_difficulty(solved_grid, difficulty)

    return jsonify({"puzzle": puzzle, "size": size, "difficulty": difficulty})

@app.route('/check_puzzle', methods=['POST'])
def check_puzzle():
    data = request.get_json()
    if not data or 'puzzle' not in data or 'size' not in data:
        return jsonify({"error": "Invalid request: 'puzzle' and 'size' are required."}), 400

    puzzle = data['puzzle']
    size = data['size']

    if not isinstance(puzzle, list) or not all(isinstance(row, list) and len(row) == size for row in puzzle) or len(puzzle) != size:
        return jsonify({"error": "Invalid puzzle format."}), 400

    is_correct = check_solution(puzzle, size)

    return jsonify({"is_correct": is_correct})

@app.route('/save_game', methods=['POST'])
def save_game():
    data = request.get_json()
    if not data or 'puzzle' not in data or 'time' not in data or 'difficulty' not in data or 'size' not in data:
        return jsonify({"error": "Invalid request: puzzle, time, difficulty, and size are required."}), 400

    game_state = {
        "puzzle": data['puzzle'],
        "time": data['time'],
        "difficulty": data['difficulty'],
        "size": data['size']
    }

    saved_games = []
    if os.path.exists(GAME_DATA_FILE):
        with open(GAME_DATA_FILE, 'r') as f:
            try:
                saved_games = json.load(f)
            except json.JSONDecodeError:
                saved_games = []

    game_id = len(saved_games) + 1
    game_state['id'] = game_id
    saved_games.append(game_state)

    with open(GAME_DATA_FILE, 'w') as f:
        json.dump(saved_games, f, indent=4)

    return jsonify({"message": "Game saved successfully!", "id": game_id}), 201

@app.route('/load_game/<int:game_id>', methods=['GET'])
def load_game(game_id):
    if not os.path.exists(GAME_DATA_FILE):
        return jsonify({"error": "No saved games found."}), 404

    with open(GAME_DATA_FILE, 'r') as f:
        try:
            saved_games = json.load(f)
        except json.JSONDecodeError:
            return jsonify({"error": "No saved games found or file is corrupted."}), 404

    for game in saved_games:
        if game.get('id') == game_id:
            return jsonify(game), 200

    return jsonify({"error": f"Game with ID {game_id} not found."}), 404

@app.route('/get_hint', methods=['POST'])
def get_hint():
    data = request.get_json()
    if not data or 'puzzle' not in data or 'size' not in data:
        return jsonify({"error": "Invalid request: 'puzzle' and 'size' are required."}), 400

    current_puzzle = data['puzzle']
    size = data['size']

    temp_puzzle_for_hint = [row[:] for row in current_puzzle]

    empty_cell_found = False
    for r in range(size):
        for c in range(size):
            if temp_puzzle_for_hint[r][c] == 0:
                empty_cell_found = True
                # Call solve_sudoku on the temp_puzzle_for_hint to find a solution
                # solve_sudoku will fill the first empty cell it finds with a valid number if possible.
                if solve_sudoku(temp_puzzle_for_hint, size):
                    # After solving, the temp_puzzle_for_hint will contain the solved value at (r, c)
                    return jsonify({"row": r, "col": c, "value": temp_puzzle_for_hint[r][c]}), 200
                else:
                    return jsonify({"error": "Puzzle is currently unsolvable from this state, cannot provide a hint."}), 400

    if not empty_cell_found:
        return jsonify({"message": "Puzzle is already completed!"}), 200

    return jsonify({"error": "Could not find a valid hint (internal error or no empty cells)."})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
