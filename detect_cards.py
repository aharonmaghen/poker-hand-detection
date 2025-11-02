from ultralytics import YOLO
import mss
import numpy as np
import cv2
import win32gui
import win32con
import time
from pathlib import Path


def get_scrcpy_windows():
    '''
    Finds all active Windows handles whose title contains "scrcpy".
    
    Returns:
        dict: Dictionary where keys are window handles (HWND) and values are
              bounding box coordinates (left, top, width, height) of the client area.
    '''
    windows = {}
    
    def enum_window_callback(hwnd, ctx):
        window_title = win32gui.GetWindowText(hwnd)
        if "scrcpy" in window_title.lower():
            # GetClientRect returns (left, top, right, bottom) where left=0, top=0
            _, _, right, bottom = win32gui.GetClientRect(hwnd)
            # Convert top-left corner (0, 0) to screen coordinates
            client_left, client_top = win32gui.ClientToScreen(hwnd, (0, 0))
            width = right
            height = bottom
            windows[hwnd] = {
                'left': client_left,
                'top': client_top,
                'width': width,
                'height': height
            }
        return True
    
    win32gui.EnumWindows(enum_window_callback, None)
    return windows


def capture_window_frame(bbox):
    '''
    Captures a frame from a window using mss screen capture.
    
    Args:
        bbox (dict): Dictionary with 'left', 'top', 'width', 'height' keys.
    
    Returns:
        numpy.ndarray: BGR format image array suitable for YOLO model.
    '''
    with mss.mss() as sct:
        monitor = {
            "top": bbox['top'],
            "left": bbox['left'],
            "width": bbox['width'],
            "height": bbox['height']
        }
        # Capture the screen
        screenshot = sct.grab(monitor)
        # Convert to numpy array
        img = np.array(screenshot)
        # Convert BGRA to BGR (mss returns BGRA format)
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img


def detect_cards(image, model, conf=0.5):
    '''
    Detects cards in an image using YOLO11 model and returns the unique cards.

    Args:
        image (numpy.ndarray): Image array in BGR format.
        model (YOLO): Pre-loaded YOLO model instance.
        conf (float): Confidence threshold for the detection. Default is 0.5.

    Returns:
        list: List of unique cards detected in the image with confidence above the threshold sorted by their left position.
    '''
    result = model.predict(image, verbose=False)[0]
    cards = []  # a list of tuples (left, card_name)
    cards_names = []  # a list of card names for deduplication
    summary = result.summary()

    for card in summary:
        if card['confidence'] >= conf:
            card_name = card['name']
            if card_name not in cards_names:
                cards_names.append(card_name)
                card_left = min(card['box']['x1'], card['box']['x2'])
                cards.append((card_left, card_name))
        
    # Sort the cards by their left position
    cards.sort(key=lambda x: x[0])

    # Extract the card names from the sorted list
    card_names = [card[1] for card in cards]

    return card_names 


def decode_cards(cards):
    '''
    Decodes the detected cards into a human-readable format using rank_map and suit_map.

    Args:
        cards (list): List of detected cards in the dataset format. e.g. 3C = "3 of Clubs".
    
    Returns:
        list: Human-readable format of the detected cards.
    '''
    rank_map = {
        '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', 
        '8': '8', '9': '9', '10': '10', 'J': 'Jack', 'Q': 'Queen', 'K': 'King', 'A': 'Ace'
    }
    suit_map = {
        'C': 'Clubs', 'D': 'Diamonds', 'H': 'Hearts', 'S': 'Spades'
    }
    
    decoded = []
    for card in cards:
        # Extract rank and suit (handles both '10C' and single-digit cards)
        if card.startswith('10'):
            rank = '10'
            suit = card[2]
        else:
            rank = card[0]
            suit = card[1]
        
        rank_name = rank_map.get(rank, rank)
        suit_name = suit_map.get(suit, suit)
        decoded.append(f"{rank_name} of {suit_name}")
    
    return decoded


if __name__ == '__main__':
    # Setup
    print("[SETUP] Creating output directory 'cards_detected' and loading YOLO model...")
    output_dir = Path('cards_detected')
    output_dir.mkdir(exist_ok=True)
    
    weights_path = 'weights/poker_best.pt'
    model = YOLO(weights_path, task='detect')
    print("[SETUP] YOLO model loaded successfully.")
    
    # State management
    last_detection_time = {}  # Maps HWND to last detection timestamp
    
    # Main execution loop
    while True:
        # Get all scrcpy windows
        windows = get_scrcpy_windows()
        
        # Process each window
        for i, (hwnd, bbox) in enumerate(windows.items()):
            # Check cooldown
            current_time = time.time()
            if hwnd in last_detection_time:
                time_since_last = current_time - last_detection_time[hwnd]
                if time_since_last < 3.0:
                    print(f"[INFO] Skipping detection for scrcpy window {i} (HWND: {hwnd}) due to 3-second cooldown.")
                    continue
            
            # Capture frame and detect cards
            try:
                frame = capture_window_frame(bbox)
                cards = detect_cards(frame, model)
                
                # Conditional output
                if len(cards) == 2:
                    # Update last detection time
                    last_detection_time[hwnd] = current_time
                    
                    # Decode cards to human-readable format
                    card_names = decode_cards(cards)
                    
                    # Determine output file path
                    output_file = output_dir / f'phone{i}.txt'
                    
                    # Overwrite the text file with card names
                    with open(output_file, 'w') as f:
                        f.write('\n'.join(card_names))
                    
                    print(f"[SUCCESS] Detected 2 cards in scrcpy window {i}. Wrote: {card_names[0]} and {card_names[1]} to phone{i}.txt.")
                else:
                    print(f"[INFO] scrcpy window {i} (HWND: {hwnd}) detected {len(cards)} cards. Skipping write.")
                    
            except Exception as e:
                print(f"[ERROR] Failed to process scrcpy window {i} (HWND: {hwnd}): {e}")
                continue
        
        # Loop pacing
        print(f"[MONITOR] Found {len(windows)} scrcpy windows. Iteration complete.")
        time.sleep(0.1)
