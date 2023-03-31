#!/usr/bin/env python3
import rospy
from nav_msgs.msg import MapMetaData, OccupancyGrid
from std_msgs.msg import Header
from geometry_msgs.msg import PoseStamped, PolygonStamped, TransformStamped, Point32, Pose
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sensor_msgs.msg import LaserScan
import open3d as o3d
from open3d_ros_helper import open3d_ros_helper as o3drh
import tf2_ros
import tf2_geometry_msgs
from math import fabs
from map_msgs.msg import OccupancyGridUpdate
import math



class Occupancygrid:
    def __init__(self):
        self.f = 10
        self.rate = rospy.Rate(self.f)

        self.publisher_occupancygrid = rospy.Publisher(
            "/occupancygrid", OccupancyGrid, queue_size=10
        )

        self.sub_laserscan = rospy.Subscriber(
            "/scan", LaserScan, self.scan_callback
        )

        self.sub_workspace = rospy.Subscriber(
            "/workspace", PolygonStamped, self.workspace_callback
        )
        self.publisher_mapupdates= rospy.Publisher(
            "map_updates", OccupancyGridUpdate, queue_size=10
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
        self.c_space=2
        self.freespace_value = 0
        self.uknownspace_value = -1
        self.radius = 1

        self.xf_list = []
        self.yf_list = []


        self.grid = np.ones((2, 2)) 
        # self.vertices_list = np.append(self.vertices, [self.vertices[0]], axis = 0)

        self.buffer = tf2_ros.Buffer(rospy.Duration(1200.0))
        self.listener = tf2_ros.TransformListener(self.buffer)
        self.source_frame = "camera_depth_frame"
        self.target_frame = "map"
        self.transform_camera2map = TransformStamped()
        self.timeout = rospy.Duration(1)

        self.pcd = o3d.geometry.PointCloud()

        self.robot_transform = TransformStamped()
        self.gotcb = False  
        rospy.wait_for_message("/workspace", PolygonStamped)
        self.gotcb=True
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
        for _ in range(0, int(n)):
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
        self.transform_camera2map = self.buffer.lookup_transform(self.target_frame, self.source_frame, rospy.Time(0), self.timeout)
        x_r = self.get_i_index(self.transform_camera2map.transform.translation.x)
        y_r = self.get_j_index(self.transform_camera2map.transform.translation.y)
        N = int((self.laserscan.angle_max-self.laserscan.angle_min)/self.laserscan.angle_increment)
        angles = np.linspace(self.laserscan.angle_min, self.laserscan.angle_max, N)
        for dist, angle in list(zip(self.laserscan.ranges, angles))[::10]:
            if np.isnan(dist):
                continue
            distancePoseStamped = PoseStamped()
            distancePoseStamped.pose.position.x = dist * np.cos(angle) #these need to be rotated into the map frame 
            distancePoseStamped.pose.position.y = dist * np.sin(angle)
            distancePoseStamped.header.frame_id = "camera_depth_frame"
            obstacle_map_pose = tf2_geometry_msgs.do_transform_pose(distancePoseStamped, self.transform_camera2map) #continuous coordinates

            x_o = self.get_i_index(obstacle_map_pose.pose.position.x) #continuous 2 discrete
            y_o = self.get_j_index(obstacle_map_pose.pose.position.y)

            traversed = self.raytrace((x_r, y_r), (x_o, y_o))
            for xt, yt in traversed:
                self.grid[xt, yt] = self.freespace_value # FREE SPACE
            
            self.grid[x_o, y_o] = self.occupied_value 
            self.xf_list.append(x_o)
            self.yf_list.append(y_o)

            
        
        update = OccupancyGridUpdate()
        update.x = min(self.xf_list)
        update.y = min(self.yf_list)
        update.width = max(self.xf_list) - update.x + 1
        update.height = max(self.yf_list) - update.y + 1
        update.data = []
        return update
    def inflate_map(self, grid_map):
        """For C only!
        Inflate the map with self.c_space assuming the robot
        has a radius of self.radius.

        Returns the inflated grid_map.

        Inflating the grid_map means that for each self.occupied_space
        you calculate and fill in self.c_space. Make sure to not overwrite
        something that you do not want to.


        You should use:
            self.c_space  # For C space (inflated space).
            self.radius   # To know how much to inflate.

            You can use the function add_to_map to be sure that you add
            values correctly to the map.

            You can use the function is_in_bounds to check if a coordinate
            is inside the map.

        :type grid_map: GridMap
        """

        """
        Fill in your solution here
        """
        r = self.radius
        perm = [
            (i, j)
            for i in range(-r, r + 1)
            for j in range(-r, r + 1)
            if np.sqrt(i * i + j * j) <= r
        ]
        for x in range(self.x_cells):
            for y in range(self.y_cells):
                if grid_map[x, y] == self.occupied_value:
                    for i, j in perm:
                        try:
                            if grid_map[x + i, y + j] != self.occupied_value:
                                grid_map[x + i, y + j] = self.c_space
                        except:
                            pass

        # Return the inflated map
        return grid_map
    def scan_callback(self, msg):
        self.laserscan = msg
        metadata = MapMetaData()
        update = self.update_map()
        self.publisher_mapupdates.publish(update)
        metadata.resolution = self.resolution #meters per cell 
        metadata.width = self.x_cells # how many cells
        metadata.height = self.y_cells # how many cells 
        originPose = Pose()

        originPose.position.x = self.x_low 
        originPose.position.y = self.y_low
        metadata.origin = originPose


        occupancygrid_data = OccupancyGrid()
        occupancygrid_data.info = metadata
        header =  Header()
        header.frame_id = "map"
        header.stamp = rospy.Time.now()
        self.grid = self.inflate_map(self.grid)
        occupancygrid_data.header = header
        occupancygrid_data.data = list(self.grid.T.reshape(-1).astype(np.int8))
        self.publisher_occupancygrid.publish(occupancygrid_data)

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
        if not self.gotcb:
            self.grid = np.ones((self.x_cells, self.y_cells)) *self.uknownspace_value 



    def run(self):
        while not rospy.is_shutdown():

            self.rate.sleep()


if __name__ == "__main__":
    try:
        rospy.init_node("occupancygrid")
        Occupancygrid()
        rospy.spin()
    except rospy.ROSInternalException:
        pass