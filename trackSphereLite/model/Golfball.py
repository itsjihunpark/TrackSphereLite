import projectilepy
import numpy as np
import matplotlib.pyplot as plt

class Golfball:

    def __init__(self,golfball_id, swing_event_timestamp, type_of_club, replaypath): 
        self.golfball_id = golfball_id
        self.swing_event_timestamp = swing_event_timestamp
        self.type_of_club = type_of_club
        self.replaypath = replaypath


    def get_golfball_motion_properties(self, get_trajectory=False):
        raise NotImplementedError("Subclass must implement this class")
    

    def get_golf_ball_velocity(self):
        raise NotImplementedError("Subclass must implement this class")


class FlightedGolfball(Golfball):

    def __init__(self, golfball_id, swing_event_timestamp, type_of_club, replaypath, velocity_x, velocity_y, velocity_z):
        super().__init__( golfball_id, swing_event_timestamp, type_of_club, replaypath) 
        # additonal attributes ball_spinrate, ball_launch_angle, velocity_x, velocity_y, velocity_z
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.velocity_z = velocity_z
        self.velocity = self.get_golf_ball_velocity()
        self.ball_launch_angle, self.directional_angle = self.calculate_launch_angle_and_direction()
        self.distance = self.get_golfball_motion_properties()
        

    def calculate_launch_angle_and_direction(self):
        # angle is in radian
        # arcos(z/sqrt(x^2+y^2+z^2))
        velocity = self.velocity / 3.6
        launch_angle = np.arccos(np.sqrt(((self.velocity_x)**2)+((self.velocity_y)**2))/velocity) # cos^-1(ajacent/hypotenuse)
        launch_angle = np.rad2deg(launch_angle )
        
        angle_direction = self.velocity_x/np.sqrt((self.velocity_x**2)+(self.velocity_y**2))
        angle_direction = np.arccos(angle_direction)

        return round(launch_angle, 2), angle_direction


    def get_golf_ball_velocity(self):
            velocity = np.sqrt(((self.velocity_x )**2)+((self.velocity_y)**2)+((self.velocity_z )**2))
            velocity *=3.6 # m/s to kph
            return round(velocity,2)


    def get_golfball_motion_properties(self, get_trajectory=False):
        # https://www.math.union.edu/~wangj/courses/previous/math238w13/Golf%20Ball%20Flight%20Dynamics2.pdf
        # For reason why this model underestimates the distance flown by a golf ball 
        # model ignores the dimples on a golf ball; assumes smooth ball
        # Could experiment with table tennis ball

        # https://github.com/ZCK12/projectilepy
        velocity = self.velocity / 3.6 #kph to m/s
        model = projectilepy.model(initial_velocity = velocity, initial_angle=self.ball_launch_angle)
        model.drag = "Newtonian"
        model.mass = 0.0027 # 0.045kg golfball 0.0027kg table tenis ball
        model.drag_coefficient = 0.24 # https://www.researchgate.net/publication/325969742_Drag_Coefficients_of_Golf_Balls
        model.cross_sectional_area = 0.001297 # 21.34mm radius
        model.run()
        final_position = model.final_position()
        distance = round(final_position[0],2)
        if not get_trajectory:
            self.distance = distance
            return distance
        else:
            x1, y1 = zip(*model.positionValues)

            # apply rotation to horizontal and vertical trajectory to obtain xyz

            x2 = np.multiply(x1,np.cos(self.directional_angle))
            y2 = np.multiply(x1,np.sin(self.directional_angle))
            z2 = y1
            
            if self.velocity_y < 0:
                sign = -1
            else:
                sign = 1
            y2 *= sign

            # x = distance down range
            # y = distance perpendicular to down range
            # z = height of ball
            return y2.tolist(), x2.tolist(), z2
        

class RollingGolfball(Golfball):
    
    def __init__(self, golfball_id, swing_event_timestamp, type_of_club, replaypath, points_x, points_y, points_z, total_putt_Time):
        super().__init__(golfball_id, swing_event_timestamp, type_of_club, replaypath)

        self.points_x = points_x
        self.points_y = points_y
        self.points_z = points_z
        self.total_putt_Time = total_putt_Time
        self.ball_launch_angle = 0 # ball is rolling so angle would be 0 deg
        self.velocity, self.distance = self.get_golfball_motion_properties()
    

    def get_golfball_motion_properties(self, get_trajectory=False):
        # probably regression line fitting neeeded
        
        x = self.points_x.split(",")
        y = self.points_y.split(",")
        z = np.zeros(len(x)).tolist() # no launch so z will always be zero
        # trajectory = from x and y points draw a polyfit line; return x, y and z=0 (no launch)
        # distance = get the length of the polyfit line 
        # velocity = distance/total_putt_time
    
        if not get_trajectory:
            return 10, 10
        else:
            return x, y, z 
        

    
if __name__ == "__main__":
    x = 32
    y = 42
    z = 22
    v = np.sqrt(((x)**2)+((y)**2)+((z)**2))

    angle_direction = x/np.sqrt((x**2)+(y**2))
    angle_direction = np.arccos(angle_direction)
    #angle_direction = np.rad2deg(angle_direction)

    launch_angle = np.arccos(np.sqrt(((x)**2)+((y)**2))/v)
    launch_angle = np.rad2deg(launch_angle)
    launch_angle = round(launch_angle, 2)

    mySimulator = projectilepy.model(initial_velocity=v, initial_angle=launch_angle)
    mySimulator.drag = "Newtonian"
    mySimulator.mass = 0.045 
    mySimulator.drag_coefficient = 0.24
    mySimulator.cross_sectional_area = 0.001297
    mySimulator.run()
    final_position = mySimulator.final_position()
    distance = final_position[0]
    print("flew a total of", distance, "meters!", "at", launch_angle, "deg", "v =", v, " angle y", angle_direction)
    
    x1, y = zip(*mySimulator.positionValues)

    x2 = np.multiply(x1,np.cos(angle_direction))
    z2 = y
    y2 = np.multiply(x1,np.sin(angle_direction))

    print(mySimulator.time_of_flight())
    ax = plt.axes(projection='3d')
    plt.xlabel("distance downrange")
    plt.ylabel("distance crossrange")
    plt.clabel("height")
    ax.plot(x2, y2, z2)
    plt.show()
