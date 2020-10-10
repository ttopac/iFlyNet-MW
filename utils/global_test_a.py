import time

a = 5

def increment_a():
	global a
	while True:
		a = a + 1
		print (a)
		time.sleep(1)