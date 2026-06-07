import cv2
import base64


def encode_image_to_base64(image):
    """
    Convert OpenCV image to Base64 string
    for API response.
    """
    _, buffer = cv2.imencode(".jpg", image)
    return base64.b64encode(buffer).decode("utf-8")