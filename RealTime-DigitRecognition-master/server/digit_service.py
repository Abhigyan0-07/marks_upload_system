import cv2
import numpy as np
import math
from tf_keras.models import load_model
import os

# Load model relative to this file
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'cnn_model', 'digit_classifier.h5')
model = load_model(MODEL_PATH)

def predict_digit(img):
    """Predicts a single digit from a 28x28 grayscale image."""
    test_image = img.reshape(-1, 28, 28, 1)
    return int(np.argmax(model.predict(test_image)))

def image_refiner(gray):
    """Refines a grayscale image of a digit into a 28x28 format for the CNN."""
    org_size = 22
    img_size = 28
    rows, cols = gray.shape
    
    if rows > cols:
        factor = org_size / rows
        rows = org_size
        cols = int(round(cols * factor))        
    else:
        factor = org_size / cols
        cols = org_size
        rows = int(round(rows * factor))
    
    gray = cv2.resize(gray, (cols, rows))
    
    # Get padding 
    cols_padding = (int(math.ceil((img_size - cols) / 2.0)), int(math.floor((img_size - cols) / 2.0)))
    rows_padding = (int(math.ceil((img_size - rows) / 2.0)), int(math.floor((img_size - rows) / 2.0)))
    
    # Apply padding 
    gray = np.pad(gray, (rows_padding, cols_padding), 'constant')
    return gray

def extract_digits_from_frame(frame):
    """Detects and predicts all digits in a BGR frame."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Binary thresholding (assuming dark digits on light background)
    _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    results = []
    if hierarchy is None:
        return results

    for j, cnt in enumerate(contours):
        x, y, w, h = cv2.boundingRect(cnt)
        
        # Filter typical digit sizes and ensure it's an external contour
        if hierarchy[0][j][3] != -1 and w > 8 and h > 8:
            roi = gray[y:y+h, x:x+w]
            roi = cv2.bitwise_not(roi)
            roi = image_refiner(roi)
            
            pred = predict_digit(roi)
            results.append({
                "digit": pred,
                "box": [x, y, w, h]
            })
            
    # Sort results by X coordinate (left to right)
    results.sort(key=lambda x: x["box"][0])
    return results
