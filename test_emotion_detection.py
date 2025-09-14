import unittest
from EmotionDetection import emotion_detector

class TestEmotionDetector(unittest.TestCase):
    
    def test_joy(self):
        result = emotion_detector("I am glad this happened")
        self.assertEqual(result['dominant_emotion'], 'joy')
    
    def test_anger(self):
        result = emotion_detector("I am really mad about this")
        self.assertEqual(result['dominant_emotion'], 'anger')
    
    def test_disgust(self):
        result = emotion_detector("I feel disgusted just hearing about this")
        self.assertEqual(result['dominant_emotion'], 'disgust')
    
    def test_sadness(self):
        result = emotion_detector("I am so sad about this")
        self.assertEqual(result['dominant_emotion'], 'sadness')