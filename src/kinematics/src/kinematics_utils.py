from enum import Enum
from sensor_msgs.msg import JointState
import numpy as np
from geometry_msgs.msg import Quaternion
from tf.transformations import quaternion_from_matrix, quaternion_slerp
import rospy
from kinematics.srv import JointAnglesRequest

class JointData:
    """
    Class to carry joint data in a more convenient way, without using a ros message
    """

    def __init__(self) -> None:
        self.joint1 = 0
        self.joint2 = 0
        self.joint3 = 0
        self.joint4 = 0
        self.joint5 = 0
        self.gripper = 0

    def __str__(self) -> str:
         
        return    f"""
            joint1 = {self.joint1}
            joint2 = {self.joint2}
            joint3 = {self.joint3}
            joint4 = {self.joint4}
            joint5 = {self.joint5}
            gripper = {self.gripper}
            """

    @staticmethod
    def from_joint_state(state: JointState):
        data = JointData()
        data.joint1 = state.position[0]
        data.joint2 = state.position[1]
        data.joint3 = state.position[2]
        data.joint4 = state.position[3]
        data.joint5 = state.position[4]
        data.gripper = state.position[5]

        return data

    @staticmethod
    def from_np_array(state: np.ndarray, include_gripper: bool = False):
        data = JointData()
        data.joint1 = state[0]
        data.joint2 = state[1]
        data.joint3 = state[2]
        data.joint4 = state[3]
        data.joint5 = state[4]
        if include_gripper:
            data.gripper = state[5]

        return data

    @staticmethod
    def from_list(positions: list):
        data = JointData()
        data.joint1 = positions[0]
        data.joint2 = positions[1]
        data.joint3 = positions[2]
        data.joint4 = positions[3]
        data.joint5 = positions[4]

        try:
            data.gripper = positions[5]
        except:
            pass

        return data

    def to_np_array(self, include_gripper: bool = False):
        if include_gripper:
            return np.array(
                [
                    self.joint1,
                    self.joint2,
                    self.joint3,
                    self.joint4,
                    self.joint5,
                    self.gripper,
                ]
            )
        return np.array(
            [
                self.joint1,
                self.joint2,
                self.joint3,
                self.joint4,
                self.joint5,
            ]
        )
    
    def to_list(self) -> list:
        return [
                    self.joint1,
                    self.joint2,
                    self.joint3,
                    self.joint4,
                    self.joint5,
                    self.gripper,
                ]
            

    def to_joint_state(self):
        joint_state = JointState()
        joint_state.position = [
            self.joint1,
            self.joint2,
            self.joint3,
            self.joint4,
            self.joint5,
            self.gripper,
        ]

        joint_state.name = [
            "joint1",
            "joint2",
            "joint3",
            "joint4",
            "joint5",
            "r_joint"
        ]

        joint_state.header.stamp = rospy.Time.now()
        return joint_state

    def to_joint_angles_req(self, time = 2000) -> JointAnglesRequest:
        joints = self.to_list()
        time = time

        return JointAnglesRequest(joints, time)



class RefPoses(Enum):
    """
    Enum to carry references poses for the robot in joint space:
    - HOME: robot in home position
    - PICKUP_R: robot in position to pick up an object from the right
    - PREPICK_R high view of the right side
    - PICKUP_F: robot in position to pick up an object from the front
    - PREPICK_F: high view of front side
    - PICKUP_TRAY: robot in position to pick up an object from the tray
    - OPEN_GRIPPER: contains open gripper position
    - CLOSE_GRIPPER: contains closed gripper position
        - _CUBE : close the gripper hard enough for the cube
        - _BALL : close the gripper hard enough for the ball
        - _PLUSH : close the gripper hard enough for the plush
    """

    HOME = JointData.from_list(positions=[1.57, 0.91, -1.6, -1.2, 0, 0])
    UNFOLD = JointData.from_list(positions=[0, 0, 0, 0, 0, 0])
    PICKUP_R = JointData.from_list(positions=[0, -1, -0.8, -1.3, 0, -0.2])
    PREPICK_R = JointData.from_list(positions=[0 -0.2, -1.2, -1.75, 0.0, -1.5])
    PICKUP_F = JointData.from_list(positions=[1.57, -0.9, -1.15, -1.1, 0, -1.5])
    PREPICK_F = JointData.from_list(positions=[1.57, -0.4537, -0.9075, -1.797, 0.0, -1.5])
    LOOK_TRAY = JointData.from_list(positions=[-1.57, 0.33, -1.20, -1.88, 0, -0.2])
    PICKUP_TRAY = JointData.from_list(positions=[-1.57, 0.33, -1.20, -1.88, 0, -0.2])
    OPEN_GRIPPER = JointData.from_list(positions=[0, 0, 0, 0, 0, -1.5])
    DROP_POS = JointData.from_list(positions=[1.57, -0.175, -0.785, -1.309, 0,0])
    CLOSE_GRIPPER = JointData.from_list(positions=[0, 0, 0, 0, 0, 0.3])
    CLOSE_GRIPPER_CUBE = JointData.from_list(positions=[0, 0, 0, 0, 0, 0.3])
    CLOSE_GRIPPER_BALL = JointData.from_list(positions=[0, 0, 0, 0, 0, 0.2])
    CLOSE_GRIPPER_PLUSH = JointData.from_list(positions=[0, 0, 0, 0, 0, 0.3])


def ros_quaternion_to_rotation(quaternion: Quaternion):
    return np.array(
        [
            [
                1 - 2 * (quaternion.y**2 + quaternion.z**2),
                2 * (quaternion.x * quaternion.y - quaternion.z * quaternion.w),
                2 * (quaternion.x * quaternion.z + quaternion.y * quaternion.w),
            ],
            [
                2 * (quaternion.x * quaternion.y + quaternion.z * quaternion.w),
                1 - 2 * (quaternion.x**2 + quaternion.z**2),
                2 * (quaternion.y * quaternion.z - quaternion.x * quaternion.w),
            ],
            [
                2 * (quaternion.x * quaternion.z - quaternion.y * quaternion.w),
                2 * (quaternion.y * quaternion.z + quaternion.x * quaternion.w),
                1 - 2 * (quaternion.x**2 + quaternion.y**2),
            ],
        ]
    )


def rotation_to_ros_quaternion(rotation: np.ndarray) -> Quaternion:
    new_r = np.eye(4)
    new_r[:3, :3] = rotation
    return quaternion_from_matrix(new_r)


class Trajectory:
    """
    Interpolating between poses
    """
    def __init__(self, start_point, start_R, end_point, end_R, N=100) -> None:
        self.points = []
        self.orientations = []
        self.N = N
        self.start_point = start_point
        self.start_R = start_R
        self.end_point = end_point
        self.end_R = end_R

    def _gen_trajectory(self, ):
        start_quat = rotation_to_ros_quaternion(self.start_R)
        end_quat = rotation_to_ros_quaternion(self.end_R)

        for i in range(self.N):
            t = i / (self.N - 1)
            point = (1 - t) * self.start_point + t * self.end_point
            npquat = quaternion_slerp(start_quat, end_quat, t)
            quat = Quaternion(npquat[0], npquat[1], npquat[2], npquat[3])
            R = ros_quaternion_to_rotation(quat)

            yield point, R
    
