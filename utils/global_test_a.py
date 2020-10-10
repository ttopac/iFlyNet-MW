import time

a = 5

def increment_a():
	global a
	while True:
		a = a + 1
		print (a)
		time.sleep(1)


if __name__ == '__main__':
	increment_a()
	print (a)