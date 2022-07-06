import os
import re
import pydicom
import numpy as np
import matplotlib.pyplot as plt
#Import CT file(first CT file! - Superior side(head))
#check this stuff: ImagePositionPatient(use below formula!), 
#SliceThickness(maybe Z resolution), LargestPixelvalue-SmallestImagePixelValue(It is need when convert the Grayscale CT image to RGB)
#ImportantFormula: |해당축 기준좌표(CT의 첫번째 사진에 있음.)|/(해당 축 resolution) -> 넘파이로 변환하여 넣을 좌표에 더할값
#현재파일 : 
ctfolder_path = 'D:\CodeMaster\w7_dataset\P061_HN61_CT_2015-02-24_154354_RT^01.RT.Head.Neck.(Adult)_Head.&.Neck..3.0..B31s_n138__00001'
filename_list = []
fileidx = []
for top, dir, file in os.walk(ctfolder_path):
    k = -1
    for filename in file:
        
        if filename == 'metacache.mim':
            continue
        #print(filename)
        filename_list.append(filename)
        idxnum = re.findall(r'\d+', filename)[-1]
        fileidx.append(int(idxnum))

    break
#pic엔 dicom 데이터가 들어있음.



fileidx = np.array(fileidx)
fileorder = np.argsort(fileidx)
sorted_filename_list = []
for i in range(len(fileidx)):
    sorted_filename_list.append(filename_list[fileorder[i]])
    break
print(sorted_filename_list[0])
first_ct = pydicom.dcmread(ctfolder_path + '/'+sorted_filename_list[0])
#자동변환을 위해 - SIEMENS에서 찍은 CT 전용
if first_ct.Manufacturer == 'SIEMENS':
    scale_value = [float(first_ct.PixelSpacing[0]),
                   float(first_ct.PixelSpacing[1]),
                   float(first_ct.SliceThickness)]

    translation = [abs(first_ct.ImagePositionPatient[0])/first_ct.PixelSpacing[0], 
                   abs(first_ct.ImagePositionPatient[1])/first_ct.PixelSpacing[1], 
                   abs(first_ct.ImagePositionPatient[2])/first_ct.SliceThickness]

    
folder_path = 'D:\CodeMaster\w7_dataset\P061_HN61_RTst_2015-02-24_154354_RT^01.RT.Head.Neck.(Adult)_OAR61RE_n1__00000'
pic = []
for top, dir, file in os.walk(folder_path):
    for filename in file:
        if filename == 'metacache.mim':
            continue
        print(folder_path+'/'+filename)
        dcm = pydicom.dcmread(folder_path + '/' + filename, force=True)
        pic.append(dcm)

all_ctr = pic[0].ROIContourSequence #ROIContourSequence로 Contour 좌표 불러올 수 있음.
print(pic[0])
 #일단은 리스트로
#내분점 #좌표끼리 거리마다 weight 주는 방법

voxelnp = np.zeros((138, 512, 512, 3))
for ctrs in range(30):
    
    ctr_volume_coord = []
    ctr_coord_1dim = []
    coord_arr = []
    try:R, G, B = int(all_ctr[ctrs].ROIDisplayColor[0]),int(all_ctr[ctrs].ROIDisplayColor[1]),int(all_ctr[ctrs].ROIDisplayColor[2])
    except:break
    print(ctrs+1)
    for _slice in range(200):
        try:ctr_coord_1dim = all_ctr[ctrs].ContourSequence[_slice].ContourData #슬라이스 넘기면서 Contour좌표데이터 가져옴
        except:break
        
        #ctr_color = all_ctr[0].ROIDisplayColor #색깔 불러오기
        coord_arr = np.zeros((1, 3)) #미리 슬라이스의 좌표를 추가 할 array 만들어 놓고

        for idx in range(0, len(ctr_coord_1dim), 3): #1차원적 데이터인 ContourData를 3차원으로(데이터는 3의 배수이므로 다음과같이)
            ##################|해당축 기준좌표|/(해당 축 resolution) -> 넘파이에 넣을 좌표에 더할값##########################
            #현재 점 추가. x y z 순서
            coord_arr = np.append(coord_arr, 
            [[(round(ctr_coord_1dim[idx]/scale_value[0]+translation[0])), (round(ctr_coord_1dim[idx+1]/scale_value[1]+translation[1])), (round(ctr_coord_1dim[idx+2]/scale_value[2]+translation[2]))]],
            axis = 0) #voxel화를 위한 것이므로 coord_arr에 추가할 땐 int, (그냥 int하면 내림이 되므로 round 적용시켜서.)
            #np.append를 사용할 땐, append 한 거를 다시 자신에게 초기화 해줘야하고 2차원으로 추가할 땐 [[내용]]이런식으로, 추가할 차원에 맞게 괄호를 열어줘야.

            #현재 인덱스 - x, y, z좌표 
            xi, yi, zi = float(ctr_coord_1dim[idx]/scale_value[0]+translation[0]), float(ctr_coord_1dim[idx+1]/scale_value[1]+translation[1]), float(ctr_coord_1dim[idx+2]/scale_value[2]+translation[2])

            #다음 인덱스 - 위의 인덱스에서 3씩 추가한 값
            ##################|기준좌표|/resolution -> 넘파이에 넣을 좌표에 더할값##########################
            try:xiplus, yiplus, ziplus = float(ctr_coord_1dim[idx+3]/scale_value[0]+translation[0]), float(ctr_coord_1dim[idx+4]/scale_value[1]+translation[1]), float(ctr_coord_1dim[idx+5]/scale_value[2]+translation[2]) 
            #####예외, xi, yi, zi가 마지막 일경우, 그냥 pass하면 안되고 첫번째 점과 연결을 시켜주어야함.#####
            except: xiplus, yiplus, ziplus = float(ctr_coord_1dim[0]/scale_value[0]+translation[0]), float(ctr_coord_1dim[1]/scale_value[1]+translation[1]), float(ctr_coord_1dim[2]/scale_value[2]+translation[2])

            #내분 계수, 70이상으로 잡을 시 채우는 점/ 걸리는 시간의 비율이 매우매우낮아진다. 5이상 70이하가 유효하게 쓸만한 범위.
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

    #voxelnp값에 하나하나씩 지정.
    #voxelnp = np.zeros((150, 512, 512, 3)) #(z, y, x)순서, 150, 512, 512 복셀화.(3은 유색화)

    for idx, _slice in enumerate(ctr_volume_coord):
        for point_idx in range(len(_slice)):
            
            try:voxelnp[round(_slice[point_idx][2])][round(_slice[point_idx][1])][round(_slice[point_idx][0])] = \
                np.array([R, G, B])
                ##################|기준좌표|/resolution -> 넘파이에 넣을 좌표에 더할값##########################  
            except:break

#데이터타입 이렇게해야 용량 많이줄어듦
voxelnp = voxelnp.astype('uint8')

np.save('D:\CodeMaster\w7voxels\p061rtst\p061voxel_ctr', voxelnp)

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
    axes.append(fig.add_subplot(9, 12, idx+1)) #바깥루프의 축길이가 얼마나 되는지 고려해서
    subplot_title=("slice"+str(idx+1))
    axes[-1].set_title(subplot_title)
    plt.imshow(voxelnp[int(image)]) 

plt.show()