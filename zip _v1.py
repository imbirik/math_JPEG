# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import numpy as np

#начало считывания
from PIL import Image
print("Enter filename...")
filename = input()
with Image.open(filename+'.bmp') as image:
    arr = np.array(image, 'float')
    w,h,nth = np.shape(arr)
#конец считывания
    
#начало перехода к YCbCr

for row in range(0, h):
    for col in range(0, w):
        r = arr[col][row][0]
        g = arr[col][row][1]
        b = arr[col][row][2]
        arr[col][row][0] = max(0,min(255,0.299*r+0.587*g+0.114*b))
        arr[col][row][1] = max(0,min(255,-0.169*r-0.331*g+0.5*b+128))
        arr[col][row][2] = max(0,min(255,0.5*r-0.419*g-0.081*b+128))
#конец перехода к YCbCr

#начало сжатия Cb и Cr
for j in range(0, h-2,2):
   for i in range(0, w-2,2):
       avg_cb = (arr[i][j][1]+arr[i+1][j][1]+arr[i][j+1][1]+arr[i+1][j+1][1])/4
       avg_cr = (arr[i][j][2]+arr[i+1][j][2]+arr[i][j+1][2]+arr[i+1][j+1][2])/4
       arr[i//2][j//2][1] = avg_cb
       arr[i//2][j//2][2] = avg_cr

h //=2
w //=2
w = (w//8)*8
h = (h//8)*8
#конец сжатия Cb и Cr

#начало преобразования Фурье
arr_dfp = np.empty((w,h,3))
dfp = np.zeros((8,8))
def C(i, j):
    a = 0.5*np.cos((2*j+1)*i*np.pi/16);
    if i == 0 :
        return a/np.sqrt(2)
    return a
for i in range(0,8):
    for u in range(0,8):
        dfp[i][u] = C(i,u)
for row in range(0, h-7,8):
    for col in range(0,w-7,8):
        for i in range (0,8):
            for j in range(0,8):
                dcp_cb = 0
                dcp_cr = 0
                for k in range(0,8):
                    dcp_cb += dfp[i][k]*arr[k+col][j+row][1]
                    dcp_cr += dfp[i][k]*arr[k+col][j+row][2]
                arr_dfp[i+col][j+row][1] = dcp_cb
                arr_dfp[i+col][j+row][2] = dcp_cr
for row in range(0, h,8):
    for col in range(0,w,8):
        for i in range (0,8):
            for j in range(0,8):
                dcp_cb = 0
                dcp_cr = 0
                for k in range(0,8):
                    dcp_cb += arr_dfp[i+col][k+row][1]*dfp[j][k]
                    dcp_cr += arr_dfp[i+col][k+row][2]*dfp[j][k]
                arr[i+col][j+row][1] = dcp_cb
                arr[i+col][j+row][2] = dcp_cr
#конец преобразования Фурье

#начало квантования
Q = np.array(((16, 11, 10, 16, 24, 40, 51, 61),
(12, 12, 14, 19, 26, 58, 60, 55),
(14, 13, 16, 24, 40, 57, 69, 56),
(14, 17, 22, 29, 51, 87, 80, 62),
(18, 22, 37, 56, 68, 109, 103, 77),
(24, 35, 55, 64, 81, 104, 113, 92),
(49, 64, 78, 87, 103, 121, 120, 101),
(72, 92, 95, 98, 112, 100, 103, 99)))

for row in range(0, h,8):
    for col in range(0,w,8):
        for u in range (0,8):
            for v in range(0,8):
                arr[u+col][v+row][1] /= Q[u][v]
                arr[u+col][v+row][2] /= Q[u][v]
#конец квантования

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
#конец обхода зигзагом
        
#начало кодировки 
arr = np.array(arr,'int')
ans_1 = []
ans_2 = []
for row in range(0, w//8):
    ans_1.append([])
    ans_2.append([])
    for col in range(0,h//8):
        ans_1[row].append([])
        ans_2[row].append([])
        sh_1 = 0
        sh_2 = 0
        for i in range(64):
            if arr[row*8+les[i][0]][col*8+les[i][1]][1] == 0:
                sh_1 += 1
            else:
               ans_1[row][col].append(sh_1)
               ans_1[row][col].append(arr[row*8+les[i][0]][col*8+les[i][1]][1])
               sh_1 = 0
        for i in range(64):
            if arr[row*8+les[i][0]][col*8+les[i][1]][2] == 0:
                sh_2 += 1
            else:
               ans_2[row][col].append(sh_2)
               ans_2[row][col].append(arr[row*8+les[i][0]][col*8+les[i][1]][2])
               sh_2 = 0
        ans_1[row][col].append(sh_1)
        ans_2[row][col].append(sh_2)
#конец кодировки

#начало вывода
import struct
print("save as...")
filename = input()
with open(filename+'.dat', 'wb') as f:
    def pr_B(x):
        f.write(struct.pack('B',x))
    def pr_h(x):
        f.write(struct.pack('h',x))
    pr_h(h)
    pr_h(w)
    for i in range(w//8):
        for j in range(h//8):
            pr_B(len(ans_1[i][j]))
            for elem in ans_1[i][j]:
                pr_B(elem + 128)
    for i in range(w//8):
        for j in range(h//8):
            pr_B(len(ans_2[i][j]))
            for elem in ans_2[i][j]:
                pr_B(elem + 128)
    for i in range(2*w):
        for j in range(2*h):
            pr_B(arr[i][j][0])
f.close()
#конец вывода