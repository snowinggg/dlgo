import copy
from dlgo.gotypes import Player, Point
from dlgo import zobrist

class GoString():
    def __init__(self, color, stones, liberties):
        self.color = color
        self.stones = frozenset(stones)
        self.liberties = frozenset(liberties)
    '''
    def remove_liberty(self,point):
        self.liberties.remove(point)
    '''
    def without_liberty(self, point):
        new_liberties = self.liberties - set([point])
        return GoString(self.color, self.stones, new_liberties)

    '''
    def add_liberty(self,point):
        self.liberties.add(point)
    '''
    def with_liberty(self, point):
        new_liberties = self.liberties | set([point])                   # |연산과 +연산과 결과는 똑같겠지?
        return GoString(self.color, self.stones, new_liberties)

    def merged_with(self, go_string):
        assert go_string.color == self.color
        combined_stones = self.stones | go_string.stones
        return GoString(
            self.color,
            combined_stones,
            (self.liberties | go_string.liberties) - combined_stones)

    @property
    def num_liberties(self):
        return len(self.liberties)

    def __eq__(self, other):
        return isinstance(other, GoString) and \
            self.color == other.color and \
            self.stones == other.stones and \
            self.liberties == other.liberties

class Board():
    def __init__(self, num_rows, num_cols):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self._grid = {}
        self._hash = zobrist.EMPTY_BOARD                #zobrist.py에는 EMPTY_BOARD가 아니라 empty_board로 정의되어있다
                                                        #글로벌변수는 대소문자를 구분하지 않는건가?
    def place_stone(self, player, point):
        assert self.is_on_grid(point)
        assert self._grid.get(point) is None
        adjacent_same_color = []
        adjacent_opposite_color = []
        liberties = []

        for neighbor in point.neighbors():
            if not self.is_on_grid(neighbor):
                continue
                neighbor_string = self._grid.get(neighbor)
                if neighbor_string is None:
                    liberties.append(neighbor)
                elif neighbor_string.color == player:
                    if neighbor_string not in  adjacent_same_color:
                        adjacent_same_color.append(neighbor_string)
                else:
                    if neighbor_string not in adjacent_opposite_color:
                        adjacent_opposite_color.append(neighbor_string)

        new_string = GoString(player, [point], liberties)
        # [point]는 리스트형이고, GoString.__init__에서 set으로 변환됨. 다만, [point]를 정의하지 않았는데 어떻게 사용가능한지 ?
        for same_color_string in adjacent_same_color:
            new_string = new_string.merged_with(same_color_string)
        for new_string_point in new_string.stones:
            self._grid[new_string_point] = new_string
        self._hash ^= zobrist.HASH_CODE[point, player]      #github의 zobrist.py에 보면 정의되어 있긴 한데, 코드로 정의된게 아니라, print된것인데 이렇게 응용이 가능한가?
        '''
        for other_color_string in adjacent_opposite_color:
            other_color_string.remove_liberty(point)
        for other_color_string in adjacent_opposite_color:
            if other_color_string.num_liberties == 0:
                self._remove_string(other_color_string)
        '''
        for other_color_string in adjacent_opposite_color:     #이 코드 아직 제대로 이해 못함
            replacement = other_color_string.without_liberty(point)
            if replacement.num_liberties:
                self._replace_string(other_color_string.without_liberty(point))
            else:
                self._remove_string(other_color_string)

    def _replace_string(self, new_strings):
        for point in new_strings.stones:
            self._grid[point] = new_strings

    def _remove_string(self,string):
        for point in string.stones:
            for neighbor in point.neighbors():
                neighbor_string = self._grid.get(neighbor)
                if neighbor_string is None:
                    continue
                if neighbor_string is not string:
                    #neighbor_string.add_liberty(point)
                    self._replace_string(neighbor_string.with_liberty(point))       #여기 아직 정확히 이해 못함. _replace_string()의 역할이 정확히 무엇?
            self._grid[point] = None

            self._hash ^= zobrist.HASH_CODE[point, string.color]

    def is_on_grid(self, point):
        return 1<= point.row <= self.num_rows and \
            1 <= point.cols <= self.num_cols

    #바둑판 위의 점 내용을 반환한다. 만약 돌이 해당 점 위에 있으면 Player(color가 player를 의미)를 반환하고, 아니면 None을 반환한다.
    def get(self,point):
        string = self._grid.get(point)
        if string is None:
            return None
        return string.color

    #해당 점의 돌에 연결된 모든 이음(string)을 반환한다.
    def get_go_string(self,point):
        string = self._grid.get(point)
        if string is None:
            return None
        return string

    def zobrist_hash(self):         #여기도 다시 확인해보기기
       return self._hash

