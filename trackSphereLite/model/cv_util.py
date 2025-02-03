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


