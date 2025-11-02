"""
Poker Card Detection from Video using YOLO11
זיהוי קלפי פוקר מווידאו באמצעות YOLO11

Modified to work with scrcpy window capture instead of webcam.
מותאם לעבודה עם לכידת חלון scrcpy במקום מצלמה.
"""

import cv2
import numpy as np
from ultralytics import YOLO
import time
import os
import json
import win32gui
from detect_cards import decode_cards
from window_capture import find_window_by_title, capture_window, list_windows_with_keywords, list_all_visible_windows
from window_capture_improved import select_window_interactively, get_window_under_cursor, list_all_visible_windows_detailed

def detect_cards_from_frame(frame, model, conf=0.5):
    '''
    Detects cards in a video frame using YOLO11 model and returns the unique cards.

    Args:
        frame (numpy.ndarray): Video frame as numpy array (BGR format from OpenCV).
        model: Pre-loaded YOLO11 model instance.
        conf (float): Confidence threshold for the detection. Default is 0.5.

    Returns:
        tuple: (card_names, annotated_frame) - List of unique cards and frame with detections drawn.
    '''
    
    # Run prediction on the frame (numpy array)
    result = model.predict(frame, conf=conf, verbose=False)[0]
    
    cards = [] # a list of tuples (left, card_name)
    cards_names = [] # a list of card names for deduplication
    all_detections = []  # All detections for debugging (even below threshold)
    
    # Get detections from result
    annotated_frame = result.plot()  # Get annotated frame with bounding boxes
    
    # Extract detection information - similar to original detect_cards function
    if result.boxes is not None and len(result.boxes) > 0:
        for i, box in enumerate(result.boxes):
            confidence = float(box.conf[0].cpu().numpy())
            class_id = int(box.cls[0].cpu().numpy())
            card_name = result.names[class_id]
            
            # Store all detections for debugging
            all_detections.append({
                'name': card_name,
                'confidence': confidence,
                'passed_threshold': confidence >= conf
            })
            
            if confidence >= conf:
                if card_name not in cards_names:
                    cards_names.append(card_name)
                    # Get left position from bounding box (similar to original function)
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    card_left = min(x1, x2)
                    cards.append((card_left, card_name))
    else:
        # No boxes detected at all
        all_detections = None
    
    # Sort the cards by their left position (like original function)
    cards.sort(key=lambda x: x[0])
    
    # Extract the card names from the sorted list
    card_names = [card[1] for card in cards]
    
    return card_names, annotated_frame, all_detections
    

