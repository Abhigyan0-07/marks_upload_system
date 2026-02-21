import cv2
import numpy as np
import os
from openpyxl import Workbook, load_workbook as load_wb
from process_image import get_output_image, predict_digit, image_refiner

# Constants for the capture zone (ROI)
ROI_X1, ROI_Y1 = 100, 100
ROI_X2, ROI_Y2 = 400, 400
EXCEL_FILE = "marks.xlsx"

def save_to_excel(digits):
    """Saves the list of digits to a local Excel file."""
    if not digits:
        return
    
    if os.path.exists(EXCEL_FILE):
        wb = load_wb(EXCEL_FILE)
        ws = wb.active
    else:
        wb = Workbook()
        ws = wb.active
        ws.append(["Timestamp", "Identified Digits"])

    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ws.append([timestamp, ", ".join(map(str, digits))])
    wb.save(EXCEL_FILE)
    print(f"Saved {digits} to {EXCEL_FILE}")

def process_roi(frame):
    """Processes the ROI to extract and identify digits."""
    roi = frame[ROI_Y1:ROI_Y2, ROI_X1:ROI_X2]
    # Convert to grayscale for processing
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Use existing refinement logic from process_image.py if suitable, 
    # or implement a simple contour-based detection here.
    # For now, we'll save the ROI temporarily to use get_output_image logic
    temp_path = "temp_roi.png"
    cv2.imwrite(temp_path, roi)
    
    # We need to modify get_output_image slightly or reuse its logic to get the digits
    # Let's extract digits manually here to have better control
    img = cv2.imread(temp_path, 0)
    ret, thresh = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    
    found_digits = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 10 and h > 10:
            digit_roi = thresh[y:y+h, x:x+w]
            digit_roi = image_refiner(digit_roi)
            pred = predict_digit(digit_roi)
            found_digits.append(pred)
    
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    return found_digits

def main():
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    print("--- Webcam Mark Scanner ---")
    print("Press 'S' to scan the yellow box area.")
    print("Press 'Q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Draw the ROI rectangle (Yellow)
        cv2.rectangle(frame, (ROI_X1, ROI_Y1), (ROI_X2, ROI_Y2), (0, 255, 255), 2)
        cv2.putText(frame, "Capture Zone", (ROI_X1, ROI_Y1 - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        cv2.imshow("Webcam Mark Scanner", frame)

        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord('s'):
            print("Scanning...")
            digits = process_roi(frame)
            if digits:
                print(f"Identified: {digits}")
                save_to_excel(digits)
            else:
                print("No digits detected in the zone.")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
