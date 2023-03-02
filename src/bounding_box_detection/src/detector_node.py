#!/usr/bin/env python3

from typing import List
import rospy
import torch
from detector import Detector
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import cv2
from PIL import Image as PILImage
import numpy as np
import utils
import os
import time
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:512"
torch.cuda.set_per_process_memory_fraction(0.8, 0)
torch.cuda.empty_cache()
class BoundingBoxNode:
    def __init__(self) -> None:
        self.f = 60
        self.rate = rospy.Rate(self.f)

        self.camera_topic = "/camera/color/image_raw"
        self.out_image_topic = "/camera/color/image_bbs"
        self.depth_topic = "/camera/aligned_depth_to_color/image_raw"
        self.camera_info_topic = "/camera/aligned_depth_to_color/camera_info"
        self.model_path = "/home/robot/dd2419_ws/src/bounding_box_detection/src/det_2023-03-02_14-23-34-390133.pt"
        
        self.image_subscriber = rospy.Subscriber(self.camera_topic, Image, self.image_callback)
        self.depth_subscriber = rospy.Subscriber(self.depth_topic, Image, self.depth_callback)
        self.image_publisher = rospy.Publisher(self.out_image_topic, Image, queue_size=10)
        self.bridge = CvBridge()
        
        self.ros_img = None
        self.ros_depth = None
        self.image = None
        self.array_image = None
        self.depth = None
        self.array_depth = None
        self.camera_info = rospy.wait_for_message(self.camera_info_topic, CameraInfo, rospy.Duration(5))
        self.K = np.array(self.camera_info.K).reshape(3,3)

        self.verbose = False
        # self.model = Detector()
        self.model= torch.load(self.model_path)
        self.model.eval()
        self.cuda = torch.cuda.is_available()
        
        if self.cuda:
            self.model.cuda()


        self.run()

    def image_callback(self, msg):
        self.ros_img = msg
        image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
        self.image = PILImage.fromarray(image)
        self.array_image = np.asarray(image)
    
    def depth_callback(self, msg):
        self.ros_depth = msg
        depth = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
        self.depth = PILImage.fromarray(depth)
        self.array_depth = np.asarray(depth)


    
    def predict(self, image) -> List[utils.BoundingBox]:
        torch_image, _ = self.model.input_transform(image, [], validation=True)
        if self.cuda:
            torch_image = torch_image.to("cuda")
        out = self.model(torch_image.unsqueeze(0)).cpu()
        bbs = self.model.decode_output(out, 0.5, scale_bb=True)[0]
        return bbs
    
    def show_bbs_in_image(self, bbs: List[utils.BoundingBox], image) -> None:
        if len(bbs) >0:
            image = utils.draw_bb_on_image(image, bbs, utils.CLASS_DICT)
            ros_img = self.bridge.cv2_to_imgmsg(image,  encoding="passthrough")
            self.image_publisher.publish(ros_img)
        else:
            self.image_publisher.publish(self.ros_img)

    def run(self):
        while not rospy.is_shutdown():
            if self.image is not None:
                if self.verbose:
                    start = time.time()
                bbs = self.predict(self.image.copy())
                #supress multiple bbs
                bbs = utils.non_max_suppresion(bbs, confidence_threshold=0.80, diff_class_thresh=0.75)
                #add bbs to image and publish
                self.show_bbs_in_image(bbs, self.array_image)

                if self.verbose:
                    rospy.loginfo(f"full inference time = {time.time() - start}")
            
            if self.depth is not None and self.K is not None:
                rospy.loginfo(f"K = {self.K}")
                
            
            self.rate.sleep()
        

if __name__ == "__main__":
    rospy.init_node("bbdetector")
    BoundingBoxNode()
    rospy.spin()