myfamily = {
  0: {
    "name": ['a', 'b'],
    "year": 2004
  },
  1: {
    "name": ['a', 'c'],
    "year": 2007
  },
  2: {
    "name": ['c', 'b'],
    "year": 2011
  }
}

print('items: ', myfamily.items())

print('value: ', myfamily.values())

for x in myfamily.values():
    print(x['name'])

secondfamily = {}

secondfamily[0] = myfamily[0]
print(secondfamily)


size = 6
distances = [float('inf')] * size
prev = [None] * size

print(distances)
print(type(distances))
