import os
import h5py
from flask import Flask, render_template
from flask import jsonify
from flask import request

from dlgo import agent
from dlgo import goboard_fast as goboard
from dlgo.utils import coords_from_point
from dlgo.utils import point_from_coords
from dlgo.gosgf import Sgf_game
from dlgo.gotypes import Point
from dlgo import gotypes
from agent.naive import RandomBot
from agent.predict import DeepLearningAgent, load_prediction_agent
from datetime import datetime
from gosgf.sgf import SGFWriter


from bson.objectid import ObjectId
import base64
import datetime as dt
import jwt
import hashlib
import json
from pymongo import MongoClient

from flask import session, redirect, url_for

SECRET_KEY = 'SSANGLIB'
client = MongoClient('localhost', 27017)
db = client.ssanglib


from werkzeug.utils import secure_filename
cols = 'abcdefghjklmnopqrst'

__all__ = [
    'get_web_app',
]
def sgf_from_point(point):
    return '%s%s' % (
        cols[point.col - 1],
        cols[point.row - 1]
    )

def get_web_app(bot_map):

    here = os.path.dirname(__file__)
    static_path = os.path.join(here, 'static')
    app = Flask(__name__, static_folder=static_path, static_url_path='/static')



    @app.route('/')
    def home():
        token_receive = request.cookies.get('mytoken')
        try:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
            return redirect("go_home")
        except jwt.ExpiredSignatureError:
            return redirect(url_for("login", token_expired="로그인 시간이 만료되었습니다."))
        except jwt.exceptions.DecodeError:
            return redirect(url_for("login"))

    @app.route('/go_home', methods=['GET', 'POST'])
    def go_home():
        return render_template('home.html')

    @app.route('/login')
    def login():
        token_expired = request.args.get("token_expired")
        return render_template('login.html', token_expired=token_expired)

    @app.route('/api/login', methods=['POST'])
    def api_login():
        id_receive = request.form['id_give']
        pw_receive = request.form['pw_give']

        pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()
        result = db.user.find_one({'id': id_receive, 'pw': pw_hash})

        if result is not None:
            payload = {
                'id': id_receive,
                'exp': dt.datetime.utcnow() + dt.timedelta(minutes=30)
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

            return jsonify({'result': 'success', 'token': token})
        else:
            return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})

    @app.route('/sign-up')
    def register():
        return render_template('sign-up.html')

    @app.route('/api/sign-up', methods=['POST'])
    def api_sign_up():
        id_receive = request.form['id_give']
        pw_receive = request.form['pw_give']
        pwConfirm_receive = request.form['pwConfirm_give']

        check_duplicate_user = db.user.find_one({'id': id_receive})

        if check_duplicate_user is not None:
            if check_duplicate_user['id'] == id_receive:
                return jsonify({'result': 'fail', 'msg': '중복된 아이디가 존재합니다.'})

        if pw_receive != pwConfirm_receive:
            return jsonify({'result': 'fail', 'msg': '비밀번호가 서로 일치하지 않습니다.'})

        pw_hash = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()

        db.user.insert_one({'id': id_receive, 'pw': pw_hash, })

        result = db.user.find_one({'id': id_receive, 'pw': pw_hash})

        if result is not None:
            payload = {
                'id': id_receive,
                'exp': dt.datetime.utcnow() + dt.timedelta(minutes=30)
            }
            token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
            return jsonify({'result': 'success', 'token': token})
        else:
            return jsonify({'result': 'fail', 'msg': '예기치 못한 오류가 발생하였습니다.'})

    @app.route('/select-move/<bot_name>', methods=['POST'])
    def select_move(bot_name):
        content = request.json
        board_size = content['board_size']
        game_state = goboard.GameState.new_game(board_size)
        # Replay the game up to this point.
        sgf_directory = 'C:/Users/User/PycharmProjects/dlgo/httpfrontend/sgf'
        for move in content['moves']:
            if move == 'pass':
                next_move = goboard.Move.pass_turn()
            elif move == 'resign':
                next_move = goboard.Move.resign()
            else:
                next_move = goboard.Move.play(point_from_coords(move))
                now = datetime.now()
                curruent_time = now.strftime("%y.%m.%d-%H")
                if not os.path.isfile(sgf_directory + '/'+ curruent_time):
                    file = open(sgf_directory + '/'+ curruent_time, 'w')
                    file.write(';GM[1]FF[4]SZ[9];'+'B['+sgf_from_point(point_from_coords(move))+'];')
                    file.close()
                else:
                    file = open(sgf_directory + '/'+ curruent_time, 'a')
                    file.write('B['+sgf_from_point(point_from_coords(move))+'];')
                    file.close()
            game_state = game_state.apply_move(next_move)

        bot_agent = bot_map[bot_name]
        bot_move = bot_agent.select_move(game_state)
        if bot_move.is_pass:
            bot_move_str = 'pass'
        elif bot_move.is_resign:
            bot_move_str = 'resign'
        else:
            bot_move_str = coords_from_point(bot_move.point)
            file = open(sgf_directory + '/'+ curruent_time, 'a')
            file.write('W['+sgf_from_point(bot_move.point)+'];')
            file.close()
        return jsonify({
            'bot_move': bot_move_str,
            'diagnostics': bot_agent.diagnostics()
        })

    @app.route('/read-record/<file_name>', methods=['POST'])
    def read_record(file_name):
        sgf_directory = 'C:/Users/User/PycharmProjects/dlgo/httpfrontend/sgf'
        file = open(sgf_directory+'/'+file_name, 'r')
        content = file.read()
        sgf_game=Sgf_game.from_string(content)
        count = 0

        for item in sgf_game.main_sequence_iter():
            color, move_tuple = item.get_move()
            if color is not None and move_tuple is not None:
                row, col = move_tuple
                point = Point(row + 1, col + 1)
                move = goboard.Move.play(point)
            if count==1:
                if not os.path.isfile(sgf_directory + '/'+ file_name + '-read'):
                    file = open(sgf_directory + '/'+ file_name + '-read', 'w')
                    file.write(';GM[1]FF[4]SZ[9];'+'B['+sgf_from_point(point)+'];')
                    file.close()
            else:
                if not os.path.isfile(sgf_directory + '/' + file_name + '-read'):
                    file = open(sgf_directory + '/' + file_name + '-read', 'a')
                    file.write(';' + item + ';')
                    file.close()
            count+=1
        if os.path.isfile(sgf_directory + '/'+ file_name + '-read'):
            os.remove(sgf_directory + '/'+ file_name + '-read')

        board_size = content['board_size']
        game_state = goboard.GameState.new_game(board_size)
        # Replay the game up to this point.
        for move in content['moves']:
            if move == 'pass':
                next_move = goboard.Move.pass_turn()
            elif move == 'resign':
                next_move = goboard.Move.resign()
            else:
                next_move = goboard.Move.play(point_from_coords(move))
            game_state = game_state.apply_move(next_move)
        bot_agent = bot_map[bot_name]
        bot_move = bot_agent.select_move(game_state)
        if bot_move.is_pass:
            bot_move_str = 'pass'
        elif bot_move.is_resign:
            bot_move_str = 'resign'
        else:
            bot_move_str = coords_from_point(bot_move.point)
        return jsonify({
            'bot_move': bot_move_str,
            'diagnostics': bot_agent.diagnostics()
        })



    @app.route('/read-record/list')
    def list_page():
        file_lists = os.listdir('C:/Users/User/PycharmProjects/dlgo/httpfrontend/sgf')
        html = """<center><a href="/">홈페이지</a><br><br>"""
        for file_list in file_lists:

            html += """<a href="/read-record/{file_list}>">""" + file_list + "</a><br><br>"""
        html += "</center>"
        return html

    @app.route('/api/reviews', methods=['POST'])
    def save_reviews():
        title = request.form['title_give']
        content = request.form['content_give']
        file = request.files["file_give"]

        token_receive = request.cookies.get('mytoken')
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.user.find_one({"id": payload['id']})

        extension = file.filename.split('.')[-1]

        today = datetime.now()
        mytime = today.strftime('%Y-%m-%d-%H-%M-%S')

        filename = f'file-{mytime}'

        save_to = f'static/img/{filename}.{extension}'

        file.save(save_to)

        doc = {
            'review_title': title,
            'review_content': content,
            'review_file': f'{filename}.{extension}',
            'review_create_date': today.strftime('%Y.%m.%d.%H.%M.%S'),
            'author': user_info['id']

        }

        db.reviews.insert_one(doc)
        return jsonify({'msg': '등록 완료!'})

    return app

if __name__ == '__main__':
    random_agent=RandomBot()

    web_app = get_web_app({'random':random_agent})
    web_app.run(host='0.0.0.0',debug=True)

