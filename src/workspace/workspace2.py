#!/usr/bin/env python3
import rospy
from geometry_msgs.msg import PolygonStamped, Point32, PoseStamped, Pose
from nav_msgs.msg import Odometry
from robp_msgs.msg import DutyCycles
import tf2_ros
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from workspace.srv import PolyCheck, PolyCheckRequest, OccupancyCheck, OccupancyCheckRequest
from nav_msgs.msg import MapMetaData
import matplotlib.path as mplPath

class Workspace():
    def __init__(self):
        self.verbose = 0
        self.f = 10
        self.rate = rospy.Rate(self.f)
        self.robot_position = None
        self.navgoal_position = None
        self.navgoal = PoseStamped() #does that work?
        # self.publisher_dutycycle = rospy.Publisher("/motor/duty_cycles", DutyCycles, queue_size=10)
        self.publisher_vertices = rospy.Publisher("workspace", PolygonStamped, queue_size=10)
        self.subscriber_robopos = rospy.Subscriber("/odometry", Odometry, self.odom_callback)
        self.frame_id = "map"

        # self.vertices_df = pd.read_csv("~/dd2419_ws/src/workspace/example_workspace.tsv", sep="\t")
        # self.vertices_df = pd.read_csv("/home/dopey/dd2419_ws/src/workspace/QCaveWorkspace.tsv", sep="\t")
        self.vertices_df = pd.read_csv("/home/dopey/dd2419_ws/src/workspace/battery_workspace.tsv", sep="\t")
        # self.vertices_df = pd.read_csv("src/workspace/example_workspace.tsv", sep="\t")


        self.vertices = self.vertices_df.values
        self.vertices_list = np.append(self.vertices, [self.vertices[0]], axis = 0)
        self.puffer = 1 #add a medeter

        self.x_low = min(self.vertices_list, key=lambda point: point[0])[0] - self.puffer
        self.x_high = max(self.vertices_list, key=lambda point: point[0])[0] + self.puffer
        self.y_low = min(self.vertices_list, key=lambda point: point[1])[1] - self.puffer
        self.y_high = max(self.vertices_list, key=lambda point: point[1])[1] + self.puffer
        self.vertices_extrema = [self.x_low, self.x_high, self.y_low, self.y_high]
        self.resolution = 0.025 # m per cell 
        self.uknownspace_value = -1
        self.occupied_value = 1
        self.x_cells = int((self.x_high - self.x_low) /self.resolution) #cells / m
        self.y_cells = int((self.y_high - self.y_low) /self.resolution) #cells / m
        self.occupancy_grid = np.ones((self.x_cells, self.y_cells)) *self.uknownspace_value 



        self.subscriber_navgoal = rospy.Subscriber("move_base_simple/goal", PoseStamped, self.navgoal_callback)
        self.publisher_goal = rospy.Publisher('move_base_simple/goal', PoseStamped, queue_size=10)
        self.robo_posestamped = Odometry()
        self.polygon_service = rospy.Service("/polygon_service", PolyCheck, self.callback_polycheck)
        self.occupancy_service = rospy.Service("/occupancy_service", OccupancyCheck, self.callback_occupancycheck)
        self.robot_inside = True #will approach
        self.navgoal_inside = True #will aproach
        self.pinf = [10000, 10000] #point can be anywhere
        

        self.navgoalnew = False
        self.run()

    def get_x_pos(self, i):
        step = (self.x_high - self.x_low) / self.x_cells
        x_pos = (
            self.x_low + step * i + step / 2
        ) 
        return x_pos

    def get_y_pos(self, j):
        step = (self.y_high - self.y_low) / self.y_cells
        y_pos = (
            self.y_low + step * j + step / 2
        )  # added step/2 so that the coordinate is in the middle of the cells
        return y_pos
    

    def navgoal_callback(self, navgoalmsg):
        self.navgoal = PoseStamped()
        self.navgoal.pose = navgoalmsg.pose
        self.navgoal.header = navgoalmsg.header
        self.navgoal.header.frame_id = "odom"
        self.navgoal_position = [self.navgoal.pose.position.x, self.navgoal.pose.position.y]

    def odom_callback(self, msg):
        self.robo_posestamped = msg
        self.robot_position = [msg.pose.pose.position.x, msg.pose.pose.position.y]
        
    def direction(self, A, B, C):
        # find the orientation of 3 points
        # 0 : collinear points
        # 1 : clockwise 
        # 2 : counterclockwise 
        dir = (B[1]- A[1])*(C[0] - B[0]) - (B[0]-A[0])*(C[1]-B[1])
        # dir = (C[1] - A[1])*(B[0] - A[0]) - (B[1]- A[1])* (C[0]- A[0])
        # if self.verbose: 
        #     print(f"Given Orientation value:{dir}")
        if dir == 0:
            #collinear 
            if self.verbose:
                print(f"{A}, {B}, {C}: collinear, given orientation value: {dir}")
            return 0
        elif dir > 0:
            #clockwise
            if self.verbose:
                print(f"{A}, {B}, {C}: clockwise, given orientation value: {dir}") 
            return 1
        else:
            if self.verbose:
                print(f"{A}, {B}, {C}: anticlockwise, given orientation value: {dir}")
            return 2
    
    def checkonline(self, p1, p2, p3):
        # given collinear points p1, p2, p3, check if p2, lies on line segment p1p3
        if ((p2[0] <= max(p1[0], p3[0])) and (p2[0] >= min(p1[0], p3[0])) and
            (p2[1] <= max(p1[1], p3[1])) and (p2[1] >= min(p1[1], p3[1]))):
            if self.verbose:
                print(f"given collinear points: p2={p2} lies on p1= {p1} and p3= {p3}")
            return True
        return False

    def checkintersection(self, A, B, C, D):
        if self.verbose:
            print("Intersection exists")
        #ABCD points [x,y]
        #AB on line 1, CD on line 2
        # True if intersect
        d1 = self.direction(A, B, C)
        d2 = self.direction(A, B, D)
        d3 = self.direction(C, D, A)
        d4 = self.direction(C, D, B)

        if d1 != d2 and d3 != d4:
            if self.verbose:
                print(f"Intersection Reason: Different orientations for {A}, {B}, {C} and {A}, {B}, {D} || {C}, {D}, {A} and {C}, {D}, {B}")
            # different orientations imply intersection
            return True
        if d1 == 0 and self.checkonline(A, B, C):
            # A, B, C collinear and B lies on segment AC
            if self.verbose:
                print(f"Intersection Reason: {A}, {B}, {C} collinear and {B} lies on {A}-{C} segement")
            return True
        if d2 == 0 and self.checkonline(A, B, D):
            if self.verbose:
                print(f"Intersection Reason: {A}, {B}, {D} collinear and {B} lies on {A}-{D} segement")
            return True
        if d3 == 0 and self.checkonline(C, D, A):
            if self.verbose:
                print(f"Intersection Reason: {C}, {D}, {A} collinear and {C} lies on {D}-{A} segement")
            return True
        if d4 == 0 and self.checkonline(C, D, B):
            if self.verbose:
                print(f"Intersection Reason: {C}, {D}, {B} collinear and {C} lies on {D}-{B} segement")
            return True
        # return False if none of the cases are true
        return False
         
    def checkpointinsidepoly(self, point_interest, point_infinity):
        # return 1 if inside polygon
        n_edges = len(self.vertices)
        point_infinity[1] = point_interest[1] #same height
        if self.verbose:
            print("\n\n") 
            print(f"vertices: {self.vertices}")
            print(f"number of edges: {n_edges}")
        if n_edges < 3:
            return False
        i = 0
        count = 0
        if self.verbose:
            print(f"Current position of robot:{point_interest}")
        while True:
            #find point of edge of polygon
            edge1 = self.vertices[i]
            edge2 = self.vertices[i + 1]
            if self.verbose:
                print(f"edge{i}:", edge1)
                print(f"edge{i+1}:", edge2)
                
            if self.checkintersection(edge1, edge2, point_interest, point_infinity):
                #if the point is on the edge then its definitely inside aka return True
                if self.direction(edge1, point_interest, edge2) == 0:
                    return self.checkonline(point_interest, edge1, edge2)
                count += 1
                if self.verbose:
                    print("intersection count:", count)
            else:
                if self.verbose:
                    print("No intersection")

            i = (i+1) % (n_edges-1)
            if self.verbose:
                print("new i:", i)
            if i == 0:
                #break if it exceeds the edge count
                break
            # return 1 if odd number of intersection => inside
            # return 0 if even number of intersections => outside 
        return count % 2

    def checkpointinsidepoly2(self, point_interest):
        #returns true if inside map
        poly_path = mplPath.Path((self.vertices_list))
        bool_poly = poly_path.contains_point(point_interest)
        return bool_poly


    def polygon(self):
        point_list = []
        xs, ys = zip(*self.vertices_list)
        for vertice in self.vertices_list:
            point_type = Point32()
            point_type.x = vertice[0]
            point_type.y = vertice[1]
            point_list.append(point_type)
        return point_list

    def callback_polycheck(self, req:PolyCheckRequest):
        #points need to be in continuous space
        p_check = list(req.point_of_interest)
        return self.checkpointinsidepoly2(p_check)
    
    def callback_occupancycheck(self, req:OccupancyCheckRequest):
        # for x in range(self.x_cells):
        #     for y in range(self.y_cells):
        #         point_of_interest = [self.get_x_pos(x), self.get_y_pos(y)]
        #         bool_poly = self.checkpointinsidepoly(point_of_interest, self.pinf)
        #         if not bool_poly:
        #             self.occupancy_grid[x, y] = self.occupied_value
        points = [((self.get_x_pos(x), self.get_y_pos(y)), (x,y)) for x in range(self.x_cells) for y in range(self.y_cells)]
        
        for point_float, point_int in points:
            poly_bool = self.checkpointinsidepoly2(point_float)
            if not poly_bool:
                x = point_int[0]
                y = point_int[1]
                self.occupancy_grid[x, y] = self.occupied_value
        occupancy_array = list(self.occupancy_grid.reshape(-1).astype(np.int64))
        occupancy_metadata = MapMetaData()
        occupancy_metadata.resolution = self.resolution
        occupancy_metadata.width = self.x_cells
        occupancy_metadata.height = self.y_cells
        return occupancy_array, occupancy_metadata, self.vertices_extrema

    def run(self):
        while not rospy.is_shutdown():
            # Pose Stamped Publisher
            poly_points = PolygonStamped()
            point_list = self.polygon()
            poly_points.polygon.points = point_list
            poly_points.header.frame_id = self.frame_id
            self.publisher_vertices.publish(poly_points)

            ################################################# TESTING CHECKPOINTINSIDEPOLY ALG ######################################
            # x = [self.get_x_pos(x) for x in range(self.x_cells)]
            # y = [self.get_y_pos(y) for y in range(self.y_cells)]
            # # points = list(zip(x, y))
            # points = [(self.get_x_pos(x), self.get_y_pos(y)) for x in range(self.x_cells) for y in range(self.y_cells)]

            # wrong_points = []
            # occupied_points = []
            # for point in points:
            #     poly_bool = self.checkpointinsidepoly2(point) 
            #     alice_bool = self.checkpointinsidepoly([point[0], point[1]], self.pinf)
            #     if poly_bool !=  alice_bool:
            #         # print(f"WARNING: POI: {point} DIFFERENT RESULT")
            #         wrong_points.append(point)
            #     if poly_bool is not True:
            #         occupied_points.append(point)
            # # print(wrong_points)
            # plt.plot([i for i, j in occupied_points], [j for i, j in occupied_points], ".")
            # # plt.plot([i for i, j in wrong_points], [j for i, j in wrong_points], "r.")c
            # plt.show()
            #########################################################################################################################


            ## CHECK
            if self.verbose:
                rospy.loginfo(f"robot position:{self.robot_position} navgoal position:{self.navgoal_position}")
            if self.robot_position is not None  and self.navgoal_position is not None:
                self.robot_inside = self.checkpointinsidepoly(self.robot_position, self.pinf) #check robot position before boolean
                if self.robot_inside:
                    if self.verbose:
                        rospy.loginfo("Robot Inside True")
                    #Robot inside poly
                    self.navgoal_inside = self.checkpointinsidepoly(self.navgoal_position, self.pinf) #check navgoal before boolean 
                    if not self.navgoal_inside:
                        #Navgoal outside poly
                        ########### METHOD ONE:: PUBLISH POSITION OF ROBOT AS NEW NAVGOAL ############################
                        posestamped_message = PoseStamped()
                        posestamped_message.pose = self.robo_posestamped.pose.pose
                        posestamped_message.header = self.robo_posestamped.header
                        posestamped_message.header.frame_id = "odom"
                        self.publisher_goal.publish(posestamped_message)
                        rospy.loginfo("Navgoal outside workspace: New Navgoal generated.")

                        ########### METHOD TWO:: PUBLISH POSITION OF ROBOT AS NEW NAVGOAL ############################
            self.rate.sleep()


if __name__ == '__main__': 
    try:
        rospy.init_node("workspace")
        Workspace()
        rospy.spin()
    except rospy.ROSInternalException:
        pass

