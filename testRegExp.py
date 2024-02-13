import re

var = "('192.168.127.246', 57193)"
patern = r'\s(\d*)'
match = re.search(patern, var)
print(match[0].replace(' ', ''))
