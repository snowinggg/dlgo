from dlgo.agent.naive import RandomBot
from dlgo.httpfrontend.server import get_web_app
'''
random_agent = RandomBot()
web_app = get_web_app({'random':random_agent})
web_app.run()


if __name__ == '__main__':
    random_agent = RandomBot()
    web_app = get_web_app(random_agent)
    web_app.run()

'''
import keras

print(keras.__version__)

