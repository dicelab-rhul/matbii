fun = lambda data_state: 2 * (1 - data_state // 2)

for i in range(0, 3):
    print(i, fun(i))