def main():
    """
    Main function to run video card detection from scrcpy window
    """
    print("=" * 70)
    print("Poker Card Detection from scrcpy Window using YOLO11")
    print("זיהוי קלפי פוקר מחלון scrcpy באמצעות YOLO11")
    print("=" * 70)
    
    # Path to the trained model
    weights_path = 'weights/poker_best.pt'
    
    if not os.path.exists(weights_path):
        print(f"\nError: Model weights not found at: {weights_path}")
        print(f"שגיאה: משקלי המודל לא נמצאו ב: {weights_path}")
        print("Please make sure the weights file exists in the weights directory.")
        print("אנא ודא שקובץ המשקלים קיים בתיקיית weights.")
        return
    
    print(f"\nLoading model from: {weights_path}")
    print(f"טוען מודל מ: {weights_path}")
    
    # Load the YOLO11 model once
    model = YOLO(weights_path, task='detect')
    
    print("Model loaded successfully!")
    print("המודל נטען בהצלחה!\n")
    
    # Find scrcpy window - smart auto-detection first
    print("\nSearching for scrcpy window...")
    print("מחפש חלון scrcpy...")
    
    # Try to auto-detect scrcpy window by class name or title
    all_windows = list_all_visible_windows_detailed()
    scrcpy_windows = []
    
    # Look for SDL_app windows (scrcpy uses SDL) or windows with device names
    for hwnd, title, width, height, class_name in all_windows:
        # scrcpy windows typically have SDL_app class or device names in title
        is_scrcpy = (
            class_name == 'SDL_app' or  # scrcpy uses SDL
            'scrcpy' in title.lower() or
            ('device' in title.lower() or 'phone' in title.lower() or 'android' in title.lower())
        )
        # Exclude CMD and File Explorer
        if is_scrcpy and 'cmd.exe' not in title.lower() and 'file explorer' not in title.lower() and 'סייר' not in title:
            scrcpy_windows.append((hwnd, title, width, height, class_name))
    
    windows = []
    choice = None  # Initialize choice variable
    
    if scrcpy_windows:
        # Found scrcpy window automatically!
        print(f"\n✓ Found scrcpy window automatically: {scrcpy_windows[0][1]}")
        print(f"✓ נמצא חלון scrcpy אוטומטית: {scrcpy_windows[0][1]}")
        if len(scrcpy_windows) > 1:
            print(f"\nFound {len(scrcpy_windows)} potential scrcpy windows:")
            print(f"נמצאו {len(scrcpy_windows)} חלונות scrcpy פוטנציאליים:")
            for i, (hwnd, title, width, height, class_name) in enumerate(scrcpy_windows):
                print(f"  {i+1}. '{title}' ({width}x{height}) [Class: {class_name}]")
            print("\nUsing first one. If wrong, restart and choose method 2.")
            print("משתמש בראשון. אם זה לא נכון, הפעל מחדש ובחר שיטה 2.")
        windows = [(scrcpy_windows[0][0], scrcpy_windows[0][1])]
    else:
        # No auto-detection, show selection menu
        print("\n" + "="*70)
        print("Window Selection Methods")
        print("שיטות בחירת חלון")
        print("="*70)
        print("\nChoose how to select the scrcpy window:")
        print("בחר איך לבחור את חלון scrcpy:")
        print("  1. Interactive - Click on the window (RECOMMENDED)")
        print("     אינטראקטיבי - לחץ על החלון (מומלץ)")
        print("  2. List all windows and choose by number")
        print("     רשימת כל החלונות ובחירה לפי מספר")
        print("  3. Auto-detect by keywords")
        print("     זיהוי אוטומטי לפי מילות מפתח")
        print("\nEnter your choice (1, 2, or 3):")
        print("הקלד את הבחירה שלך (1, 2, או 3):")
        
        try:
            choice = input().strip()
        except KeyboardInterrupt:
            print("\nExiting.")
            print("יוצא.")
            return
        
        if choice == '1':
            # Interactive selection - user clicks on window
            window_hwnd, window_title = select_window_interactively()
            if window_hwnd:
                windows = [(window_hwnd, window_title)]
            else:
                print("\nFailed to select window interactively. Trying list method...")
                print("נכשל בבחירת חלון אינטראקטיבית. מנסה שיטת רשימה...")
                choice = '2'
    
    if choice and (choice == '2' or (choice == '1' and not windows)):
        # List all windows
        print("\nListing all visible windows:")
        print("מציג רשימה של כל החלונות הנראים:")
        all_windows = list_all_visible_windows_detailed()
        if all_windows:
            print("\nAll visible windows:")
            print("כל החלונות הנראים:")
            for i, (hwnd, title, width, height, class_name) in enumerate(all_windows):
                print(f"  {i+1}. '{title}' ({width}x{height}) [Class: {class_name}]")
            
            print("\nPlease type the number of the scrcpy window (or 'q' to quit):")
            print("אנא הקלד את המספר של חלון scrcpy (או 'q' כדי לצאת):")
            print("(Look for a window that shows your phone screen)")
            print("(חפש חלון שמציג את מסך הטלפון)")
            
            try:
                num_choice = input().strip()
                if num_choice.lower() == 'q':
                    return
                choice_num = int(num_choice) - 1
                if 0 <= choice_num < len(all_windows):
                    window_hwnd, window_title, _, _, _ = all_windows[choice_num]
                    windows = [(window_hwnd, window_title)]
                    print(f"Selected window: {window_title}")
                    print(f"חלון שנבחר: {window_title}")
                else:
                    print("Invalid choice. Exiting.")
                    print("בחירה לא חוקית. יוצא.")
                    return
            except (ValueError, KeyboardInterrupt):
                print("\nExiting.")
                print("יוצא.")
                return
        else:
            print("\nError: No visible windows found!")
            print("שגיאה: לא נמצאו חלונות נראים!")
            return
    
    if choice and choice == '3':
        # Auto-detect by keywords
        print("\nSearching for scrcpy window by keywords...")
        print("מחפש חלון scrcpy לפי מילות מפתח...")
        scrcpy_keywords = ['scrcpy', 'android', 'device', 'phone']
        windows = list_windows_with_keywords(scrcpy_keywords)
        
        # Filter out CMD windows and File Explorer windows
        windows = [(hwnd, title) for hwnd, title in windows 
                   if 'cmd.exe' not in title.lower() 
                   and 'file explorer' not in title.lower()
                   and 'סייר' not in title]
        
        if not windows:
            print("\nNo scrcpy window found automatically.")
            print("לא נמצא חלון scrcpy אוטומטית.")
            print("Try method 1 or 2 instead.")
            print("נסה שיטה 1 או 2 במקום.")
            return
    
    if not windows:
        print("\nError: No window selected!")
        print("שגיאה: לא נבחר חלון!")
        return
    
    print(f"\nFound {len(windows)} window(s):")
    print(f"נמצאו {len(windows)} חלון/ות:")
    for i, (hwnd, title) in enumerate(windows):
        print(f"  {i+1}. {title}")
    
    # Use first window found
    window_hwnd, window_title = windows[0]
    print(f"\nUsing window: {window_title}")
    print(f"משתמש בחלון: {window_title}")
    
    # Save window selection for next time
    try:
        config = {
            'last_selected_window': int(window_hwnd),
            'last_window_title': window_title,
            'confidence_threshold': 0.3
        }
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
    except:
        pass
    
    # Get window dimensions
    left, top, right, bottom = win32gui.GetWindowRect(window_hwnd)
    actual_width = right - left
    actual_height = bottom - top
    print(f"Window size: {actual_width}x{actual_height}")
    print(f"גודל חלון: {actual_width}x{actual_height}\n")
    
    print("Instructions:")
    print("הוראות:")
    print("- Press 'q' to quit")
    print("- לחץ 'q' כדי לצאת")
    print("- Press 's' to save current frame with detections")
    print("- לחץ 's' כדי לשמור פריים נוכחי עם זיהויים")
    print("- Position 2 cards in the scrcpy window (for poker hand)")
    print("- הצב 2 קלפים בחלון scrcpy (ליד פוקר)")
    print("- Make sure the scrcpy window is visible and cards are clearly visible")
    print("- ודא שחלון scrcpy נראה והקלפים נראים בבירור")
    print("- Cards should be in the center area for best results")
    print("- הקלפים צריכים להיות באזור המרכז לתוצאות מיטביות\n")
    
    # Create output directory for saved frames
    output_dir = "detected_cards"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
        print(f"נוצרה תיקיית פלט: {output_dir}\n")
    
    # FPS calculation
    fps_counter = 0
    fps_time = time.time()
    fps_display = 0
    
    # Detection confidence threshold (start lower for better detection)
    conf_threshold = 0.3
    
    print("Starting detection...")
    print("מתחיל זיהוי...\n")
    print("Make sure the scrcpy window stays visible during detection.")
    print("ודא שחלון scrcpy נשאר נראה במהלך הזיהוי.\n")
    
    frame_count = 0
    last_frame = None
    
    while True:
        # Capture frame from scrcpy window
        frame = capture_window(window_hwnd)
        
        if frame is None:
            # Print warning only occasionally to avoid spam
            if frame_count % 30 == 0:
                print("Warning: Could not capture window frame. Window might be minimized or hidden.")
                print("אזהרה: לא ניתן ללכוד פריים מהחלון. החלון עשוי להיות מזעור או מוסתר.")
            # Use last frame if available
            if last_frame is not None:
                frame = last_frame.copy()
            else:
                time.sleep(0.1)
                continue
        
        last_frame = frame.copy()
        frame_count += 1
        
        # Check if window still exists and is visible
        if not win32gui.IsWindowVisible(window_hwnd):
            print("Warning: scrcpy window is no longer visible.")
            print("אזהרה: חלון scrcpy כבר לא נראה.")
            time.sleep(0.1)
            continue
        
        # Detect cards in the frame
        cards, annotated_frame, all_detections = detect_cards_from_frame(frame, model, conf=conf_threshold)
        
        # Debug: Show detection info (only on first few frames, when cards detected, or when no cards)
        show_debug = (
            frame_count <= 3 or  # First frames
            len(cards) > 0 or  # Cards detected - always show
            (len(cards) == 0 and frame_count % 60 == 0)  # No cards every 60 frames
        )
        
        if show_debug:
            if all_detections is None or len(all_detections) == 0:
                if frame_count % 60 == 0:  # Don't spam
                    print(f"Frame {frame_count}: No detections at all from model")
                    print(f"פריים {frame_count}: אין זיהויים כלל מהמודל")
            else:
                print(f"Frame {frame_count}: Found {len(all_detections)} detection(s) (threshold: {conf_threshold:.2f})")
                print(f"פריים {frame_count}: נמצאו {len(all_detections)} זיהוי/ים (threshold: {conf_threshold:.2f})")
                for det in all_detections[:5]:  # Show first 5
                    status = "✓" if det['passed_threshold'] else "✗"
                    print(f"  {status} {det['name']}: {det['confidence']:.3f}")
                
                if len(cards) == 0:
                    print("  ⚠ No cards passed threshold. Press '-' to lower threshold.")
                    print("  ⚠ אין קלפים שעברו את ה-threshold. לחץ '-' כדי להוריד את ה-threshold.")
                elif len(cards) == 1:
                    print(f"  ✓ Found 1 card. Need 1 more card for poker hand.")
                    print(f"  ✓ נמצא קלף אחד. צריך קלף נוסף ליד פוקר.")
                else:
                    print(f"  ✓✓ Found {len(cards)} cards! Poker hand ready!")
                    print(f"  ✓✓ נמצאו {len(cards)} קלפים! יד פוקר מוכנה!")
        
        # Display detection results on the frame
        display_frame = annotated_frame.copy()
        
        # Debug: Show frame dimensions on first frame and save it
        if frame_count == 1:
            print(f"\nFrame captured successfully. Size: {frame.shape[1]}x{frame.shape[0]}")
            print(f"פריים נלכד בהצלחה. גודל: {frame.shape[1]}x{frame.shape[0]}")
            
            # Save first frame for debugging
            debug_filename = os.path.join(output_dir, "first_frame_debug.jpg")
            cv2.imwrite(debug_filename, frame)
            
            # Also save annotated frame
            annotated_debug_filename = os.path.join(output_dir, "first_frame_annotated_debug.jpg")
            cv2.imwrite(annotated_debug_filename, annotated_frame)
            
            print(f"\nIMPORTANT: Check these files to see what was captured:")
            print(f"חשוב: בדוק את הקבצים האלה כדי לראות מה נלכד:")
            print(f"  - {debug_filename}")
            print(f"  - {annotated_debug_filename}")
            print(f"\nIf the first_frame_debug.jpg shows a CMD window or File Explorer,")
            print(f"you need to select a different window (the actual scrcpy window).")
            print(f"אם first_frame_debug.jpg מציג חלון CMD או סייר קבצים,")
            print(f"אתה צריך לבחור חלון אחר (חלון scrcpy האמיתי).\n")
        
        # Add information overlay
        info_y = 30
        line_height = 25
        
        # Background for text
        overlay = display_frame.copy()
        cv2.rectangle(overlay, (10, 10), (400, 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, display_frame, 0.3, 0, display_frame)
        
        # Display number of cards detected
        card_count_text = f"Cards Detected: {len(cards)}/2"
        cv2.putText(display_frame, card_count_text,
                   (20, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        info_y += line_height
        
        # Display detected cards
        if cards:
            decoded = decode_cards(cards[:2])  # Show first 2 cards for poker hand
            for i, card_name in enumerate(decoded[:2]):
                card_text = f"Card {i+1}: {card_name}"
                color = (0, 255, 0) if i == 0 else (0, 255, 255)
                cv2.putText(display_frame, card_text,
                           (20, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                info_y += line_height
            
            # Show message if only 1 card detected
            if len(cards) == 1:
                hint_text = "Need 1 more card for poker hand"
                cv2.putText(display_frame, hint_text,
                           (20, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                info_y += line_height
        else:
            no_cards_text = "No cards detected"
            if all_detections and len(all_detections) > 0:
                no_cards_text += f" ({len(all_detections)} below threshold)"
            cv2.putText(display_frame, no_cards_text,
                       (20, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            info_y += line_height
            # Show threshold hint
            cv2.putText(display_frame, f"Press '-' to lower threshold ({conf_threshold:.2f})",
                       (20, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
        
        # Calculate and display FPS
        fps_counter += 1
        if time.time() - fps_time >= 1.0:
            fps_display = fps_counter
            fps_counter = 0
            fps_time = time.time()
        
        fps_text = f"FPS: {fps_display}"
        cv2.putText(display_frame, fps_text,
                   (20, info_y + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Status message at bottom
        if len(cards) >= 2:
            status_text = "2 Cards Detected! - Poker Hand Ready"
            status_color = (0, 255, 0)
        elif len(cards) == 1:
            status_text = "1 Card Detected - Need 1 More"
            status_color = (0, 165, 255)
        else:
            status_text = "No Cards Detected"
            status_color = (0, 0, 255)
        
        cv2.putText(display_frame, status_text,
                   (10, actual_height - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
        
        # Show frame
        cv2.imshow('Poker Card Detection - זיהוי קלפי פוקר', display_frame)
        
        # Handle keyboard input
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            # Save current frame
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(output_dir, f"detection_{timestamp}.jpg")
            cv2.imwrite(filename, display_frame)
            print(f"Frame saved: {filename}")
            print(f"פריים נשמר: {filename}")
            if cards:
                print(f"Cards detected: {', '.join(decode_cards(cards[:2]))}")
                print(f"קלפים שזוהו: {', '.join(decode_cards(cards[:2]))}")
        elif key == ord('+') or key == ord('='):
            # Increase confidence threshold
            conf_threshold = min(0.95, conf_threshold + 0.05)
            print(f"Confidence threshold: {conf_threshold:.2f}")
        elif key == ord('-'):
            # Decrease confidence threshold
            conf_threshold = max(0.1, conf_threshold - 0.05)
            print(f"Confidence threshold: {conf_threshold:.2f}")
    
    # Cleanup
    cv2.destroyAllWindows()
    print("\n" + "=" * 70)
    print("Detection stopped.")
    print("הזיהוי הופסק.")
    print("=" * 70)

if __name__ == "__main__":
    main()

