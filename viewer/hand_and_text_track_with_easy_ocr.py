#------------------------------------------------------------------------------
# This script receives video from the HoloLens front RGB camera and plays it.
# The camera supports various resolutions and framerates. See
# https://github.com/jdibenes/hl2ss/blob/main/etc/pv_configurations.txt
# for a list of supported formats. The default configuration is 1080p 30 FPS. 
# The stream supports three operating modes: 0) video, 1) video + camera pose, 
# 2) query calibration (single transfer).
# Press esc to stop.
#------------------------------------------------------------------------------

from pynput import keyboard

import cv2
import hl2ss_imshow
import hl2ss
import configparser
import sys
sys.path.append("./HandMovementTracking/")
import numpy as np

from collections import deque
import mediapipe as mp
from utils.utils_v2 import get_idx_to_coordinates, rescale_frame

mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands


# Settings --------------------------------------------------------------------
config = configparser.ConfigParser()
config.read('config.ini')
# HoloLens address
host = config['DEFAULT']['ip']

# Port
port = hl2ss.StreamPort.PERSONAL_VIDEO

# Operating mode
# 0: video
# 1: video + camera pose
# 2: query calibration (single transfer)
mode = hl2ss.StreamMode.MODE_1

# Camera parameters
width     = 640
#crop_img = img[y:y+h, x:x+w]
height    = 360
framerate = 15

# Video encoding profile
profile = hl2ss.VideoProfile.H264_BASE

# Encoded stream average bits per second
# Must be > 0
bitrate = hl2ss.get_video_codec_bitrate(width, height, framerate, hl2ss.get_video_codec_default_factor(profile))

# Decoded format
# Options include:
# 'bgr24'
# 'rgb24'
# 'bgra'
# 'rgba'
# 'gray8'
decoded_format = 'bgr24'

#------------------------------------------------------------------------------

def crop_image(img, px, py, w, h):
    x1 = max(px - int(w), 0)
    y1 = max(py - (int(h*2)), 0)
    x2 = min(px + int(w), img.shape[1])
    y2 = min(py, img.shape[0])
    
    crop_img = img[y1:y2, x1:x2]
    return crop_img

hl2ss.start_subsystem_pv(host, port)

if (mode == hl2ss.StreamMode.MODE_2):
    data = hl2ss.download_calibration_pv(host, port, width, height, framerate)
    print('Calibration')
    print(f'Focal length: {data.focal_length}')
    print(f'Principal point: {data.principal_point}')
    print(f'Radial distortion: {data.radial_distortion}')
    print(f'Tangential distortion: {data.tangential_distortion}')
    print('Projection')
    print(data.projection)
    print('Intrinsics')
    print(data.intrinsics)
else:
    enable = True

    def on_press(key):
        global enable
        enable = key != keyboard.Key.esc
        return enable

    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    client = hl2ss.rx_decoded_pv(host, port, hl2ss.ChunkSize.PERSONAL_VIDEO, mode, width, height, framerate, profile, bitrate, decoded_format)
    client.open()
    hands = mp_hands.Hands(
        min_detection_confidence=0.7, min_tracking_confidence=0.7)
    hand_landmark_drawing_spec = mp_drawing.DrawingSpec(thickness=5, circle_radius=5)
    #hand_connection_drawing_spec = mp_drawing.DrawingSpec(thickness=10, circle_radius=10) 
    #pts = deque(maxlen=64)
    
    while (enable):
        data = client.get_next_packet()

        #print(f'Pose at time {data.timestamp}')
        #print(data.pose)
        #print(f'Focal length: {data.payload.focal_length}')
        #print(f'Principal point: {data.payload.principal_point}')
        
   
        idx_to_coordinates = {}
        image = data.payload.image 
        #image = rescale_frame(image, percent=50)
        #mage = cv2.flip(image, 1)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results_hand = hands.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        if results_hand.multi_hand_landmarks:
            for hand_landmarks in results_hand.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    image=image,
                    landmark_list=hand_landmarks,
                    #connections=mp_hands.HAND_CONNECTIONS,
                    landmark_drawing_spec=hand_landmark_drawing_spec,
                    #connection_drawing_spec=hand_connection_drawing_spec
                    )
                idx_to_coordinates = get_idx_to_coordinates(image, results_hand)
        if 8 in idx_to_coordinates:
            print(idx_to_coordinates[8])
            #pts.appendleft(idx_to_coordinates[8])  # Index Finger
        #for i in range(1, len(pts)):
        #    if pts[i - 1] is None or pts[i] is None:
        #        continue
        #    thick = int(np.sqrt(len(pts) / float(i + 1)) * 4.5)
        #   cv2.line(image, pts[i - 1], pts[i], (0, 255, 0), thick)
            image = crop_image(image, idx_to_coordinates[8][0], idx_to_coordinates[8][1], 35, 17)
            cv2.imshow("Res", image)
            
        if cv2.waitKey(5) & 0xFF == 27:
            break
    #hands.close()
    
        #cv2.imshow('Video', data.payload.image)
        #cv2.waitKey(1)
    hands.close()
    client.close()
    listener.join()

hl2ss.stop_subsystem_pv(host, port)
