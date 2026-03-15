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
    return int(np.argmax(model.predict(test_image, verbose=0)))

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

    # Adaptive thresholding handles variable real-world lighting much better
    # than a fixed binary threshold
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=11,
        C=2
    )

    # Morphological opening to remove tiny noise specks
    kernel = np.ones((2, 2), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

    results = []
    if hierarchy is None:
        return results

    for j, cnt in enumerate(contours):
        x, y, w, h = cv2.boundingRect(cnt)

        # FIX: use == -1 to select OUTER (top-level) contours, which are the
        # actual digit blobs.  The previous != -1 was selecting inner holes/voids
        # inside characters like '0', '8', '6', etc. — causing zero detections
        # for most digits.
        is_outer_contour = hierarchy[0][j][3] == -1

        # Tighter size filter to avoid noise
        if is_outer_contour and w > 15 and h > 15:
            roi = gray[y:y + h, x:x + w]
            roi = cv2.bitwise_not(roi)
            roi = image_refiner(roi)

            pred = predict_digit(roi)
            results.append({
                "digit": pred,
                "box": [x, y, w, h]
            })

    # Sort in reading order: top-to-bottom row, then left-to-right within each row
    # Use a row tolerance of 20px so items on the same line cluster together
    row_tolerance = 20
    results.sort(key=lambda r: (r["box"][1] // row_tolerance, r["box"][0]))

    return results
