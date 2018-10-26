# -*- coding: utf-8 -*-

import numpy as np

#начало считывания
import struct
print("enter filename...")
filename = input()
f = open(filename+'.dat', 'rb')
data = f.read()
tmp = 0
def rd_B():
    global tmp
    tmp+=1
    return struct.unpack('B',data[tmp-1:tmp])[0]
def rd_h():
    global tmp
    tmp+=2
    return struct.unpack('h',data[tmp-2:tmp])[0]
    
h = rd_h()
w = rd_h()
ans_1 = []
for i in range(w//8):
    ans_1.append([])
    for j in range(h//8):
        ans_1[i].append([])
        z = rd_B()
        for elem in range(z):
            ans_1[i][j].append(rd_B()-128)
ans_2 = []
for i in range(w//8):
    ans_2.append([])
    for j in range(h//8):
        ans_2[i].append([])
        z = rd_B()
        for elem in range(z):
            ans_2[i][j].append(rd_B()-128)
arr_Y = np.empty((2*w,2*h))
for i in range(2*w):
    for j in range(2*h):
        arr_Y[i][j] = rd_B()
f.close()
#конец считывания

#начало обхода зигзагом
les = np.empty((64,2), dtype = 'int')
les[0] = (0,0)
tmp = 1
for i in range(1,8):
    for j in range(0,i+1):
        if i % 2 == 0:
            les[tmp][0] = j
            les[tmp][1] = i-j
        else:
            les[tmp][0] = i-j
            les[tmp][1] = j
        tmp+=1
for i in range(8,15):
    for j in range(i-7,8):
        if i % 2 == 0:
            les[tmp][0] = j 
            les[tmp][1] = i-j
        else:
            les[tmp][0] = i-j 
            les[tmp][1] = j
        tmp+=1
#конец обхода

#начало декодирования
arr = np.empty((w,h,3),dtype = 'int') 
tmp = 0
for row in range(0,w//8):
    for col in range(0,h//8):
       sh = 0
       for k in range(0,len(ans_1[row][col])-1,2):
           x = ans_1[row][col][k]
           y = ans_1[row][col][k+1]
           for l in range(x):
               arr[row*8+les[sh][0]][col*8+les[sh][1]][1] = 0
               sh+=1
           arr[row*8+les[sh][0]][col*8+les[sh][1]][1] = y
           sh+=1
       for k in range(0,ans_1[row][col][-1]):
            arr[row*8+les[sh][0]][col*8+les[sh][1]][1] = 0
            sh+=1

for row in range(w//8):
    for col in range(h//8):
       sh = 0
       for k in range(0,len(ans_2[row][col])-1,2):
           x = ans_2[row][col][k]
           y = ans_2[row][col][k+1]
           for l in range(x):
               arr[row*8+les[sh][0]][col*8+les[sh][1]][2] = 0
               sh+=1
           arr[row*8+les[sh][0]][col*8+les[sh][1]][2] = y
           sh+=1
       for k in range(0,ans_2[row][col][-1]):
            arr[row*8+les[sh][0]][col*8+les[sh][1]][2] = 0
            sh+=1
#конец декодирования
            
#начало квантования
Q = np.array(((16, 11, 10, 16, 24, 40, 51, 61),
(12, 12, 14, 19, 26, 58, 60, 55),
(14, 13, 16, 24, 40, 57, 69, 56),
(14, 17, 22, 29, 51, 87, 80, 62),
(18, 22, 37, 56, 68, 109, 103, 77),
(24, 35, 55, 64, 81, 104, 113, 92),
(49, 64, 78, 87, 103, 121, 120, 101),
(72, 92, 95, 98, 112, 100, 103, 99)))

for row in range(0, h-7,8):
    for col in range(0,w-7,8):
        for u in range (0,8):
            for v in range(0,8):
                arr[u+col][v+row][1] *= Q[u][v]
                arr[u+col][v+row][2] *= Q[u][v]
#конец квантования

#начало преобразования Фурье                
dfp = np.zeros((8,8))
def C(i, j):
    a = 0.5*np.cos((2*j+1)*i*np.pi/16);
    if i == 0 :
        return a/np.sqrt(2)
    return a
for i in range(0,8):
    for u in range(0,8):
        dfp[i][u] = C(i,u)

arr_res = arr.copy()
for row in range(0, h-7,8):
    for col in range(0,w-7,8):
        for i in range (0,8):
            for j in range(0,8):
                dcp_cb = 0
                dcp_cr = 0
                for k in range(0,8):
                    dcp_cb += dfp[k][i]*arr[k+col][j+row][1]
                    dcp_cr += dfp[k][i]*arr[k+col][j+row][2]
                arr_res[i+col][j+row][1] = dcp_cb
                arr_res[i+col][j+row][2] = dcp_cr
for row in range(0, h-7,8):
    for col in range(0,w-7,8):
        for i in range (0,8):
            for j in range(0,8):
                dcp_cb = 0
                dcp_cr = 0
                for k in range(0,8):
                    dcp_cb += arr_res[i+col][k+row][1]*dfp[k][j]
                    dcp_cr += arr_res[i+col][k+row][2]*dfp[k][j]
                arr[i+col][j+row][1] = dcp_cb
                arr[i+col][j+row][2] = dcp_cr
#конец преобразования Фурье

#начало востановаления YCbCr
w = 2*w
h = 2*h
arr_big = np.empty((w,h,3))
for i in range(w//2):
    for j in range(h//2):
        arr_big[2*i][2*j][1] = arr_big[2*i+1][2*j][1] = arr_big[2*i][2*j+1][1] = arr_big[2*i+1][2*j+1][1] = arr[i][j][1]
        arr_big[2*i][2*j][2] = arr_big[2*i+1][2*j][2] = arr_big[2*i][2*j+1][2] = arr_big[2*i+1][2*j+1][2] = arr[i][j][2]
for i in range(w):
    for j in range(h):
        arr_big[i][j][0] = arr_Y[i][j]

arr = arr_big
#конец востановаления YCbCr

#Начало перехода к RGB
for col in range(0, w):
    for row in range(0, h):
        y = arr[col][row][0]
        cb = arr[col][row][1]-128
        cr = arr[col][row][2]-128
        arr[col][row][0] = min(255,max(0,y+1.402*cr))
        arr[col][row][1] = min(255,max(0,y-0.344*cb-0.714*cr))
        arr[col][row][2] = min(255,max(0,y+1.72*cb))
#конец перехода к RGB

#начало вывода
from PIL import Image
arr = np.array(arr, 'byte')
result = Image.fromarray(arr,'RGB')
print("save as..")
filename = input()
result.save(filename+'.bmp')
#конец вывода