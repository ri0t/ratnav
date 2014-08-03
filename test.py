__author__ = 'riot'
import cv2
import numpy as np
from common import anorm
from matplotlib import pyplot as plt

def filter_matches(kp1, kp2, matches, ratio = 0.75):
    mkp1, mkp2 = [], []
    for m in matches:
        if len(m) == 2 and m[0].distance < m[1].distance * ratio:
            m = m[0]
            mkp1.append( kp1[m.queryIdx] )
            mkp2.append( kp2[m.trainIdx] )
    p1 = np.float32([kp.pt for kp in mkp1])
    p2 = np.float32([kp.pt for kp in mkp2])
    kp_pairs = zip(mkp1, mkp2)
    return p1, p2, kp_pairs

def explore_match(win, img1, img2, kp_pairs, status = None, H = None):
    h1, w1 = img1.shape[:2]
    h2, w2 = img2.shape[:2]
    vis = np.zeros((max(h1, h2), w1+w2), np.uint8)
    vis[:h1, :w1] = img1
    vis[:h2, w1:w1+w2] = img2
    vis = cv2.cvtColor(vis, cv2.COLOR_GRAY2BGR)

    if H is not None:
        corners = np.float32([[0, 0], [w1, 0], [w1, h1], [0, h1]])
        corners = np.int32( cv2.perspectiveTransform(corners.reshape(1, -1, 2), H).reshape(-1, 2) + (w1, 0) )
        cv2.polylines(vis, [corners], True, (255, 255, 255))

    if status is None:
        status = np.ones(len(kp_pairs), np.bool_)
    p1 = np.int32([kpp[0].pt for kpp in kp_pairs])
    p2 = np.int32([kpp[1].pt for kpp in kp_pairs]) + (w1, 0)

    green = (0, 255, 0)
    red = (0, 0, 255)
    white = (255, 255, 255)
    kp_color = (51, 103, 236)
    for (x1, y1), (x2, y2), inlier in zip(p1, p2, status):
        if inlier:
            col = green
            cv2.circle(vis, (x1, y1), 2, col, -1)
            cv2.circle(vis, (x2, y2), 2, col, -1)
        else:
            col = red
            r = 2
            thickness = 3
            cv2.line(vis, (x1-r, y1-r), (x1+r, y1+r), col, thickness)
            cv2.line(vis, (x1-r, y1+r), (x1+r, y1-r), col, thickness)
            cv2.line(vis, (x2-r, y2-r), (x2+r, y2+r), col, thickness)
            cv2.line(vis, (x2-r, y2+r), (x2+r, y2-r), col, thickness)
    vis0 = vis.copy()
    for (x1, y1), (x2, y2), inlier in zip(p1, p2, status):
        if inlier:
            cv2.line(vis, (x1, y1), (x2, y2), green)

    return vis

    # print("Showing")
    # cv2.imshow(win, vis)
    # def onmouse(event, x, y, flags, param):
    #     cur_vis = vis
    #     if flags & cv2.EVENT_FLAG_LBUTTON:
    #         cur_vis = vis0.copy()
    #         r = 8
    #         m = (anorm(p1 - (x, y)) < r) | (anorm(p2 - (x, y)) < r)
    #         idxs = np.where(m)[0]
    #         kp1s, kp2s = [], []
    #         for i in idxs:
    #              (x1, y1), (x2, y2) = p1[i], p2[i]
    #              col = (red, green)[status[i]]
    #              cv2.line(cur_vis, (x1, y1), (x2, y2), col)
    #              kp1, kp2 = kp_pairs[i]
    #              kp1s.append(kp1)
    #              kp2s.append(kp2)
    #         cur_vis = cv2.drawKeypoints(cur_vis, kp1s, flags=4, color=kp_color)
    #         cur_vis[:,w1:] = cv2.drawKeypoints(cur_vis[:,w1:], kp2s, flags=4, color=kp_color)
    #
    #     cv2.imshow(win, cur_vis)
    # cv2.setMouseCallback(win, onmouse)
    # return vis


img = cv2.imread('./images/training/bmw.png', 0)
plate = cv2.imread('./images/query/plate_german.png', 0)

orb = cv2.ORB()

# global thresholding
ret1,th1 = cv2.threshold(img,127,255,cv2.THRESH_BINARY)

# Otsu's thresholding
ret2,th2 = cv2.threshold(img,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)

# Otsu's thresholding after Gaussian filtering
blur = cv2.GaussianBlur(img,(3,3),0)
ret3,th3 = cv2.threshold(blur,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)



# Pick these images as matching sources
img = th2
plate = plate

# Compute keypoints
kp_img, des_img = orb.detectAndCompute(img,None)
kp_plate, des_plate = orb.detectAndCompute(plate,None)

img_kp_plate = cv2.drawKeypoints(plate, kp_plate, color=(0,255,0), flags=0)
img_kp_img = cv2.drawKeypoints(img, kp_img, color=(255 , 0, 0), flags=0)

# plot all the images and their histograms
images = [img, 0, th1,
          img, 0, th2,
          blur, 0, th3,
          img_kp_plate, 0, img_kp_img]
titles = ['Original Noisy Image','Histogram','Global Thresholding (v=127)',
          'Original Noisy Image','Histogram',"Otsu's Thresholding",
          'Gaussian filtered Image','Histogram',"Otsu's Thresholding",
          'Plate KP', 'Histogram', 'Image KP']
plt.figure(0)
for i in xrange(4):
    plt.subplot(5,3,i*3+1),plt.imshow(images[i*3],'gray')
    plt.title(titles[i*3]), plt.xticks([]), plt.yticks([])
    plt.subplot(5,3,i*3+2),plt.hist(images[i*3].ravel(),256)
    plt.title(titles[i*3+1]), plt.xticks([]), plt.yticks([])
    plt.subplot(5,3,i*3+3),plt.imshow(images[i*3+2],'gray')
    plt.title(titles[i*3+2]), plt.xticks([]), plt.yticks([])

plt.show()

# Do the matching

bf = cv2.BFMatcher(cv2.NORM_HAMMING) #, crossCheck=True)

print("Matching")
matches = bf.knnMatch(des_img, trainDescriptors=des_plate, k=2)
print("Filtering")
p1, p2, kp_pairs = filter_matches(kp_img, kp_plate, matches)
print("Displaying")
img_match = explore_match('find_obj', img, plate, kp_pairs)


# Plot the actual matching
plt.figure(1)
plt.imshow(img_match)

plt.show()