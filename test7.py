
from datetime import datetime
sgf_directory = 'C:/Users/User/PycharmProjects/dlgo/httpfrontend/sgf'

now = datetime.now()
curruent_time = now.strftime("%y.%m.%d-%H")

file = open(sgf_directory + '/'+ curruent_time, 'r')
content=file.read()
print(content)