import unittest
from unittest.mock import patch
import numpy as np
from core.perception.ocr_engine import OCREngine

class testocrengine(unittest.TestCase):
    def setUp(self):
        self.ocr=OCREngine()
        self.sample=np.zeros(
            (100,100,3),
            dtype=np.uint8
        )
    
    def test_lang(self):
        ocr=OCREngine(language="eng")
        self.assertEqual(ocr.language,"eng")

    @patch("core.perception.ocr_engine.pytesseract.image_to_string")
    def test_dig_ocr(self,mock_string):
        mock_string.return_value="hello world \n"
        expected_str="hello world"
       
        result=self.ocr.extract_dig_text(self.sample)
        self.assertEqual(result,expected_str)


    def test_None_frame(self):
        with self.assertRaises(ValueError):
            self.ocr.extract_dig_text(None)  

    def test_empty_frames(self):
        empty=np.array([])
        result=self.ocr.extract_dig_text(empty)
        self.assertEqual(result,"")

    def test_empty_dict(self):
        empty=np.array([])
        result=self.ocr.extract_physical_text_with_boxes(empty)
        self.assertEqual(result,[])   


    @patch("core.perception.ocr_engine.pytesseract.image_to_data")
    def test_phy_ocr(self,mock_data):
        mock_data.return_value={
            "text":["hello","","world"],
            "conf":["95","-1","88"],
            "left":[10,0,50],
            "top":[10,0,50],
            "height":[10,0,50],
            "width":[10,0,50]

        }
        result=self.ocr.extract_physical_text_with_boxes(self.sample)
        expected=[
            {"text":"hello",
             "box":{
                "left":10,
                "top":10,
                "height":10,
                "width":10
            },
            "conf":95
        },
        {
            "text":"world",
            "box":{
                "left":50,
                "top":50,
                "height":50,
                "width":50
                


            },
            "conf":88
        }]

        self.assertEqual(result,expected)
        mock_data.assert_called_once()

     



if __name__=="__main__":
    unittest.main()
    





             



        


        
    
 