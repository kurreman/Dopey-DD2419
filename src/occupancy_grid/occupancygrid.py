#!/usr/bin/env python3
import rospy
from nav_msgs.msg import MapMetaData, OccupancyGrid
from std_msgs.msg import Header
from geometry_msgs.msg import PoseStamped, PolygonStamped, TransformStamped, Point32, Pose
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sensor_msgs.msg import LaserScan
import open3d as o3d
from open3d_ros_helper import open3d_ros_helper as o3drh
import tf2_ros
import tf2_geometry_msgs
from math import fabs

class Occupancygrid:
    def __init__(self):
        self.f = 10
        self.rate = rospy.Rate(self.f)

        self.publisher_occupancygrid = rospy.Publisher(
            "/occupancygrid", OccupancyGrid, queue_size=10
        )

        self.publisher_pointtransformed = rospy.Publisher(
            "/checkpoint", PoseStamped, queue_size= 10
        )
        self.sub_laserscan = rospy.Subscriber(
            "/laserscan", LaserScan, self.scan_callback
        )

        self.sub_workspace = rospy.Subscriber(
            "/workspace", PolygonStamped, self.workspace_callback
        )
        self.laserscan = LaserScan()


        self.vertices = []
        # print(
        #     f"vertices: {self.vertices}, x min:{min(self.vertices[:,0])}, xmax: {max(self.vertices[:,0])}, y min: {min(self.vertices[:, 1])}, y max : {max(self.vertices[:,1])}"
        # )
        self.x_low = 0
        self.x_high = 0
        self.y_low = 0
        self.y_high = 0

        self.x_cells = 0
        self.y_cells = 0
        self.resolution = 0.025 # m per cell 

        self.y_n = int(1 / self.resolution)
        self.x_n = int(1 / self.resolution)

        self.occupied_value = 1
        self.freespace_value = 0
        self.uknownspace_value = -1

        self.checkpose = PoseStamped()


        self.grid = np.ones((2, 2)) 
        # self.vertices_list = np.append(self.vertices, [self.vertices[0]], axis = 0)

        self.buffer = tf2_ros.Buffer(rospy.Duration(1200.0))
        self.listener = tf2_ros.TransformListener(self.buffer)
        self.source_frame = "camera_color_frame"
        self.target_frame = "map"
        self.transform_camera2map = TransformStamped()
        self.timeout = rospy.Duration(1)

        self.pcd = o3d.geometry.PointCloud()

        self.robot_transform = TransformStamped()

        rospy.wait_for_message("/workspace", PolygonStamped)

        self.run()

    def get_i_index(self, x):
        index = math.floor((x - self.x_low)/self.resolution) 
        if index < 0:
            index = 0
        elif index > (self.x_cells - 1):
            index = self.x_cells - 1
        return index

    def get_j_index(self, y):
        index = math.floor((y - self.y_low)/self.resolution)
        if index < 0:
            index = 0
        elif index > (self.y_cells- 1):
            index =  self.y_cells - 1
        return index

    def get_x_pos(self, i):
        step = (self.x_high - self.x_low) / self.x_cells
        x_pos = (
            self.x_low + step * i + step / 2
        )  # added step / 2 so that; the coordinate is in the middle of the cell
        return x_pos

    def get_y_pos(self, j):
        step = (self.y_high - self.y_low) / self.y_cells
        y_pos = (
            self.y_low + step * j + step / 2
        )  # added step/2 so that the coordinate is in the middle of the cells
        return y_pos

    def incrementer(self, x, y, direction):
        # x and y are the current position of the robot in discrete values
        dx = np.cos(direction)
        dy = np.sin(direction)

        x += dx
        y += dy
        return [int(x), int(y)]

    # def raytrace(self, indices_robot, indices_obstacles, direction):
    #     (x_start, y_start) = indices_robot
    #     (x_end, y_end) = indices_obstacles
    #     # dx = np.cos(direction)
    #     # dy = np.sin(direction)
    #     direction_2 = np.arctan2((y_end-y_start),(x_end-x_start))
    #     dx = np.cos(direction_2)
    #     dy = np.sin(direction_2)
    #     print(f"indices robot:{x_start, y_start}")
    #     print(f"indices obstacle:{x_end, y_end}")
    #     print(f"step size x, y :{dx, dy}")

    #     x_mid = x_start
    #     y_mid = y_start
        
    #     traversed = []
    #     print(f"obstacle indice: {x_end, y_end}")
    #     while (x_mid, y_mid) != indices_obstacles:
    #         traversed.append((int(x_mid), int(y_mid)))
    #         plt.plot(int(x_end), int(y_end))
    #         x_mid += dx  
    #         y_mid += dy
    #         print(f"incrementsL{x_mid, y_mid}")
    #         plt.scatter(int(x_mid), int(y_mid))
    #     plt.show()
    #     print(traversed)


    #     return traversed
    
    def raytrace(self, start, end):
        """Returns all cells in the grid map that has been traversed
        from start to end, including start and excluding end.
        start = (x, y) grid map index
        end = (x, y) grid map index
        """
        (start_x, start_y) = start
        (end_x, end_y) = end
        x = start_x
        y = start_y
        (dx, dy) = (fabs(end_x - start_x), fabs(end_y - start_y))
        n = dx + dy
        x_inc = 1
        if end_x <= start_x:
            x_inc = -1
        y_inc = 1
        if end_y <= start_y:
            y_inc = -1
        error = dx - dy
        dx *= 2
        dy *= 2

        traversed = []
        for i in range(0, int(n)):
            traversed.append((int(x), int(y)))

            if error > 0:
                x += x_inc
                error -= dy
            else:
                if error == 0:
                    traversed.append((int(x + x_inc), int(y)))
                y += y_inc
                error += dx

        return traversed
    
    

    def update_map(self):
        # transform_camera2map = self.buffer.lookup_transform(self.source_frame, self.target_frame, rospy.Time(0), self.timeout)
        self.transform_camera2map = self.buffer.lookup_transform(self.target_frame, self.source_frame, rospy.Time(0), self.timeout)
        # print(self.transform_camera2map)
        #robot_pose## get ROBOT POSITION IN MAP FRAME 
        x_r = self.get_i_index(self.transform_camera2map.transform.translation.x)
        y_r = self.get_j_index(self.transform_camera2map.transform.translation.y)
        # print(f"robot indices:{x_r, y_r}")


        angle = self.laserscan.angle_min
        for count, dist in enumerate(self.laserscan.ranges):
            # print(f"{count} dist:{dist}")
            distancePoseStamped = PoseStamped()
            distancePoseStamped.pose.position.x = dist * np.cos(angle) #these need to be rotated into the map frame 
            distancePoseStamped.pose.position.y = dist * np.sin(angle)
            distancePoseStamped.header.frame_id = "camera_color_frame"
            obstacle_map_pose = tf2_geometry_msgs.do_transform_pose(distancePoseStamped, self.transform_camera2map) #continuous coordinates
            # print(f"transformed obstacle position:{obstacle_map_pose.pose.position.x, obstacle_map_pose.pose.position.y}")
            self.checkpose.pose.position= obstacle_map_pose.pose.position
            self.checkpose.pose.orientation = obstacle_map_pose.pose.orientation
            self.checkpose.header = distancePoseStamped.header
            self.checkpose.header.frame_id = "map"
            
            # print(f"check pose: {self.checkpose}")
            
            x_o = self.get_i_index(obstacle_map_pose.pose.position.x) #continuous 2 discrete
            y_o = self.get_j_index(obstacle_map_pose.pose.position.y)
            self.grid[x_o, y_o] = self.occupied_value  # mark occupied space
            # print(f"occupied indices:{x_o, y_o}")
            # print(self.grid[x_o, y_o])

            traversed = self.raytrace((x_r, y_r), (x_o, y_o))
            print("successful raytracing")
            for xt, yt in traversed:
                self.grid[xt, yt] = self.freespace_value # FREE SPACE
            
            self.grid[x_o, y_o] = self.occupied_value 
            
            angle += self.laserscan.angle_increment
            #check if traversed

        #for every distance in the range list coming from the msg
        #find the transformation from camera optical color to map 
        #robot coordinates [0,0]
        #obstacle coordinates robot_coord[0] + dist*np.cos(angle)

        


    def scan_callback(self, msg):
        self.laserscan = msg
        # self.update_map()
        # for x, y in zip(*coordinate_list):
        #     obstacle_pos_dicrete_space = [self.get_i_index(x), self.get_j_index(y)]
        #     delta_y = obstacle_pos_dicrete_space[1] - robot_pos_disc_space[1]
        #     delta_x = obstacle_pos_dicrete_space[0] - robot_pos_disc_space[0]
        #     bounded = True
        #     while bounded:
        #         # FREE SPACE
        #         direction = np.arctan2(delta_y / delta_x)
        #         robot_explore_pos = self.incrementer(
        #             robot_pos_disc_space[0], robot_pos_disc_space[1], direction
        #         )
        #         self.grid[robot_explore_pos[0], robot_explore_pos[1]] = 0  # free space

        #         bounded = robot_explore_pos != obstacle_pos_dicrete_space

        #     # OCCUPIED SPACE
        #     self.grid[self.get_i_index(x), self.get_j_index(y)] = -1  # occupied
        # # Unknown

        # Free space

    def workspace_callback(self, msg):
        self.vertices = msg.polygon.points
        self.x_low = min(self.vertices, key=lambda point: point.x).x
        self.x_high = max(self.vertices, key=lambda point: point.x).x
        self.y_low = min(self.vertices, key=lambda point: point.y).y
        self.y_high = max(self.vertices, key=lambda point: point.y).y
        # print(self.x_low) #corners of the occupancy grid in the map frame
        # print(self.x_high)
        # print(self.y_low)
        # print(self.y_high)
        self.x_cells = int((self.x_high - self.x_low) /self.resolution) #cells / m
        self.y_cells = int((self.y_high - self.y_low) /self.resolution) #cells / m
        self.grid = np.ones((self.x_cells, self.y_cells)) *self.uknownspace_value 



    def run(self):
        while not rospy.is_shutdown():
            metadata = MapMetaData()
            # metadata.map_load_time =
            # metadata.origin =
            self.update_map()
            metadata.resolution = self.resolution #meters per cell 
            metadata.width = self.x_cells # how many cells
            metadata.height = self.y_cells # how many cells 
            originPose = Pose()
            # originPose.position.x = self.transform_camera2map.transform.translation.x 
            # originPose.position.y = self.transform_camera2map.transform.translation.y
            originPose.position.x = self.x_low 
            originPose.position.y = self.y_low
            # originPose.orientation = self.transform_camera2map.transform.rotation #same orientation as coming from the transformation
            metadata.origin = originPose
            # print(f"cameratransform:{self.transform_camera2map}")
            # print(f"origin:{originPose}")

            occupancygrid_data = OccupancyGrid()
            occupancygrid_data.info = metadata
            header =  Header()
            header.frame_id = "map"
            header.stamp = rospy.Time.now()
            occupancygrid_data.header = header
            # print(f"Free space {sum(sum(self.grid == self.freespace_value))}\noccupied space: {sum(sum(self.grid == self.occupied_value))}\nunkown space: {sum(sum(self.grid == self.uknownspace_value))}")
            occupancygrid_data.data = list(self.grid.T.reshape(-1).astype(np.int8))
            # print(occupancygrid_data.data)
            self.publisher_occupancygrid.publish(occupancygrid_data)
            self.publisher_pointtransformed.publish(self.checkpose)
            print("published stuff")


            self.rate.sleep()


if __name__ == "__main__":
    try:
        rospy.init_node("occupancygrid")
        Occupancygrid()
        rospy.spin()
    except rospy.ROSInternalException:
        pass
