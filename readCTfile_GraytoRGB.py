import os
import numpy as np
import pydicom
import matplotlib.pyplot as plt
#현재파일: P001_HN1_CT_2018-11-01_102652_RT^01.RT.Head.Neck.(Adult)_Head.&.Neck..3.0..B31s_n150__00000
folder_path = 'D:\CodeMaster\w7_dataset\P001_HN1_CT_2018-11-01_102652_RT^01.RT.Head.Neck.(Adult)_Head.&.Neck..3.0..B31s_n150__00000'

pic = []

#CT 파일 불러오기
#https://wikidocs.net/39 -> os.walk 사용법.

CT_voxel = np.zeros((150, 512, 512, 3))
#matlab에서 largestimagepixel value 따져야함!
for top, dir, file in os.walk(folder_path):
    k = -1
    for filename in file:
        if filename == 'metacache.mim':
            continue
        #print(folder_path+'/'+filename)
        k += 1
        ds = pydicom.dcmread(folder_path + '/' + filename, force=True)
        pic.append(ds)
        tmp = ds.pixel_array/4095 #largepixelvalue로 나눠줌.
        pixel_rgb = np.stack((tmp,) * 3, axis = -1) #grayscale->RGB convert
        CT_voxel[k] = pixel_rgb #그레이 스케일 복셀 -> RGB로 바꾸어야...
        
    break
#np.save('CT_voxel_scaled', CT_voxel)
window = plt.figure(figsize = (20, 32))
n_cols = 6
n_rows = (len(pic)//n_cols + 1)
print(len(pic))
for idx in range(len(pic)):
    #window.add_subplot(n_rows, n_cols, idx+1)
    plt.imshow(CT_voxel[idx])
    plt.show()
    #plt.savefig('CT%d' %idx)