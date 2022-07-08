import os
import re
from nbformat import write
import numpy as np
import pydicom
from pydicom.pixel_data_handlers.util import apply_modality_lut, apply_voi_lut, apply_windowing
from numpngw import write_png
import imageio
#from PIL import Image #PIL은 8bit image만 다룰수 있음.
#https://stackoverflow.com/questions/62739851/convert-rgb-arrays-to-pil-image

basepath = 'D:\CodeMaster\w7_dataset'
folder_path = basepath + '\P001_HN1_CT_2018-11-01_102652_RT^01.RT.Head.Neck.(Adult)_Head.&.Neck..3.0..B31s_n150__00000'

pic = []

#CT 파일 불러오기
#https://wikidocs.net/39 -> os.walk 사용법.


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
#dicom file 끝에있는 번호를 정렬하는데 그 번호가 들어있는 리스트를 인덱스대로 정렬함
#정렬된 인덱스대로 dicom file을 가져오면 됨.
sorted_filename_list = []
for i in range(len(fileidx)):
    sorted_filename_list.append(filename_list[fileorder[i]])

zsize = len(sorted_filename_list)
CT_voxel = np.zeros((zsize, 512, 512, 3), 'int32')
#file정렬
fordeterminepixelvalue = pydicom.dcmread(folder_path + '/' + sorted_filename_list[0])

if fordeterminepixelvalue.PixelRepresentation == 1:
    conv_coeff = 2**15
    for i in range(len(sorted_filename_list)):
        ct_dicomdata = pydicom.dcmread(folder_path + '/' + sorted_filename_list[i])
        pic.append(ct_dicomdata)
        slope = int(ct_dicomdata.RescaleSlope)
        intercept = int(ct_dicomdata.RescaleIntercept)
        temp_slice = slope * ct_dicomdata.pixel_array + intercept#largepixelvalue로 나눠줌.
        temp_slice = temp_slice.astype('int32')

        window_center = ct_dicomdata.WindowCenter
        window_width = ct_dicomdata.WindowWidth
        
        img_min = window_center - window_width // 2
        img_max = window_center + window_width // 2

        temp_slice[temp_slice < img_min] = img_min
        temp_slice[temp_slice > img_max] = img_max

        temp_slice *= round(conv_coeff/(img_max-img_min))
        pixel_rgb = np.stack((temp_slice, ) * 3, axis = -1)
        CT_voxel[i] = pixel_rgb

#elif ispixelplus.Manufacturer == 'SIEMENS': #SIEMENS일때,,, 자체 windowing
else: 
    conv_coeff = 2**15
    for i in range(len(sorted_filename_list)):
        ct_dicomdata = pydicom.dcmread(folder_path + '/' + sorted_filename_list[i])
        pic.append(ct_dicomdata)
         #largepixelvalue로 나눠줌.
        slope = int(ct_dicomdata.RescaleSlope)
        intercept = int(ct_dicomdata.RescaleIntercept)
        temp_slice = slope * ct_dicomdata.pixel_array + intercept
        temp_slice = temp_slice.astype('int32')

        window_center = ct_dicomdata.WindowCenter[1]
        window_width = ct_dicomdata.WindowWidth[1]

        img_min = window_center - window_width // 2
        img_max = window_center + window_width // 2

        temp_slice[temp_slice < img_min] = img_min
        temp_slice[temp_slice > img_max] = img_max

        temp_slice *= round(conv_coeff/(img_max-img_min))
        pixel_rgb = np.stack((temp_slice, ) * 3, axis = -1)
        CT_voxel[i] = pixel_rgb


ctr_voxel = np.load('D:\CodeMaster\w7voxels\p001rtst\p001voxel_ctr.npy')

print(np.min(CT_voxel))
print(np.max(CT_voxel))
CT_voxel += 32800-abs(np.min(CT_voxel))

CT_voxel[CT_voxel <= np.min(CT_voxel)] = 0
CT_voxel[CT_voxel >= np.max(CT_voxel)] = 2**16-1

CT_voxel = CT_voxel.astype('uint16')

###################pls check manufaturer####################
if ct_dicomdata.Manufacturer != 'SIEMENS':
    ctr_voxel = np.flip(ctr_voxel, axis = 0)

CT_ctr_voxel = np.where(ctr_voxel != [0, 0, 0], ctr_voxel, CT_voxel)
np.save('D:\CodeMaster\w7voxels\p001ct\p001CTvoxel', CT_ctr_voxel)

 
for k in range(len(CT_ctr_voxel)):
    write_png('D:\CodeMaster\w7voxels\p001ct\p001ct%d.png' %(k+1), CT_ctr_voxel[k])
    
