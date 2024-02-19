def print_board(board):
    for row in reversed(board):
        print(" ".join(row))

def initialize_board(num_rows, num_cols):
    return [["-" for _ in range(num_cols)] for _ in range(num_rows)]

def insert_chip(board, position, chip_type):
    row, col = position_to_index(position)
    if board[row][col] == "-":
        board[row][col] = chip_type
        return row
    return -1

def check_if_winner(board, position, chip_type):
    row, col = position_to_index(position)
    # Check horizontally
    count = 0
    for c in range(len(board[row])):
        if board[row][c] == chip_type:
            count += 1
            if count == 4:
                return True
        else:
            count = 0

    # Check vertically
    count = 0
    for r in range(len(board)):
        if board[r][col] == chip_type:
            count += 1
            if count == 4:
                return True
        else:
            count = 0

    # No diagonal check as per assumptions
    return False

def position_to_index(position):
    row, col = map(int, position.split("-"))
    return row - 1, col - 1

# Main function
def main():
    print("Welcome to Connect-Four!")
    num_rows = int(input("What would you like the height of the board to be? "))
    num_cols = int(input("What would you like the length of the board to be? "))
    print()

    board = initialize_board(num_rows, num_cols)
    print_board(board)
    print()

    print("Player 1: x")
    print("Player 2: o")
    print()

    players = ['x', 'o']
    turn = 0
    while True:
        player = players[turn % 2]
        position = input(f"Player {player}: Enter position (e.g., 1-1, 2-3): ")
        row, col = position_to_index(position)
        row = insert_chip(board, position, player)
        print_board(board)
        print()

        if check_if_winner(board, position, player):
            print(f"Player {player} won the game!")
            break

        turn += 1

        # Check for a tie
        if all(cell != '-' for row in board for cell in row):
            print("Draw. Nobody wins.")
            break

if __name__ == "__main__":
    main()
