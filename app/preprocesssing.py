import cv2
import numpy as np
from PIL import Image 

def treshold(src):
    """Binarize image using tresholding."""
    image = cv2.imread(src)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255,
	cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 21, 10)
    return thresh

def preprocess(src):
    """Perform preprocessing for OCR."""
    image = treshold(src)

    # out_image = Image.fromarray(image) 
    # outimage.save("output_image.png") # save to file 
    return image


if __name__ == "__main__":
    image = '/workspaces/medtesthelper_bot/data/images/analiz.png'
    preprocess(image)