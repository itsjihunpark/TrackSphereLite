import numpy as np


def get_vector_from_two_points(xyz1, xyz2):
    x1, y1, z1 = xyz1
    x2, y2, z2 = xyz2
    return (x2-x1),(y2-y1),(z2-z1)
    
def calculate_angle_between_vector_and_z_axis(vector):
    # angle is in radian
    # arcos(z/sqrt(x^2+y^2+z^2))
    x, y, z = vector
    vector_dist = calculate_vector_dist(vector)
    return np.arccos(z/vector_dist)
    
def calculate_vector_dist( vector):
    x, y, z = vector
    vector_dist = np.sqrt(((x)**2)+((y)**2)+((z)**2))

def compute_centroid(bbox):
    left, top, right, bottom = bbox

    center_x = left + ((right-left)/2)
    center_y = top + ((bottom-top)/2)
    
    return (int(center_x), int(center_y))


def reconstruct_3d(centroid_left, centroid_right, config):

    xl, yl = centroid_left
    xr, yr = centroid_right

    disparity  = xl-xr
    
    # obtain from disparity and depth relationship from the 6th degree polynomial
    z = 0


    # obtain from depth and px width relationship from the quadratic
    x = 0


    # obtain from depth and px height relationship from the quadratic
    y = 0

    return round(x, 3), round(y, 3), round(z,3)    


def check_det_within_roi(roi, det):
    roi_x1, roi_y1, roi_x2, roi_y2 = roi
    det_x1, det_y1, det_x2, det_y2 = det

    within_x_axis = False
    within_y_axis = False

    if det_x1 >= roi_x1 and det_x2 <= roi_x2:
        within_x_axis = True
    if det_y1 >= roi_y1 and det_y2 <= roi_y2:
        within_y_axis = True
    
    return within_x_axis and within_y_axis

    

