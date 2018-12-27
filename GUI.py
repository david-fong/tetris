import random


class Test2:
    n: int

    def __init__(self):
        self.n = 1


class Test1:
    test2 = Test2()
    test2.n += 1
    print(test2.n)

