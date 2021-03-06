import os
import re
import numpy as np
import pydicom
from pydicom.pixel_data_handlers.util import apply_modality_lut, apply_voi_lut
from numpngw import write_png
from PIL import Image #PIL은 8bit image만 다룰수 있음.
#https://stackoverflow.com/questions/62739851/convert-rgb-arrays-to-pil-image


folder_path = 'D:\CodeMaster\w7_dataset\P091_HN91_CT_2019-06-10_173337_._Neck.3.0_n155__00000'

pic = []

#CT 파일 불러오기
#https://wikidocs.net/39 -> os.walk 사용법.

CT_voxel = np.zeros((155, 512, 512, 3))
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
det = pydicom.dcmread(folder_path + '/' + sorted_filename_list[0])
window_center = -1000
window_width = 6000
if det.Manufacturer == 'TOSHIBA':
    window_center = -1200
    window_width = 4000
    for i in range(len(sorted_filename_list)):
        ds = pydicom.dcmread(folder_path + '/' + sorted_filename_list[i])
        pic.append(ds)
        s = int(ds.RescaleSlope)
        b = int(ds.RescaleIntercept)
        tmp = s * ds.pixel_array + b#largepixelvalue로 나눠줌.

        ds.WindowCenter = window_center
        ds.WindowWidth = window_width
        tmp = apply_modality_lut(tmp, ds)
        tmp = apply_voi_lut(tmp, ds)

        pixel_rgb = np.stack((tmp, ) * 3, axis = -1) #그레이 스케일 복셀 -> RGB로 바꾸어야...
        CT_voxel[i] = pixel_rgb

else: #SIEMENS일때,,, 자체 windowing
    for i in range(len(sorted_filename_list)):
        ds = pydicom.dcmread(folder_path + '/' + sorted_filename_list[i])
        pic.append(ds)
        
        tmp = ds.pixel_array #largepixelvalue로 나눠줌.
        pixel_rgb = np.stack((tmp, ) * 3, axis = -1) #그레이 스케일 복셀 -> RGB로 바꾸어야...
        CT_voxel[i] = pixel_rgb
    CT_voxel /= 4095
    CT_voxel *= 65535
    CT_voxel = np.where(CT_voxel > 40000, 60000, CT_voxel)
    CT_voxel = np.where(CT_voxel < 11000, 0, CT_voxel)
CT_voxel = CT_voxel.astype('uint16')
ctr_voxel = np.load('D:\CodeMaster\w7voxels\p091rtst\p091voxel_ctr.npy')

###################pls check manufaturer####################
if ds.Manufacturer == 'TOSHIBA':
    ctr_voxel = np.flip(ctr_voxel, axis = 0)

CT_ctr_voxel = np.where(ctr_voxel != [0, 0, 0], ctr_voxel, CT_voxel)
np.save('D:\CodeMaster\w7voxels\p091ct\p091CTvoxel', CT_ctr_voxel)

for k in range(len(CT_ctr_voxel)):
    ####use PIL part######
    #tempdata = CT_ctr_voxel[k]
    #img = Image.fromarray(tempdata)
    #img.save('D:\CodeMaster\w7voxels\p061ct\p061ct%d.png' %(k+1)) 
    ####use numpngw part####
    write_png('D:\CodeMaster\w7voxels\p091ct\p091ct%d.png' %(k+1), CT_ctr_voxel[k])
    
