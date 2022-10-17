import random

from dlgo.gotypes import Player, Point

def to_python(player_state):
    if player_state is None:
        return 'None'
    if player_state == Player.black:
        return Player.black
    return Player.white

MAX63 = 0x7fffffffffffffff

table = {}
empty_board = 0
for row in range(1,20):
    for col in range(1,20):
        for state in (Player.black, Player.white):
            code = random.randint(0, MAX63)
            table[Point(row, col), state] = code

print('from .gotypes import Player, Point')
print('')
print("__all__ = ['HASH CODE', 'EMPTY_BOARD']")
print('')
print('HASH_CODE = {')
for(pt, state),hash_code in table.items():
    print(' (%r, %s): %r,' % (pt, to_python(state), hash_code))
print('}')
print('')
print('EMPTY_BOARD = %d' % (empty_board,))                      #이거 괄호 안에 컴마 다음에 왜 비워둔거임? 뭐지?

#여기도 아직 정확히 의미 파악 못함 -> 어느정도 한듯, 근데 12~31까지는 함수를 정의하지 않았는데, 어떻게 역할하는거지?