import os
import re
import pydicom
import numpy as np
from collections import deque
#Import CT file(first CT file! - Superior side(head))
#check this stuff: ImagePositionPatient(use below formula!), 
#SliceThickness(maybe Z resolution), LargestPixelvalue-SmallestImagePixelValue(It is need when convert the Grayscale CT image to RGB)
#ImportantFormula: |해당축 기준좌표(CT의 첫번째 사진에 있음.)|/(해당 축 resolution) -> 넘파이로 변환하여 넣을 좌표에 더할값
#현재파일 : 
basepath = 'D:\CodeMaster\w7_dataset'
CT_folder_path = basepath+'\P041_HN41_CT_2019-03-11_202004_RT^01.RT.Head.Neck.(Adult)_Head.&.Neck..3.0..B31s_n160__00001'
RTst_folder_path = basepath + '\P041_HN41_RTst_2019-03-11_202004_RT^01.RT.Head.Neck.(Adult)_RE_n1__00001'
convertcolor = 65535/255
######################################import CT info############################################
filename_list = []
fileidx = []
for top, dir, file in os.walk(CT_folder_path):
    for filename in file:
        if filename[-3:] != 'dcm':
            continue
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

print(sorted_filename_list[0])
first_ct = pydicom.dcmread(CT_folder_path + '/'+sorted_filename_list[0])
#좌표변환의 기준이 되는건 항상 '발쪽방향에서 첫번째 사진'
#자동변환을 위해

#standard: SIEMENS
scale_value = [float(first_ct.PixelSpacing[0]),
               float(first_ct.PixelSpacing[1]),
               float(first_ct.SliceThickness)]

translation = [abs(first_ct.ImagePositionPatient[0])/first_ct.PixelSpacing[0], 
               abs(first_ct.ImagePositionPatient[1])/first_ct.PixelSpacing[1], 
               abs(first_ct.ImagePositionPatient[2])/first_ct.SliceThickness]

if first_ct.Manufacturer == 'TOSHIBA': #TOSHIBA일 경우 좌표 보정(사진순서가 다름)
    translation[2] -= 1
###############################end of import CT info#################################

###############################import RTst info######################################
pic = []
for top, dir, file in os.walk(RTst_folder_path):
    for filename in file:
        if filename[-3:] != 'dcm':
            continue
        print(RTst_folder_path +'/'+filename)
        dcm = pydicom.dcmread(RTst_folder_path + '/' + filename, force=True)
        pic.append(dcm)

all_ctr = pic[0].ROIContourSequence #ROIContourSequence로 Contour 좌표 불러올 수 있음.

 #일단은 리스트로
#내분점 #좌표끼리 거리마다 weight 주는 방법
zsize = len(filename_list)
voxelnp = np.zeros((zsize, 512, 512, 3))
print('connecting pixel...')
for ctrs in range(len(all_ctr)):


    #########################function############################
    ctr_volume_coord = []
    ctr_coord_1dim = []
    coord_arr = []
    print(ctrs+1)
    R, G, B = int(all_ctr[ctrs].ROIDisplayColor[0]),int(all_ctr[ctrs].ROIDisplayColor[1]),int(all_ctr[ctrs].ROIDisplayColor[2])
    for _slice in range(len(all_ctr[ctrs].ContourSequence)):
        ctr_coord_1dim = all_ctr[ctrs].ContourSequence[_slice].ContourData #슬라이스 넘기면서 Contour좌표데이터 가져옴
        coord_arr = np.zeros((1, 3)) #미리 슬라이스의 좌표를 추가 할 array 만들어 놓고

        for idx in range(0, len(ctr_coord_1dim), 3): #1차원적 데이터인 ContourData를 3차원으로(데이터는 3의 배수이므로 다음과같이)
            ##################|해당축 기준좌표|/(해당 축 resolution) -> 넘파이에 넣을 좌표에 더할값####################
            coord_arr = np.append(coord_arr, 
            [[(round(ctr_coord_1dim[idx]/scale_value[0]+translation[0])), 
            (round(ctr_coord_1dim[idx+1]/scale_value[1]+translation[1])), 
            (round(ctr_coord_1dim[idx+2]/scale_value[2]+translation[2]))]],
            axis = 0) 
    

        coord_arr = np.delete(coord_arr, 0, axis = 0)
        ctr_volume_coord.append(coord_arr) 

    ############################function#############################
    for idx, _slice in enumerate(ctr_volume_coord):
        for point_idx in range(len(_slice)):
            zi, yi, xi = _slice[point_idx][2], _slice[point_idx][1], _slice[point_idx][0]
            try:ziplus, yiplus, xiplus = _slice[point_idx+1][2], _slice[point_idx+1][1], _slice[point_idx+1][0]
            except:ziplus, yiplus, xiplus = _slice[0][2], _slice[0][1], _slice[0][0]
            
            ##################bfs searching for next point#################
            ########################connecting pixel#######################
            std_distance = ((xi-xiplus)**2 + (yi-yiplus)**2)**0.5
            if std_distance > 20:
                continue
            queue = deque()
            dx = [1, -1, 0, 0]
            dy = [0, 0, 1, -1]
            voxelnp[int(zi)][int(yi)][int(xi)] = np.array([round(R*convertcolor), round(G*convertcolor), round(B*convertcolor)])
            queue.append((xi, yi))
            while queue:
                x, y = queue.popleft()
                for i in range(4):
                    nx = x + dx[i]
                    ny = y + dy[i]
                    this_distance = ((nx-xiplus)**2+(ny-yiplus)**2)**0.5
                    if std_distance <= this_distance:
                        continue
                    else:
                        std_distance = this_distance
                        if (nx, ny) == (xiplus, yiplus):
                            break
                        queue.append((nx, ny))
                        voxelnp[int(zi)][int(ny)][int(nx)] = np.array([round(R*convertcolor), round(G*convertcolor), round(B*convertcolor)])
            ###############################O(n)#############################
            
            

#데이터타입 이렇게해야 용량 많이줄어듦
voxelnp = voxelnp.astype('uint16')

np.save('D:\CodeMaster\w7voxels\p041rtst\p041voxel_ctr', voxelnp)
