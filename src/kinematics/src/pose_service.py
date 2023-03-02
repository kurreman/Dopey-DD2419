#!/usr/bin/env python3
import rospy
from sensor_msgs.msg import JointState
from enum import Enum
from std_srvs.srv import Empty, EmptyResponse, EmptyRequest
from std_msgs.msg import Float64
import numpy as np
from kinematics_utils import RefPoses, JointData
from kinematics.srv import JointAngles, GripStrength
from hiwonder_servo_msgs.msg import CommandDuration


class PoseService:
    """
    Allows for easy publishing of robot poses in joint space, not to be used for inverse kinematics.
    """

    def __init__(self) -> None:
        self.home_service = rospy.Service("home", Empty, self.home_callback)
        self.pickup_service_right = rospy.Service(
            "pickup/right", Empty, self.pickup_r_callback
        )
        self.pickup_service_front = rospy.Service(
            "pickup/front", Empty, self.pickup_f_callback
        )
        self.pickup_service_tray = rospy.Service(
            "pickup/tray", Empty, self.pickup_t_callback
        )
        self.open_gripper_service = rospy.Service(
            "gripper/open", Empty, self.open_gripper_callback
        )
        self.close_gripper_service = rospy.Service(
            "gripper/close", GripStrength, self.close_gripper_callback
        )
        self.pickup_routine_service = rospy.Service(
            "pickup/full", Empty, self.pickup_routine_callback
        )
        self.pose_service = rospy.Service(
            "pose_service", JointAngles, self.pose_service_callback
        )
        self.joint1_pub = rospy.Publisher(
            "/joint1_controller/command_duration", CommandDuration, queue_size=10
        )
        self.joint2_pub = rospy.Publisher(
            "/joint2_controller/command_duration", CommandDuration, queue_size=10
        )
        self.joint3_pub = rospy.Publisher(
            "/joint3_controller/command_duration", CommandDuration, queue_size=10
        )
        self.joint4_pub = rospy.Publisher(
            "/joint4_controller/command_duration", CommandDuration, queue_size=10
        )
        self.joint5_pub = rospy.Publisher(
            "/joint5_controller/command_duration", CommandDuration, queue_size=10
        )
        self.gripper_pub = rospy.Publisher(
            "r_joint_controller/command_duration", CommandDuration, queue_size=10
        )

        self.joint_state_sub = rospy.Subscriber(
            "/joint_states", JointState, self.join_state_callback
        )
        self.cur_joint_state = JointState()

    def pose_service_callback(self, req: JointAngles):
        joint_data = JointData.from_list(req.joints)
        time = req.time
        rospy.loginfo("moving to pose")
        self.publish_data(joint_data, time, len(req.joints) == 6)
        return EmptyResponse()

    def join_state_callback(self, state: JointState):
        self.cur_joint_state = state

    def home_callback(self, req: EmptyRequest) -> EmptyResponse:
        rospy.loginfo("Moving to home position")
        self.publish_data(RefPoses.HOME.value, include_gripper=True)
        return EmptyResponse()

    def pickup_r_callback(self, req: EmptyRequest) -> EmptyResponse:
        rospy.loginfo("Moving to right pickup position")
        self.publish_data(RefPoses.PICKUP_R.value)
        return EmptyResponse()

    def pickup_f_callback(self, req: EmptyRequest) -> EmptyResponse:
        rospy.loginfo("Moving to front pickup position")
        self.publish_data(RefPoses.PICKUP_F.value, include_gripper=True)
        return EmptyResponse()

    def pickup_t_callback(self, req: EmptyRequest) -> EmptyResponse:
        rospy.loginfo("Moving to tray pickup position")
        self.publish_data(RefPoses.PICKUP_TRAY.value)
        return EmptyResponse()

    def pickup_routine_callback(self, req:EmptyRequest) -> EmptyResponse:
        rospy.loginfo("pickup routine started")
        self.publish_data(RefPoses.HOME.value)
        rospy.sleep(2)
        rospy.loginfo("moving to front pickup zone")
        self.publish_data(RefPoses.PREPICK_F.value)
        rospy.sleep(2)
        self.open_gripper_callback(EmptyRequest())
        rospy.sleep(2)
        rospy.loginfo("moving to pick")
        self.publish_data(RefPoses.PICKUP_F.value)
        rospy.sleep(2)
        rospy.loginfo("closing gripper")
        grip_req = GripStrength
        grip_req.strength = "cube"
        self.close_gripper_callback(grip_req)
        rospy.sleep(2)
        rospy.loginfo("going back home")
        self.publish_data(RefPoses.HOME.value)
        rospy.sleep(2)
        return EmptyResponse()



    def publish_data(self, joint_data: JointData, time:int = 2000, include_gripper: bool = False):
        self.joint1_pub.publish(self.to_command_duration(joint_data.joint1, duration=time))
        self.joint2_pub.publish(self.to_command_duration(joint_data.joint2, duration=time))
        self.joint3_pub.publish(self.to_command_duration(joint_data.joint3, duration=time))
        self.joint4_pub.publish(self.to_command_duration(joint_data.joint4, duration=time))
        self.joint5_pub.publish(self.to_command_duration(joint_data.joint5, duration=time))

        if include_gripper:
            self.gripper_pub.publish(self.to_command_duration(joint_data.gripper))
        else:
            self.gripper_pub.publish(
                self.to_command_duration(
                    JointData.from_joint_state(self.cur_joint_state).gripper
                )
            )

    def open_gripper_callback(self, req: EmptyRequest) -> EmptyResponse:
        rospy.loginfo("Opening gripper")
        self.gripper_pub.publish(
            self.to_command_duration(RefPoses.OPEN_GRIPPER.value.gripper, duration=1000)
        )

        return EmptyResponse()

    def close_gripper_callback(self, req: GripStrength) -> EmptyResponse:
        rospy.loginfo("Closing gripper")
        
        if req.strength == "cube":
            self.gripper_pub.publish(
                self.to_command_duration(
                    RefPoses.CLOSE_GRIPPER_CUBE.value.gripper, duration=1000
                )
            )
        
        elif req.strength == "ball":
            self.gripper_pub.publish(
                self.to_command_duration(
                    RefPoses.CLOSE_GRIPPER_BALL.value.gripper, duration=1000
                )
            )       

        elif req.strength == "plush":
            self.gripper_pub.publish(
                self.to_command_duration(
                    RefPoses.CLOSE_GRIPPER_PLUSH.value.gripper, duration=1000
                )
            )
        
        else:
            self.gripper_pub.publish(
                self.to_command_duration(
                    RefPoses.CLOSE_GRIPPER.value.gripper, duration=1000
                )
            )
        return EmptyResponse()

    @staticmethod
    def to_command_duration(position: float, duration: float = 2000) -> CommandDuration:
        command = CommandDuration()
        command.data = position
        command.duration = duration

        return command


if __name__ == "__main__":
    rospy.init_node("pose_server")
    PoseService()
    rospy.spin()