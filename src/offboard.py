#!/usr/bin/env python

import rospy
from mavros_msgs.srv import SetMode, SetModeResponse, CommandBool
from mavros_msgs.msg import State
from geometry_msgs.msg import PoseStamped
from geometry_msgs.msg import Twist, Vector3


def state_cb(state):
    global current_state
    current_state = state

def pose_cb(pose):
    global desiredPose
    desiredPose = pose


if __name__ == '__main__':
    try:

        current_state = State()
        desiredPose = PoseStamped()
    
        rospy.init_node('offboard_setter', anonymous=True)
        
        # define topics
        state_sub = rospy.Subscriber('mavros/state', State, state_cb)
        pose_sub = rospy.Subscriber('pilot/pose', PoseStamped, pose_cb)
        rospy.wait_for_service('mavros/set_mode')
        rospy.wait_for_service('mavros/cmd/arming')
        local_pos_pub = rospy.Publisher('mavros/setpoint_position/local', PoseStamped, queue_size=10)
        twist_pub = rospy.Publisher('mavros/setpoint_velocity/cmd_vel_unstamped', Twist, queue_size=1)

        
        rate = rospy.Rate(20)

        while not current_state.connected:
            rate.sleep()
        

        desiredPose.pose.position.x = 10
        desiredPose.pose.position.y = 0
        desiredPose.pose.position.z = 5

        linear = Vector3(0,0,0)
        angular = Vector3(0,0,0)
        twist = Twist(linear, angular)

        for i in range(1,50):
            local_pos_pub.publish(desiredPose)
            print("pose sent")
            rate.sleep()

        set_mode_client = rospy.ServiceProxy('mavros/set_mode', SetMode)
        response_setmode = set_mode_client.call(0, "OFFBOARD")
        #response_setmode = set_mode_client(mode)
        print(response_setmode)
        print("offboard")
    
        arming_client = rospy.ServiceProxy('mavros/cmd/arming', CommandBool)
        response_arming = arming_client.call(True)
        #response_arming = arming_client(True)
        print(response_arming)
        print("armed")

        last_request = rospy.Time.now()
        count = 0

        while not rospy.is_shutdown():

            timeExceeded = rospy.get_rostime() - last_request > rospy.Duration(5)
            if current_state.mode != "OFFBOARD" and timeExceeded:
                response_setmode = set_mode_client.call(0, "OFFBOARD")
                last_request = rospy.Time.now()

            else:
                if not current_state.armed and timeExceeded:
                    response_arming = arming_client.call(True)
                    last_request = rospy.Time.now()
            
            if count<100:
                local_pos_pub.publish(desiredPose)
            else:
                local_pos_pub.publish(desiredPose)
                #twist_pub.publish(twist)
            
            if count == 200:
                print("Fin pose")    
            count += 1
            rate.sleep()

    except rospy.ROSInterruptException:
        print("ROS Interruption exception")
        pass

"""
Interesante este codigo para tomar ejemplos como llamar a los servicios, y si fallan devolver el estado; o las funciones de wait_for_landed y asi:
https://github.com/PX4/Firmware/blob/d2aa68f62c5e131f2cf4223cefdc6e1e29bbb5da/integrationtests/python_src/px4_it/mavros/mavros_test_common.py
"""