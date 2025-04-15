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


def reconstruct_3d(centroid_left, centroid_right, img_height, reconstruct_3d_reg_model, focal_length, optical_center_x, optical_center_y):

    xl, yl = centroid_left
    xr, yr = centroid_right

    disparity  = xl-xr    
    # obtain from disparity and depth relationship from the polynomial
    z_world = reconstruct_3d_reg_model['disparity_to_depth'](disparity) # depth (mm) from disparity

    # obtain from depth and px width relationship from the quadratic    
    mm_per_pixel_width = reconstruct_3d_reg_model['depth_to_px_width_coeff'](z_world) # px width coversion coefficient (mm/px) from depth
    # convert xl to camera-based coordinate system
    x = xl - optical_center_x
    # obtain position
    x_world = x*mm_per_pixel_width
    
    # obtain from depth and px height relationship from the quadratic
    mm_per_pixel_height = reconstruct_3d_reg_model['depth_to_px_height_coeff'](z_world) # px height coversion coefficient (mm/px) from depth
    # convert yl to camera-based coordinate system
    y = yl - optical_center_y
    # obtain position
    y_world = y*mm_per_pixel_width
     
    
    return round(x_world/1000,3), round(y_world/1000, 3), round(z_world/1000,3) # in meters   


def obtain_velocity_in_meters_per_second(timestamped_3d_positions):
    x0 = timestamped_3d_positions['x'][-4]
    y0 = timestamped_3d_positions['y'][-4]
    z0 = timestamped_3d_positions['z'][-4]
    t0 = timestamped_3d_positions['timestamp_l'][-4]

    x1 = timestamped_3d_positions['x'][-1]
    y1 = timestamped_3d_positions['y'][-1]
    z1 = timestamped_3d_positions['z'][-1]
    t1 = timestamped_3d_positions['timestamp_l'][-1] 
    
    delta_t_s = (t1 - t0)
    
    x_meters_per_second = ((x1 - x0))/delta_t_s # in m/s
    y_meters_per_second = ((y1 - y0))/delta_t_s # in m/s
    z_meters_per_second = ((z1 - z0))/delta_t_s # in m/s
    
    return x_meters_per_second, y_meters_per_second, z_meters_per_second

def bbox_is_valid(bbox_l, bbox_r):
    # if aspect ratio is at least 0.7 and at most 1.4
    left_l, top_l, right_l, bottom_l = bbox_l
    left_r, top_r, right_r, bottom_r = bbox_r
    
    width_l = right_l - left_l
    height_l = bottom_l - top_l
    
    width_r = right_r - left_r
    height_r = bottom_r - top_r

    aspect_ratio_l = width_l/height_l
    aspect_ratio_r = width_r/height_r

    is_valid = False
    if (0.9 < aspect_ratio_l and aspect_ratio_l < 1.1) and (0.9 < aspect_ratio_r and aspect_ratio_r < 1.1):
        is_valid = True
    return is_valid


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

    