class Move():
    def __init__(self,point=None, is_pass=False, is_resign=False):
        assert(point is not None) ^ is_pass ^ is_resign
        self.point = point
        self.is_play = (self.point is not None)
        self.is_pass = is_pass
        self.is_resign = is_resign

        @classmethod
        def play(cls, point):
            return Move(point=point)

        @classmethod
        def pass_turn(cls):
            return Move(is_pass=True)

        @classmethod
        def resign(cls):
            return Move(is_resign=True)

class GameState():
    def __init__(self, board, next_player, previous, move):
        self.board = board
        self.next_player = next_player
        self.previous_state = previous
        if self.previous_state is None:                     # 여기도 아직 이해 못함...
            self.previous_states = frozenset()
        else:
            self.previous_states = frozenset(
                previous.previous_states |
                {(previous.next_player, previous.board.zobrist_hash())}
            )
        self.last_move = move

    def apply_move(self, move):
        if move.is_play:
            next_board = copy.deepcopy(self.board)
            next_board.place_stone(self.next_player, move.point)
        else:
            next_board = self.board
        return GameState(next_board, self.next_player.other, self, move)

    @classmethod
    def new_game(cls, board_size):
        if isinstance(board_size, int):
            board_size = (board_size, board_size)
        board = Board(*board_size)                  #이게 무슨 의미?
        return GameState(board, Player.black, None, None)

    def is_move_self_capture(self, player, move):
        if not move.is_play:
            return False
        next_board = copy.deepcopy(self.board)
        next_board.place_stone(player, move.point)
        new_string = next_board.get_go_string(move.point)
        return new_string.num_liberties == 0

    @property
    def situation(self):
        return(self.next_player, self.board)

    def does_move_violate_ko(self, player, move):
        if not move.is_play:
            return False
        next_board = copy.deepcopy(self.board)
        next_board.place_stone(player, move.point)
        next_situation = (player.other, next_board.zobrist_hash())
        return next_situation in self.previous_states
        '''
        past_state = self.previous_state
        while past_state is not None:
            if past_state.situation == next_situation:
                return True
            past_state = past_state.previous_state
        return False '''

    def is_valid_move(self, move):
        if self.is_over():                          # self.is_over가 아니라 self.is_over()인 이유는 무엇?
            return False
        if move.is_pass or move.is_resign:
            return True
        return (
            self.board.get(move.point) is None and
            not self.is_move_self_capture(self.next_player, move) and
            not self.does_move_violate_ko(self.next_player, move)
        )

    def is_over(self):
        if self.last_move is None:
            return False
        if self.last_move.is_resign:
            return True
        second_last_move = self.previous_state.last_move
        if second_last_move is None:
            return False
        return self.last_move.is_pass and second_last_move.is_pass #이것도 잘 이해안감

    def legal_moves(self):
        moves=[]
        for row in range(1,self.board.num_rows + 1):
            for col in range(1,self.board.num_cols + 1):
                move = Move.play(Point(row,col))
                if self.is_valid_move(move):
                    moves.append(move)

        moves.append(Move.pass_turn())
        moves.append(Move.resign())
        return moves

    def winner(self):
        if not self.is_over():
            return None
        if self.last_move.is_resign:
            return self.next_player
        game_result = compute_game_result(self)
        return game_result.winner

