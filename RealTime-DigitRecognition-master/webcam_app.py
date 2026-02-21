import cv2
import numpy as np
import os
import tkinter as tk
from tkinter import filedialog
from openpyxl import Workbook, load_workbook as load_wb
from process_image import predict_digit, image_refiner
from datetime import datetime

# Global variables for ROI selection
start_point = None
end_point = None
is_dragging = False
roi_selected = False

def select_excel_file():
    """Opens a file dialog to select an Excel file."""
    root = tk.Tk()
    root.withdraw()  # Hide the main tkinter window
    print("Please select the Excel marksheet file...")
    file_path = filedialog.askopenfilename(
        title="Select Marksheet Excel File",
        filetypes=[("Excel files", "*.xlsx")]
    )
    
    if not file_path:
        # If no file selected, create a default one
        file_path = "marks.xlsx"
        if not os.path.exists(file_path):
            wb = Workbook()
            ws = wb.active
            ws.append(["Timestamp", "Identified Digits"])
            wb.save(file_path)
            print(f"Created new default file: {file_path}")
    
    root.destroy()
    return file_path

def save_to_excel(file_path, digits):
    """Saves the identified digits to the selected Excel file."""
    if not digits:
        return
    
    try:
        wb = load_wb(file_path)
        ws = wb.active
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ws.append([timestamp, ", ".join(map(str, digits))])
        wb.save(file_path)
        print(f"✅ Saved results {digits} to {os.path.basename(file_path)}")
    except Exception as e:
        print(f"❌ Error saving to Excel: {e}")

def mouse_callback(event, x, y, flags, param):
    """Mouse callback to handle custom ROI selection."""
    global start_point, end_point, is_dragging, roi_selected
    
    if event == cv2.EVENT_LBUTTONDOWN:
        start_point = (x, y)
        is_dragging = True
        roi_selected = False
        
    elif event == cv2.EVENT_MOUSEMOVE:
        if is_dragging:
            end_point = (x, y)
            
    elif event == cv2.EVENT_LBUTTONUP:
        end_point = (x, y)
        is_dragging = False
        if start_point != end_point:
            roi_selected = True

def process_roi(frame, sp, ep):
    """Processes the manual area to extract and identify digits."""
    x1, y1 = min(sp[0], ep[0]), min(sp[1], ep[1])
    x2, y2 = max(sp[0], ep[0]), max(sp[1], ep[1])
    
    if x2 - x1 < 5 or y2 - y1 < 5:
        return []

    roi = frame[y1:y2, x1:x2]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    
    # Process ROI
    ret, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    
    found_digits = []
    # Sort contours left to right
    bounding_boxes = [cv2.boundingRect(c) for c in contours]
    if not bounding_boxes:
        return []
    
    # Filter and process
    for (x, y, w, h) in sorted(bounding_boxes, key=lambda b: b[0]):
        if w > 8 and h > 8:
            digit_roi = thresh[y:y+h, x:x+w]
            digit_roi = image_refiner(digit_roi)
            pred = predict_digit(digit_roi)
            found_digits.append(pred)
            
    return found_digits

def main():
    excel_path = select_excel_file()
    
    # Use CAP_DSHOW for better Windows compatibility
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        print("Error: Could not open webcam. Trying default backend...")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Fatal Error: No camera found.")
            return

    cv2.namedWindow("Webcam Mark Scanner")
    cv2.setMouseCallback("Webcam Mark Scanner", mouse_callback)

    print(f"\nTarget File: {excel_path}")
    print("Instructions:")
    print("1. Click and drag to MARK the box around the digits.")
    print("2. Press 'S' to identify digits in the box and SAVE to Excel.")
    print("3. Press 'Q' to Quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Draw current selection
        display_frame = frame.copy()
        if start_point and end_point:
            color = (0, 255, 255) if not is_dragging else (0, 165, 255)
            cv2.rectangle(display_frame, start_point, end_point, color, 2)
            if roi_selected:
                cv2.putText(display_frame, "Ready to Scan", (start_point[0], start_point[1] - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        cv2.imshow("Webcam Mark Scanner", display_frame)

        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord('s'):
            if roi_selected:
                print("Scanning selected zone...")
                digits = process_roi(frame, start_point, end_point)
                if digits:
                    print(f"Found: {digits}")
                    save_to_excel(excel_path, digits)
                else:
                    print("No digits detected in the selection.")
            else:
                print("Please mark a box first by dragging the mouse.")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
