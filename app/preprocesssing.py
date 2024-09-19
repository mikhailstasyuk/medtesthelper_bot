import cv2
import numpy as np
from PIL import Image 

def threshold(src):
    """Binarize image using thresholding."""
    # image = cv2.imread(src)
    # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # thresh = cv2.adaptiveThreshold(gray, 255,
	# cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 21, 10)
    # return thresh


    image = cv2.imread(src, cv2.IMREAD_GRAYSCALE)
    _, thresh = cv2.threshold(image, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    cv2.imwrite('preprocessed_image.png', thresh)  # Save and inspect the preprocesse
    return thresh


def check_image_dpi(image_path, min_dpi=295):
    """Check if input image has minimum 300 DPI"""
    try:
        with Image.open(image_path) as img:
            # Get the image DPI
            dpi = img.info.get('dpi')
            
            if dpi:
                # Check that both DPI values (X and Y) are not less than min_dpi
                print(dpi)
                return dpi[0] >= min_dpi and dpi[1] >= min_dpi
            else:
                raise Exception(f"Failed to get DPI information for {image_path}")
    except Exception as e:
        raise Exception(f"Error opening image {image_path}: {e}")


def preprocess(src):
    """Perform preprocessing for OCR."""
    image = threshold(src)

    # out_image = Image.fromarray(image) 
    # outimage.save("output_image.png") # save to file 
    return image


if __name__ == "__main__":
    image = '/workspaces/medtesthelper_bot/data/images/analiz.png'
    preprocess(image)