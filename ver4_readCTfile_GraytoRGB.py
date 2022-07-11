import os
import re
import numpy as np
import pydicom
from numpngw import write_png

#from PIL import Image #PIL은 8bit image만 다룰수 있음.
#https://stackoverflow.com/questions/62739851/convert-rgb-arrays-to-pil-image

basepath = 'D:\CodeMaster\w7_dataset'
#CT폴더 불러오기
folder_path = basepath + '\P021_HN21_CT_2018-05-18_114459_._Neck.3.0_n164__00001'
#Contour파일 불러오기
ctr_voxel = np.load('D:\CodeMaster\w7voxels\p021rtst\p021voxel_ctr.npy')
#https://wikidocs.net/39 -> os.walk 사용법.

fileidx = []
CT_dcm_files = [] #list for dcm data
for top, dir, file in os.walk(folder_path):
    k = -1
    for filename in file:
        if filename[-3:] != 'dcm':
            continue
        temp_ct_slice = pydicom.dcmread(folder_path + '/' + filename)
        CT_dcm_files.append(temp_ct_slice)
        idxnum = temp_ct_slice.InstanceNumber
        fileidx.append(idxnum)
    break


fileidx = np.array(fileidx)
fileorder = np.argsort(fileidx) 
#dicom file 끝에있는 번호를 정렬하는데 그 번호가 들어있는 리스트를 인덱스대로 정렬함
#정렬된 인덱스대로 dicom file을 가져오면 됨.
sorted_CT_file = []
for i in range(len(fileidx)):
    sorted_CT_file.append(CT_dcm_files[fileorder[i]])

zsize = len(sorted_CT_file)
CT_voxel = np.zeros((zsize, 512, 512, 3), 'int32')
first_ct = sorted_CT_file[0]

convert_coeff = 2**(first_ct.BitsAllocated-1)

if type(first_ct.WindowCenter) == pydicom.valuerep.DSfloat:
    window_center = first_ct.WindowCenter
    window_width = first_ct.WindowWidth
else:
    window_center = first_ct.WindowCenter[1]
    window_width = first_ct.WindowWidth[1]
    
img_min = window_center - window_width // 2
img_max = window_center + window_width // 2

if first_ct.Manufacturer != 'SIEMENS':
    sorted_CT_file.reverse()

for i in range(len(sorted_CT_file)):
    ct_dicomdata = sorted_CT_file[i]
    slope = int(ct_dicomdata.RescaleSlope)
    intercept = int(ct_dicomdata.RescaleIntercept)
    temp_arr_slice = slope * ct_dicomdata.pixel_array + intercept
    temp_arr_slice = temp_arr_slice.astype('int32')
    temp_arr_slice[temp_arr_slice < img_min] = img_min
    temp_arr_slice[temp_arr_slice > img_max] = img_max
    temp_arr_slice *= round(convert_coeff/(img_max-img_min))
    pixel_rgb = np.stack((temp_arr_slice, ) * 3, axis = -1)
    CT_voxel[i] = pixel_rgb


print(np.min(CT_voxel))
print(np.max(CT_voxel))
CT_voxel += int(convert_coeff)-abs(np.min(CT_voxel))
CT_voxel[CT_voxel <= np.min(CT_voxel)] = 0
CT_voxel[CT_voxel >= np.max(CT_voxel)] = 2**16-1

CT_voxel = CT_voxel.astype('uint16')

###################pls check manufaturer####################

#if ct_dicomdata.Manufacturer != 'SIEMENS':
#    ctr_voxel = np.flip(ctr_voxel, axis = 0)

CT_ctr_voxel = np.where(ctr_voxel != [0, 0, 0], ctr_voxel, CT_voxel)
CT_ctr_voxel = np.flip(CT_ctr_voxel, axis = 0)
np.save('D:\CodeMaster\w7voxels\p021ct\p021CTvoxel', CT_ctr_voxel)

 
for k in range(len(CT_ctr_voxel)):
    write_png('D:\CodeMaster\w7voxels\p021ct\p021ct%d.png' %(k+1), CT_ctr_voxel[k])
    
