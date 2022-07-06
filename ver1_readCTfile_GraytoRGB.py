import os
import re
import numpy as np
import pydicom
from PIL import Image

folder_path = 'D:\CodeMaster\w7_dataset\P061_HN61_CT_2015-02-24_154354_RT^01.RT.Head.Neck.(Adult)_Head.&.Neck..3.0..B31s_n138__00001'

pic = []

#CT 파일 불러오기
#https://wikidocs.net/39 -> os.walk 사용법.

CT_voxel = np.zeros((138, 512, 512, 3))
filename_list = []
fileidx = []
for top, dir, file in os.walk(folder_path):
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

#file정렬
for i in range(len(sorted_filename_list)):
    ds = pydicom.dcmread(folder_path + '/' + sorted_filename_list[i])
    pic.append(ds)
    tmp = 255*(ds.pixel_array/4095)#largepixelvalue로 나눠줌.
    pixel_rgb = np.stack((tmp, ) * 3, axis = -1) #그레이 스케일 복셀 -> RGB로 바꾸어야...
    CT_voxel[i] = pixel_rgb

#print(np.max(CT_voxel))
#quit()
CT_voxel = CT_voxel.astype('uint8')
ctr_voxel = np.load('D:\CodeMaster\w7voxels\p061rtst\p061voxel_ctr.npy')

CT_ctr_voxel = np.where(ctr_voxel != [0, 0, 0], ctr_voxel, CT_voxel)
np.save('D:\CodeMaster\w7voxels\p061ct\p061CTvoxel', CT_ctr_voxel)

for k in range(len(CT_ctr_voxel)):
    tempdata = CT_ctr_voxel[k]
    img = Image.fromarray(tempdata, 'RGB')
    img.save('D:\CodeMaster\w7voxels\p061ct\p061ct%d.png' %(k+1))
    
#21, 31 -> 정렬이 안되어있음.