from threading import Thread
import global_test_a
import time
from global_test_a import a

def print_from_a():
	global a
	print(a)

if __name__ == '__main__':
	t1 = Thread(target=global_test_a.increment_a)
	t1.start()
	while True:
		from global_test_a import a #This is key. Otherwise the variable doesn't update.
		print_from_a()
		time.sleep(1)
