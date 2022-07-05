import os
import pydicom
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
folder_path = 'D:\CodeMaster\w7_dataset\P001_HN1_RTst_2018-11-01_102652_RT^01.RT.Head.Neck.(Adult)_re_n1__00000'
pic = []
for top, dir, file in os.walk(folder_path):
    for filename in file:
        if filename == 'metacache.mim':
            continue
        print(folder_path+'/'+filename)
        dcm = pydicom.dcmread(folder_path + '/' + filename, force=True)
        pic.append(dcm)

all_ctr = pic[0].ROIContourSequence #ROIContourSequence로 Contour 좌표 불러올 수 있음.

ctr_volume_coord = [] #일단은 리스트로
#내분점 #좌표끼리 거리마다 weight 주는 방법
for ctrs in range(24):
    ctr_coord_1dim = []
    coord_arr = []
    R = int(all_ctr[ctrs].ROIDisplayColor[0])
    G = int(all_ctr[ctrs].ROIDisplayColor[1])
    B = int(all_ctr[ctrs].ROIDisplayColor[2])
    for _slice in range(200):
        try:ctr_coord_1dim = all_ctr[ctrs].ContourSequence[_slice].ContourData #슬라이스 넘기면서 Contour좌표데이터 가져옴
        except:break
        
        #ctr_color = all_ctr[0].ROIDisplayColor #색깔 불러오기
        coord_arr = np.zeros((1, 3)) #미리 슬라이스의 좌표를 추가 할 array 만들어 놓고

        for idx in range(0, len(ctr_coord_1dim), 3): #1차원적 데이터인 ContourData를 3차원으로(데이터는 3의 배수이므로 다음과같이)

            #현재 점 추가. x y z 순서
            coord_arr = np.append(coord_arr, 
            [[(round(ctr_coord_1dim[idx]/0.9766+255.49017)), (round(ctr_coord_1dim[idx+1]/0.9766+468.473991)), (round(ctr_coord_1dim[idx+2]/3+169.3333))]],
            axis = 0) #voxel화를 위한 것이므로 coord_arr에 추가할 땐 int, (그냥 int하면 내림이 되므로 round 적용시켜서.)
            #np.append를 사용할 땐, append 한 거를 다시 자신에게 초기화 해줘야하고 2차원으로 추가할 땐 [[내용]]이런식으로, 추가할 차원에 맞게 괄호를 열어줘야.

            #현재 인덱스 - x, y, z좌표 
            xi, yi, zi = float(ctr_coord_1dim[idx]/0.9766+255.49017), float(ctr_coord_1dim[idx+1]/0.9766+468.473991), float(ctr_coord_1dim[idx+2]/3+169.3333)

            #다음 인덱스 - 위의 인덱스에서 3씩 추가한 값
            try:xiplus, yiplus, ziplus = float(ctr_coord_1dim[idx+3]/0.9766+255.49017), float(ctr_coord_1dim[idx+4]/0.9766+468.473991), float(ctr_coord_1dim[idx+5]/3+169.3333) 
            #####예외, xi, yi, zi가 마지막 일경우, 그냥 pass하면 안되고 첫번째 점과 연결을 시켜주어야함.#####
            except: xiplus, yiplus, ziplus = float(ctr_coord_1dim[0]/0.9766+255.49017), float(ctr_coord_1dim[1]/0.9766+468.473991), float(ctr_coord_1dim[2]/3+169.3333)

            #내분 계수, 70이상으로 잡을 시 채우는 점/ 걸리는 시간의 비율이 매우매우낮아진다. 5이상 70이하가 유효하게 쓸만한 범위.
            #9에서 왜끊기지? 
            indiv_coeff = 30
            largedist = ((xi - xiplus)**2 + (yi - yiplus)**2 + (zi - ziplus)**2) ** 0.5
            if largedist < 1: #만약 길이 차이가 적게나서 1보다 작을 때 largedist를 기본 내분 갯수에 곱하면 내분 갯수가 기본보다 작아짐.
                largedist = 1 #따라서 길이 차이가 적다면 largedist를 1로.
            indiv = round(indiv_coeff * largedist) #largedist에 따라 weight가 달라짐(largedist가 크면(다음 점과의 떨어진 거리가 길다면) 내분도 많이함)

            #내분점을 추가. 다음 점은 다음 반복에서 추가할 것이므로 추가할 필요없음.
            for jdx in range(1, indiv):
                coord_arr = np.append(coord_arr, 
                [[(round((((indiv-1-jdx)*xi +(jdx+1)*xiplus)/indiv))), 
                (round((((indiv-1-jdx)*yi +(jdx+1)*yiplus)/indiv))), 
                (round((((indiv-1-jdx)*zi +(jdx+1)*ziplus)/indiv)))]],
                axis = 0)

        coord_arr = np.delete(coord_arr, 0, axis = 0) #zeros로 coord_arr의 head에 더미를 만들었으니, 맨앞은 0, 0, 0이라 삭제해주어야함.
        coord_arr = np.unique(coord_arr, axis = 0) #float 계산에 round롤 하므로 겹치는 점을 삭제.
        ctr_volume_coord.append(coord_arr) #ctr_volume_coord에 좌표 정보가 정리된 2차원 array를 추가함.
    print(len(ctr_volume_coord))

    #voxelnp값에 하나하나씩 지정.
    voxelnp = np.zeros((150, 512, 512, 3)) #(z, y, x)순서, 150, 512, 512 복셀화.(3은 유색화)

     #contour출력을 위해 zcoord 만들어 놓기

    #넘파이 array는 양의 정수로 인덱싱해야하므로 좌표 변환이 필요.

    for idx, _slice in enumerate(ctr_volume_coord):
        for point_idx in range(len(_slice)):
            try:voxelnp[round(_slice[point_idx][2])+1][round(_slice[point_idx][1])][round(_slice[point_idx][0])] = \
                np.array([R/255, G/255, B/255])
                ##################|기준좌표|/resolution -> 넘파이에 넣을 좌표에 더할값##########################  
            except:break


    np.save('D:\CodeMaster\w7voxels\p001rtst_1\p001voxel%d' %(ctrs+1), voxelnp)

#만든 voxel로 슬라이스마다 contour 출력
output = 0
if output == 0:
    quit()
zc = np.where(voxelnp != 0) #Data 형이 뭔지 고려해주고
zcoord = []
for i in range(len(zc[0])):
    zcoord.append(int(zc[0][i]))
zcoord = list(set(zcoord))

print(voxelnp.shape)
axes = [] 
fig = plt.figure(figsize = (17, 17))
for idx, image in enumerate(zcoord):
    axes.append(fig.add_subplot(6, 8, idx+1)) #바깥루프의 축길이가 얼마나 되는지 고려해서
    subplot_title=("slice"+str(idx+1))
    axes[-1].set_title(subplot_title)
    plt.imshow(voxelnp[int(image)]) 

plt.show()