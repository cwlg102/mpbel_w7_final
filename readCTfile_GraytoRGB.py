import os
import numpy as np
import pydicom
import matplotlib.pyplot as plt
from PIL import Image

folder_path = 'D:\CodeMaster\w7_dataset\P011_HN11_CT_2018-01-04_165105_RT^01.RT.Head.Neck.(Adult)_Head.&.Neck..3.0..B31s_n173__00001'

pic = []

#CT 파일 불러오기
#https://wikidocs.net/39 -> os.walk 사용법.

CT_voxel = np.zeros((173, 512, 512, 3))

for top, dir, file in os.walk(folder_path):
    k = -1
    for filename in file:
        if filename == 'metacache.mim':
            continue
        #print(folder_path+'/'+filename)
        k += 1
        ds = pydicom.dcmread(folder_path + '/' + filename, force=True)
        pic.append(ds)
        #matlab에서 largestimagepixel value 따져야함!
        tmp = ds.pixel_array/4095 #largepixelvalue로 나눠줌.
        
        pixel_rgb = np.stack((tmp,) * 3, axis = -1) #grayscale->RGB convert
        CT_voxel[k] = pixel_rgb #그레이 스케일 복셀 -> RGB로 바꾸어야...
    break
#pic엔 dicom 데이터가 들어있음.

#print(np.max(CT_voxel))
#quit()
CT_voxel += np.load('D:\CodeMaster\w7voxels\p011rtst\p011voxel_ctr.npy')
np.save('D:\CodeMaster\w7voxels\p011ct\p011CTvoxel', CT_voxel)
window = plt.figure(figsize = (20, 32))
n_cols = 6
n_rows = (len(pic)//n_cols + 1)
print(len(pic))
for idx in range(len(pic)):
    #window.add_subplot(n_rows, n_cols, idx+1)
    #plt.imsave('D:\CodeMaster\w7voxels\p011ct\p011CT%d' %(idx+1), CT_voxel[idx])
    plt.imshow(CT_voxel[idx])
    plt.savefig('D:\CodeMaster\w7voxels\p011ct\p011ct%d' %(idx+1))
    #plt.show()
#21, 31 -> 정렬이 안되어있음.