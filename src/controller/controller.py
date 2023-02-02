#!/usr/bin/env python3
import rospy
from geometry_msgs.msg import Twist
from robp_msgs.msg import DutyCycles, Encoders
import math
import numpy as np


class CartesianController:
    def __init__(self, twist_topic: str = "/motor_controller/twist", verbose=False):
        self.duty_pub = rospy.Publisher("/motor/duty_cycles", DutyCycles, queue_size=10)
        self.encoder_sub = rospy.Subscriber(
            "/motor/encoders", Encoders, self.encoder_callback
        )
        self.twist_sub = rospy.Subscriber(twist_topic, Twist, self.twist_callback)

        self.f = 10
        self.b = 0.3
        self.r = 0.04921
        self.ticks_per_rev = 3072

        self.twist = Twist()
        self.encoders = Encoders()

        self.int_error_left = 0
        self.int_error_right = 0
        self.P_left = 0.01
        self.I_left = 0.02
        self.P_right = 0.01
        self.I_right = 0.02

        self.verbose = verbose

        rospy.init_node("cartesian_controller", anonymous=True)
        rospy.loginfo("Cartesian controller started")

        self.rate = rospy.Rate(self.f)
        self.run()

    def run(self):
        while not rospy.is_shutdown():
            desired_w = self.twist.angular.z
            desired_v = self.twist.linear.x

            w_left, w_right = self.translate_encoders()

            desired_w_left = (self.b * desired_w + desired_v) / self.r
            desired_w_right = (-self.b * desired_w + desired_v) / self.r

            error_left = desired_w_left - w_left
            error_right = desired_w_right - w_right

            if self.verbose:
                rospy.loginfo(
                    "current error: {} and {}".format(error_left, error_right)
                )

            self.int_error_left += error_left * (1 / self.f)
            self.int_error_right += error_right * (1 / self.f)

            left_command = self.P_left * error_left + self.I_left * self.int_error_left
            right_command = (
                self.P_right * error_right + self.I_right * self.int_error_right
            )

            duty_left = np.clip(left_command, -1, 1)
            duty_right = np.clip(right_command, -1, 1)

            msg = DutyCycles()
            msg.duty_cycle_left = duty_left
            msg.duty_cycle_right = duty_right
            self.duty_pub.publish(msg)

            self.rate.sleep()

    def translate_encoders(self):

        w_left = (
            2 * math.pi * self.f * self.encoders.delta_encoder_left
        ) / self.ticks_per_rev
        w_right = (
            2 * math.pi * self.f * self.encoders.delta_encoder_right
        ) / self.ticks_per_rev

        return w_left, w_right

    def encoder_callback(self, data):
        if self.verbose:
            rospy.loginfo("Encoder callback")
        self.encoders = data

        if self.verbose:

            rospy.loginfo(
                "Encoders received: {} and {}".format(
                    self.encoders.delta_encoder_left, self.encoders.delta_encoder_right
                )
            )

    def twist_callback(self, data):
        if self.verbose:
            rospy.loginfo("Twist callback")

        self.twist = data

        if self.verbose:
            rospy.loginfo("Twist received: {}".format(self.twist.linear.x))


if __name__ == "__main__":
    rospy.init_node("cartesian_controller", anonymous=True)
    controller = CartesianController("/motor_controller/twist")
    rospy.spin()