# TicTacToe by Korwin Bieniek
import random


# custom exceptions
class NegativePlacementError(Exception):
    """Raised when one of the indexes is negative"""
    pass


class AlreadyTakenSpotError(Exception):
    """Raised when one of the indexes is already taken"""
    pass


CROSS_SYMBOL = 'X'
CIRCLE_SYMBOL = 'O'

import threading


def create_thread(target):
    thread = threading.Thread(target=target)
    thread.daemon = True
    thread.start()


# creating a TCP socket for the server
import socket

HOST = '127.0.0.1'
PORT = 65432
connection_established = False
conn, addr = None, None

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((HOST, PORT))
sock.listen(1)


def receive_data(board):
    global turn
    while True:
        data = sock.recv(1024).decode()  # receive data from the server, it is a blocking method
        data = data.split('-')  # the format of the data after splitting is: ['x', 'y', 'yourturn', 'playing']
        x, y = int(data[0]), int(data[1])
        if data[2] == 'yourturn':
            turn = True
        board.fix_spot(x - 1, y - 1, 'O')
        show_board(board)




def parse_history(text, size_of_board):
    lines = text.split('\n')
    boards = []
    for i in range(0, len(lines), size_of_board):
        board_lines = lines[i:i + size_of_board]
        board = '\n'.join(board_lines)
        boards.append(board)
    return boards


def load_history(filename, size_of_board):
    with open(filename) as doc:
        content = doc.read()
    return parse_history(content, size_of_board)


def print_board(board):
    for row in board:
        print(row)


def _create_board(size):
    rows = []
    for i in range(size):
        row = []
        for j in range(size):
            row.append('-')
        rows.append(row)
    return rows


class Board:

    def __init__(self, size):
        self.board = _create_board(size)

    def fix_spot(self, row, col, player):
        self.board[row][col] = player

    def _check_rows(self, player, board_length):
        for i in range(board_length):
            win = True
            for j in range(board_length):
                if self.board[i][j] != player:
                    win = False
                    break
            if win:
                return win

    def _check_columns(self, player, board_length):
        for i in range(board_length):
            win = True
            for j in range(board_length):
                if self.board[j][i] != player:
                    win = False
                    break
            if win:
                return win

    def _check_diagonals(self, player, board_length):
        win = True
        for i in range(board_length):
            win = True
            if self.board[i][i] != player:
                win = False
                break
        if win:
            return win

        for i in range(board_length):
            win = True
            if self.board[i][board_length - 1 - i] != player:
                win = False
                break
        if win:
            return win
        return False

    def is_win(self, player):
        if self._check_rows(player, len(self.board)) \
                or self._check_columns(player, len(self.board)) \
                or self._check_diagonals(player, len(self.board)):
            return True
        else:
            return False

    def is_draw(self):
        for row in self.board:
            for place in row:
                if place == '-':
                    return False
        return True

    def verify_functionality(self, board):

        self.board = board

        if self.is_draw():
            print("It's a draw!")
        elif self.is_win(CROSS_SYMBOL):
            print(f'Player {CROSS_SYMBOL} won the game!')
        elif self.is_win(CIRCLE_SYMBOL):
            print(f'Player {CIRCLE_SYMBOL} won the game!')
        else:
            print("Game is still running")


def show_board(board):
    for row in board.board:
        for place in row:
            print(place, end=" ")
        print()


def check_sign_placement(player, board):
    while True:
        try:
            row, col = list(
                map(int, input('Enter row and column numbers to fix spot: ').split()))
            print()
            if row < 0 or col < 0:
                raise NegativePlacementError
            elif board.board[row - 1][col - 1] != '-':
                raise AlreadyTakenSpotError
            else:
                board.fix_spot(row - 1, col - 1, player)
                save_file(board)
                return (row, col)
        except AlreadyTakenSpotError:
            print('This place is already taken, try another one')
            continue
        except NegativePlacementError:
            print('Input a positive number')
            continue
        except IndexError:
            print(f'Input a number between 1 and {len(board)}')
            continue
        except ValueError:
            print('Input two numbers separated by space')
            continue


def save_file(board):
    with open('replay.txt', 'a') as file_open:
        for item in board.board:
            file_open.write("%s\n" % item)


def start(board):
    if connection_established:
        clear_file = open('replay.txt', 'w')
        size = len(board.board)
        board.board = _create_board(size)
        save_file(board)  # save empty board

        player = CROSS_SYMBOL

        while True:
            print(f'Player {player} turn:')

            show_board(board)
            finish = board.is_win(player)
            rows_cols = check_sign_placement(player, board)
            send_data = '{}-{}-{}-{}'.format(rows_cols[0], rows_cols[1], 'yourturn', finish).encode()
            conn.send(send_data)
            print(send_data)

            if finish:
                print(f'Player {player} won the game!')
                break

            if board.is_draw():
                print("It's a draw!")
                break

        print()
        show_board(board)
        clear_file.close()


def turns_navigation(size):
    turns = load_history('replay.txt', size)
    index = 0
    print(turns[0])  # print empty board
    while True:
        turn_choice = input('To see the next turn enter \'d\''
                            ', to see the previous turn enter \'c\','
                            'to quit enter \'q\': ')
        if turn_choice == 'd':
            if index + 1 > len(turns) - 2:
                print("This was the last move")
            else:
                index += 1
                print(turns[index])

        elif turn_choice == 'c':
            if index - 1 < 0:
                print("This is the first turn, you can't go back anymore")
            else:
                index -= 1
                print(turns[index])

        elif turn_choice == 'q':
            exit()




def waiting_for_connection(board):
    global connection_established, conn, addr
    conn, addr = sock.accept()  # wait for a connection, it is a blocking method
    print('client is connected')
    connection_established = True
    start(board)
    receive_data(board)

if __name__ == '__main__':
    game_board = Board(3)
    waiting_for_connection(game_board)
    #start(game_board)
