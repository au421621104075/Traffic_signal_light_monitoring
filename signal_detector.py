import cv2            #Used for image processing tasks, like capturing images, converting color spaces (e.g., BGR to HSV), and creating masks to detect colors (red, green, yellow).
import numpy as np    # Used to handle image data as arrays, enabling fast manipulation of pixel values. For example, np.sum()

def detect_signal_color(frame):
    roi = frame[100:300, 100:300]  # Adjust based on camera view #Define region of interest (ROI)
    #Converts to HSV for easier color detection.

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    '''cv2:        OpenCV library.
       cvtColor(): Means “convert color” — it's used to convert an image from one color format to another.
       roi:        The Region of Interest (a cropped part of the image).
       cv2.COLOR_BGR2HSV: Tells OpenCV to convert from BGR (Blue, Green, Red) to HSV (Hue, Saturation, Value).'''
    #hsv: Image in HSV color space.
    #Lower bound (0, 100, 100): Detects bright, saturated red colors.
    #Upper bound (10, 255, 255): Ensures the detected color is within the red hue range, with high saturation and brightness.
    red_mask = cv2.inRange(hsv, (0, 100, 100), (10, 255, 255))
    green_mask = cv2.inRange(hsv, (50, 100, 100), (70, 255, 255))
    yellow_mask = cv2.inRange(hsv, (20, 100, 100), (30, 255, 255))

    red = np.sum(red_mask)
    green = np.sum(green_mask)
    yellow = np.sum(yellow_mask)

    if red > green and red > yellow:
        return "Red"
    elif green > red and green > yellow:
        return "Green"
    elif yellow > red and yellow > green:
        return "Yellow"
    else:
        return "Malfunction"
