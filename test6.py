from dlgo.gosgf import Sgf_game
from dlgo.goboard_fast import GameState, Move
from dlgo.gotypes import Point
from dlgo.utils import print_board

sgf_content="(;GM[1]FF[4]CA[UTF-8]SZ[19]RU[Chinese];B[ee];W[ef];B[ff];W[df];B[fe];W[fc];B[ec];W[gd];B[fb])"
sgf_game = Sgf_game.from_string(sgf_content)

game_state = GameState.new_game(19)

def press_enter():
    print("")
    input("\tPress Enter Key to Continue . . .")
    print("")

count=0
for item in sgf_game.main_sequence_iter():
    color,move_tuple = item.get_move()

    print(item)
    print(count)
    print('//')
    count+=1