

def func(n):
    list=[]
    for j in range(2, n+1):
        for i in range(2, j):
            if j % i == 0:
                break
            if i == j-1:
                list.append(j)
    print(list)

func(100)

