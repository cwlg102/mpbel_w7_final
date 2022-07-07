import os
import re
import numpy as np
import pydicom
from pydicom.pixel_data_handlers.util import apply_modality_lut, apply_voi_lut
from numpngw import write_png
#from PIL import Image #PIL은 8bit image만 다룰수 있음.
#https://stackoverflow.com/questions/62739851/convert-rgb-arrays-to-pil-image


folder_path = 'D:\CodeMaster\w7_dataset\P001_HN1_CT_2018-11-01_102652_RT^01.RT.Head.Neck.(Adult)_Head.&.Neck..3.0..B31s_n150__00000'
zsize = int(folder_path[-10:-7])
pic = []

#CT 파일 불러오기
#https://wikidocs.net/39 -> os.walk 사용법.

CT_voxel = np.zeros((zsize, 512, 512, 3))
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

#file정렬
determine_company = pydicom.dcmread(folder_path + '/' + sorted_filename_list[0])
window_center = -1000
window_width = 6000
if determine_company.Manufacturer == 'TOSHIBA':
    window_center = -1200
    window_width = 4000
    for i in range(len(sorted_filename_list)):
        ds = pydicom.dcmread(folder_path + '/' + sorted_filename_list[i])
        pic.append(ds)
        s = int(ds.RescaleSlope)
        b = int(ds.RescaleIntercept)
        temp_slice = s * ds.pixel_array + b#largepixelvalue로 나눠줌.

        ds.WindowCenter = window_center
        ds.WindowWidth = window_width
        temp_slice = apply_modality_lut(temp_slice, ds)
        temp_slice = apply_voi_lut(temp_slice, ds)

        pixel_rgb = np.stack((temp_slice, ) * 3, axis = -1) #그레이 스케일 복셀 -> RGB로 바꾸어야...
        CT_voxel[i] = pixel_rgb

elif determine_company.Manufacturer == 'SIEMENS': #SIEMENS일때,,, 자체 windowing
    for i in range(len(sorted_filename_list)):
        ds = pydicom.dcmread(folder_path + '/' + sorted_filename_list[i])
        pic.append(ds)
        
        temp_slice = ds.pixel_array #largepixelvalue로 나눠줌.
        pixel_rgb = np.stack((temp_slice, ) * 3, axis = -1) #그레이 스케일 복셀 -> RGB로 바꾸어야...
        CT_voxel[i] = pixel_rgb
    CT_voxel /= 4095
    CT_voxel *= 65535
    CT_voxel = np.where(CT_voxel > 40000, 58000, CT_voxel)
    CT_voxel = np.where(CT_voxel < 7000, 4000, CT_voxel)
CT_voxel = CT_voxel.astype('uint16')
ctr_voxel = np.load('D:\CodeMaster\w7voxels\p001rtst\p001voxel_ctr.npy')

###################pls check manufaturer####################
if ds.Manufacturer == 'TOSHIBA':
    ctr_voxel = np.flip(ctr_voxel, axis = 0)

CT_ctr_voxel = np.where(ctr_voxel != [0, 0, 0], ctr_voxel, CT_voxel)
np.save('D:\CodeMaster\w7voxels\p001ct\p001CTvoxel', CT_ctr_voxel)

for k in range(len(CT_ctr_voxel)):
    ####use PIL part######
    #tempdata = CT_ctr_voxel[k]
    #img = Image.fromarray(tempdata)
    #img.save('D:\CodeMaster\w7voxels\p001ct\p001ct%d.png' %(k+1)) 
    ####use numpngw part####
    write_png('D:\CodeMaster\w7voxels\p001ct\p001ct%d.png' %(k+1), CT_ctr_voxel[k])
    
