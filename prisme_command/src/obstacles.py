#!/usr/bin/env python
"""
Exploration node
ROS node for an exploration robot running in simulation using V-REP.
"""

import rospy
import message_filters
import random
import time
from sensor_msgs.msg import Range
from geometry_msgs.msg import Twist, Vector3
from math import pow

__author__ = "Karl Kangur"
__email__ = "karl.kangur@gmail.com"

max_distance = 0.05

def process_ir_front(ir_left, ir_left_center, ir_right_center, ir_right):
    """Do obstacle avoidance."""
    distances = [ir_left.range, ir_left_center.range, ir_right_center.range, ir_right.range]
    weights = [(max_distance - distances[i]) for i in range(len(distances))]
    
    base_lin_speed = 0.12
    base_ang_speed = 0.4
    
    alpha = 0.5
    k_linear = 500
    k_angular = 50
    
    delta = (1-alpha)*(weights[3]-weights[0]) + alpha*(weights[2]-weights[1])
    
    v_linear = base_lin_speed / (1 + pow(k_linear*abs(delta),2))
    v_angular = base_ang_speed * k_angular * delta
    
    rospy.loginfo("Distances: %f %f %f %f", distances[0], distances[1], distances[2], distances[3])
    rospy.loginfo("Weights: %f %f %f %f", weights[0], weights[1], weights[2], weights[3])
    rospy.loginfo("Delta: %f,\tv_lin: %f, \tv_ang: %f", delta, v_linear, v_angular)
    
    if not rospy.is_shutdown():
        set_speed(v_linear, v_angular)


def set_speed(linear, angular):
    # Set robot speed with a Twist topic
    msg = Twist()
    msg.linear = Vector3()
    msg.linear.x = linear
    msg.linear.y = 0.0
    msg.linear.z = 0.0
    msg.angular = Vector3()
    msg.angular.x = 0.0
    msg.angular.y = 0.0
    msg.angular.z = angular

    # Actually publish the topic
    pub.publish(msg)


def stop_robot():
    rospy.loginfo("Stopping robot")
    set_speed(0, 0)


def initialize():
    """Initialize the sample node."""
    global pub
    namespace = "/prisme/"
    controller = "vel_controller/"

    # Provide a name for the node
    rospy.init_node("explore", anonymous=True)

    # Give some feedback in the terminal
    rospy.loginfo("Exploration node initialization")

    # Subscribe to and synchronise the infra-red sensors in front of the robot
    ir_front_left = message_filters.Subscriber(namespace+"ir_front_left", Range)
    ir_front_right = message_filters.Subscriber(namespace+"ir_front_right", Range)
    ir_front_left_center = message_filters.Subscriber(
        namespace+"ir_front_left_center", Range)
    ir_front_right_center = message_filters.Subscriber(
        namespace+"ir_front_right_center", Range)
    # Wait for all topics to arrive before calling the callback
    ts_ir_front = message_filters.TimeSynchronizer([
        ir_front_left,
        ir_front_left_center,
        ir_front_right_center,
        ir_front_right], 1)
    # Register the callback to be called when all sensor readings are ready
    ts_ir_front.registerCallback(process_ir_front)

    # Publish the linear and angular velocities so the robot can move
    pub = rospy.Publisher(namespace+controller+"cmd_vel", Twist, queue_size=1)

    # Register the callback for when the node is stopped
    rospy.on_shutdown(stop_robot)

    # spin() keeps python from exiting until this node is stopped
    rospy.spin()

if __name__ == "__main__":
    initialize()
