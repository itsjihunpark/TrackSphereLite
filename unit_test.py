import unittest
import sys
import json
import os
import cv2
from datetime import datetime

sys.path.insert(1, r'/home/j-p/working/TrackSphereLite/trackSphereLite')
sys.path.insert(1, r'/home/j-p/working/TrackSphereLite/util')
from model.BinocularCamera import BinocularCamera
from model.ObjectDetector import ObjectDetector
from model.FrameProducer import ReplayFrameProducer, MotionFileredFrameProducer
from model.Golfball import FlightedGolfball, RollingGolfball
from BetterPyUnitFormat import BetterPyUnitTestRunner

class TestModelComponents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("setting up classes")
        f = open("./bvts_config/config.json")  
        cls._config = json.load(f)

        cls._binocular_camera = BinocularCamera(config=cls._config)
        cls._binocular_camera.stop_camera_pair()
        cls._binocular_camera.setup_camera(mode="fullframe")
        cls._binocular_camera.start_camera_pair()

        cls._object_detector = ObjectDetector(config=cls._config)
        

    @classmethod
    def tearDownClass(cls):
        print("tearing down classes")
        del cls._object_detector
        del cls._binocular_camera


    def test_binocular_camera_sensor_readings(self):
        """Unit test ID 1: Testing that images are being read from the camera sensors'"""
        frame_left, frame_right, ts_left, ts_right = next(self._binocular_camera)
        self.assertEqual(len(frame_left.shape),3) # testing image obtained is a 3 dim array (width, height, rgb value)
        self.assertEqual(len(frame_right.shape),3) # testing image obtained is a 3 dim array (width, height, rgb value)


    def test_binocular_camera_sensor_synchronisation_10000nsec(self):   
        """Unit test ID 2: Testing that images are being read approximately at the same moment: fail if more than 10,000 nsec difference'"""
        for i in range (1, 50):
            frame_left, frame_right, ts_left, ts_right = next(self._binocular_camera) 
        delta = 10000 # 10000 nsec (10 usec) difference threshold
        msg = f"sync delta: {abs(ts_left-ts_right)}"
        self.assertAlmostEqual(ts_left,ts_right, None, msg, delta)
    

    def test_binocular_camera_sensor_synchronisation_20000nsec(self):   
        """Unit test ID 3: Testing that images are being read approximately at the same moment: fail if more than 20,000 nsec difference'"""
        for i in range (1, 50):
            frame_left, frame_right, ts_left, ts_right = next(self._binocular_camera) 
        delta = 20000 # 20000 nsec (20 usec) difference threshold
        msg = f"sync delta: {abs(ts_left-ts_right)}"
        self.assertAlmostEqual(ts_left,ts_right, None, msg, delta)


    def test_binocular_camera_video_recording(self):
        """Unit test ID 4: Testing that video is being recorded and timestamps are being extracted'"""
        dest_sink, dest_source, dest_sink_ts, dest_source_ts = self._binocular_camera.record_synchronised_video()
        dir_len = len(os.listdir(self._config['temporary_video_record_directory']))
        os.remove(dest_sink)
        os.remove(dest_source)
        os.remove(dest_sink_ts)
        os.remove(dest_source_ts)
        self.assertEqual(dir_len, 4)


    def test_object_detector_with_test_image(self):
        """Unit test ID 5: Testing object detector class on test images'"""
        results = self._object_detector.model.val(data="./test_data/golfball_dataset_test.yaml")
        precision = results.box.map # mean Average Precision across multiple IoU thresholds from 0.5 to 0.95
        self.assertGreater(precision, 0.9)
    

    def test_replay_frame_producer(self):
        """Unit test ID 6: Testing replay frame producer is returning pairs of images and timestamps'"""
        
        dest_sink, dest_source, dest_sink_ts, dest_source_ts = self._binocular_camera.record_synchronised_video()
        right_video_producer = cv2.VideoCapture(dest_sink)
        left_video_producer = cv2.VideoCapture(dest_source)

        right_pts =open(dest_sink_ts, "r")
        left_pts = open(dest_source_ts, "r")

        producer = ReplayFrameProducer(left_video_producer, right_video_producer, left_pts, right_pts, 0, self._binocular_camera)
        frame_left, frame_right, ts_left, ts_right = next(producer)

        os.remove(dest_sink)
        os.remove(dest_source)
        os.remove(dest_sink_ts)
        os.remove(dest_source_ts)        

        self.assertEqual(len(frame_left.shape),3) # testing image obtained is a 3 dim array (width, height, rgb value)
        self.assertEqual(len(frame_right.shape),3) # testing image obtained is a 3 dim array (width, height, rgb value)
        self.assertIsNotNone(ts_left)
        self.assertIsNotNone(ts_right)

    
    def test_motion_filtered_frame_producer(self):
        """Unit test ID 7: Testing that motion filtered frame producer returns fewer frames than replay frame producer'"""
        dest_sink, dest_source, dest_sink_ts, dest_source_ts = self._binocular_camera.record_synchronised_video()

        right_video_producer = cv2.VideoCapture(dest_sink)
        left_video_producer = cv2.VideoCapture(dest_source)

        right_pts =open(dest_sink_ts, "r")
        left_pts = open(dest_source_ts, "r")

        producer = ReplayFrameProducer(left_video_producer, right_video_producer, left_pts, right_pts, 0, self._binocular_camera)
        non_filtered_frames_counter = 0
        for frame_left, frame_right, ts_left, ts_right in producer:
            non_filtered_frames_counter+=1
        
        non_filtered_producer = MotionFileredFrameProducer(producer, self._binocular_camera.roi, self._binocular_camera.motion_threshold, release_n_frames=10)
        filtered_frames_counter = 0
        for frame_left, frame_right, ts_left, ts_right, filter_flag in non_filtered_producer:
            if filter_flag:
                filtered_frames_counter+=1

        os.remove(dest_sink)
        os.remove(dest_source)
        os.remove(dest_sink_ts)
        os.remove(dest_source_ts)       

        self.assertGreater(non_filtered_frames_counter, filtered_frames_counter)


    def test_flighted_golf_ball_modelling(self):
        """Unit test ID 8: Testing that flighted golf ball is modelling its trajectory and speed given the initial speed components'"""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
        golfball = FlightedGolfball(None, timestamp, "p", "sequence_1.mp4", 51, 2, 22) 
        trajectory = golfball.get_golfball_motion_properties(get_trajectory=True)
        
        self.assertIsNotNone(trajectory)
        self.assertIsNotNone(golfball.velocity)
        self.assertIsNotNone(golfball.ball_launch_angle)
        self.assertIsNotNone(golfball.distance)

    def test_rolling_golf_ball_modelling(self):
        """Unit test ID 9: Testing that rolling golf ball is modelling the speed and distance travelled given the entire trajectory'"""  
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
        golfball = RollingGolfball(None, timestamp, "3i", "sequence_1.mp4", "0,1,2,3,4,5,6,7,8","0,1,2,3,4,5,6,7,8","0,1,2,3,4,5,6,7,8", 10)
        
        self.assertIsNotNone(golfball.distance)
        self.assertIsNotNone(golfball.velocity)

if __name__ == "__main__":

    testSuite = unittest.loader.makeSuite(TestModelComponents)
    runner = BetterPyUnitTestRunner()
    runner.run(testSuite)

    # unittest.main(verbosity=3)
