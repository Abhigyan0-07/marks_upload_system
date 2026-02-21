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
    root.withdraw()
    root.attributes("-topmost", True)
    print("Please select the Excel marksheet file in the popup...")
    
    file_path = filedialog.askopenfilename(
        title="Select Marksheet Excel File",
        filetypes=[("Excel files", "*.xlsx")]
    )
    
    if not file_path:
        print("No file selected. Using default 'marks.xlsx'...")
        file_path = "marks.xlsx"
        if not os.path.exists(file_path):
            wb = Workbook()
            ws = wb.active
            ws.append(["Timestamp", "Identified Digits"])
            wb.save(file_path)
    
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
        print(f"✅ Saved: {digits}")
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
            # Ensure ROI has some size
            if abs(start_point[0] - end_point[0]) > 10 and abs(start_point[1] - end_point[1]) > 10:
                roi_selected = True

def get_digits_and_contours(roi):
    """Utility to get contours and predict digits from a frame segment."""
    if roi.size == 0:
        return [], []
    
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    # Adaptive thresholding often works better for varying lighting
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                   cv2.THRESH_BINARY_INV, 11, 2)
    
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    digits = []
    boxes = []
    
    # Sort from left to right
    sorted_contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[0])
    
    for cnt in sorted_contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if 5 < w < 100 and 15 < h < 150: # Filter typical digit sizes
            digit_img = thresh[y:y+h, x:x+w]
            digit_img = image_refiner(digit_img)
            pred = predict_digit(digit_img)
            digits.append(pred)
            boxes.append((x, y, w, h))
            
    return digits, boxes, thresh

def main():
    excel_path = select_excel_file()
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Fatal Error: No camera found.")
            return

    cv2.namedWindow("Webcam Mark Scanner")
    cv2.setMouseCallback("Webcam Mark Scanner", mouse_callback)
    
    print(f"\nTarget File: {excel_path}")
    print("1. Drag a box on the feed.")
    print("2. Align digit inside green boxes.")
    print("3. Press 'S' to save, 'Q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret: break

        display_frame = frame.copy()
        preview_thresh = None

        if start_point and end_point:
            x1, y1 = min(start_point[0], end_point[0]), min(start_point[1], end_point[1])
            x2, y2 = max(start_point[0], end_point[0]), max(start_point[1], end_point[1])
            
            # Draw ROI
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
            
            if roi_selected:
                roi = frame[y1:y2, x1:x2]
                digits, boxes, preview_thresh = get_digits_and_contours(roi)
                
                # Draw live feedback boxes
                for (bx, by, bw, bh) in boxes:
                    cv2.rectangle(display_frame, (x1+bx, y1+by), (x1+bx+bw, y1+by+bh), (0, 255, 0), 2)
                
                if digits:
                    cv2.putText(display_frame, f"Detected: {digits}", (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                if preview_thresh is not None:
                    cv2.imshow("AI Preview (Binarized)", preview_thresh)

        cv2.imshow("Webcam Mark Scanner", display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'): break
        elif key == ord('s') and roi_selected:
            final_digits, _, _ = get_digits_and_contours(frame[y1:y2, x1:x2])
            save_to_excel(excel_path, final_digits)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
