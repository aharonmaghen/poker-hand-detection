from ultralytics import YOLO
import numpy as np
from PIL import Image, ImageCms

def detect_cards(image_path_or_array, weights_path, conf=0.5):
    '''
    Detects cards in an image using YOLO11 model and returns the unique cards.

    Args:
        image_path_or_array (str or np.ndarray): Path to the image file or numpy array of the image.
        weights_path (str): Path to the YOLO11 weights file.
        conf (float): Confidence threshold for the detection. Default is 0.5.

    Returns:
        list: List of unique cards detected in the image with confidence above the threshold sorted by their left position.
    '''

    model = YOLO(weights_path, task='detect')
    result = model.predict(image_path_or_array, verbose=False)[0]
    cards = [] # a list of tuples (left, card_name)
    cards_names = [] # a list of card names for deduplication
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
    Decodes the detected cards into a human-readable format.

    Args:
        cards (list): List of detected cards in the dataset format. e.g. 3C = "3 of Clubs".
    
    Returns:
        str: Human-readable format of the detected cards.
    '''
    
    card_names = {
        'AC': 'Ace of Clubs',
        '2C': '2 of Clubs',
        '3C': '3 of Clubs',
        '4C': '4 of Clubs',
        '5C': '5 of Clubs',
        '6C': '6 of Clubs',
        '7C': '7 of Clubs',
        '8C': '8 of Clubs',
        '9C': '9 of Clubs',
        '10C': '10 of Clubs',
        'JC': 'Jack of Clubs',
        'QC': 'Queen of Clubs',
        'KC': 'King of Clubs',
        'AD': 'Ace of Diamonds',
        '2D': '2 of Diamonds',
        '3D': '3 of Diamonds',
        '4D': '4 of Diamonds',
        '5D': '5 of Diamonds',
        '6D': '6 of Diamonds',
        '7D': '7 of Diamonds',
        '8D': '8 of Diamonds',
        '9D': '9 of Diamonds',
        '10D': '10 of Diamonds',
        'JD': 'Jack of Diamonds',
        'QD': 'Queen of Diamonds',
        'KD': 'King of Diamonds',
        'AH': 'Ace of Hearts',
        '2H': '2 of Hearts',
        '3H': '3 of Hearts',
        '4H': '4 of Hearts',
        '5H': '5 of Hearts',
        '6H': '6 of Hearts',
        '7H': '7 of Hearts',
        '8H': '8 of Hearts',
        '9H': '9 of Hearts',
        '10H': '10 of Hearts',
        'JH': 'Jack of Hearts',
        'QH': 'Queen of Hearts',
        'KH': 'King of Hearts',
        'AS': 'Ace of Spades',
        '2S': '2 of Spades',
        '3S': '3 of Spades',
        '4S': '4 of Spades',
        '5S': '5 of Spades',
        '6S': '6 of Spades',
        '7S': '7 of Spades',
        '8S': '8 of Spades',
        '9S': '9 of Spades',
        '10S': '10 of Spades',
        'JS': 'Jack of Spades',
        'QS': 'Queen of Spades',
        'KS': 'King of Spades',
    }
    
    return [card_names[card] for card in cards]

def find_scrcpy_windows():
    '''
    Finds all scrcpy windows on macOS using Quartz API.
    
    Returns:
        list: List of dictionaries containing window information with title, bounds, etc.
    '''
    from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
    
    window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
    
    # Filter for scrcpy windows
    scrcpy_windows = []
    for window in window_list:
        owner = window.get('kCGWindowOwnerName', '')
        title = window.get('kCGWindowName', '')
        
        # Look for windows with 'scrcpy' in the owner or title
        if 'scrcpy' in owner.lower():
            scrcpy_windows.append(window)
    
    return scrcpy_windows


def capture_window_screenshot(window_info):
    '''
    Captures a screenshot of a specific window on macOS.
    
    Args:
        window_info (dict): Window information dictionary from Quartz API.
        
    Returns:
        np.ndarray or None: Image as numpy array, or None if capture failed.
    '''
    from Quartz import CGWindowListCreateImage, CGRectMake, kCGWindowImageDefault, kCGWindowListOptionIncludingWindow
    
    # Get window bounds
    bounds = window_info.get('kCGWindowBounds', {})
    x = int(bounds.get('X', 0))
    y = int(bounds.get('Y', 0))
    width = int(bounds.get('Width', 0))
    height = int(bounds.get('Height', 0))
    
    if width == 0 or height == 0:
        return None
    
    # Create window ID
    window_id = window_info.get('kCGWindowNumber', 0)
    
    try:
        # Capture the window image
        image_ref = CGWindowListCreateImage(
            CGRectMake(x, y, width, height),
            kCGWindowListOptionIncludingWindow,
            window_id,
            kCGWindowImageDefault
        )
        
        if image_ref is None:
            return None
        
        # Convert CGImageRef to numpy array using AppKit
        import AppKit
        import io
        bitmap = AppKit.NSBitmapImageRep.alloc().initWithCGImage_(image_ref)
        data = bitmap.representationUsingType_properties_(AppKit.NSBitmapImageFileTypePNG, None)
        
        # Read PNG data into PIL Image
        img = Image.open(io.BytesIO(data))
        
        # Convert color space if ICC profile exists (before mode conversion)
        if 'icc_profile' in img.info:
            try:
                # Convert from embedded ICC profile to sRGB
                img = ImageCms.profileToProfile(img, ImageCms.ImageCmsProfile(io.BytesIO(img.info['icc_profile'])), ImageCms.createProfile('sRGB'))
            except Exception as cms_error:
                # If color space conversion fails, continue without it
                print(f"Warning: ICC profile conversion failed: {cms_error}")
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        return np.array(img)
    
    except Exception as e:
        print(f"Error capturing window: {e}")
        return None


def process_stream(window_info, idx, weights_path, output_dir, stop_event):
    '''
    Continuously process video stream from a scrcpy window.
    
    Args:
        window_info (dict): Window information dictionary from Quartz API.
        idx (int): Window index.
        weights_path (str): Path to YOLO weights file.
        output_dir (str): Output directory for results.
        stop_event: Threading event to signal stop.
    '''
    import os
    import time
    from datetime import datetime
    
    window_title = window_info.get('kCGWindowName', f'Window_{idx}')
    output_file = os.path.join(output_dir, f'phone{idx}.txt')
    
    print(f"  → Started stream processing for window {idx + 1}: {window_title[:50]}")
    
    last_cards = None
    confirmed_cards = None  # Store the last confirmed pair of cards
    last_detection_time = 0  # Track when 2 cards were last detected
    
    while not stop_event.is_set():
        try:
            # Check if we need to pause after detecting 2 cards
            if time.time() - last_detection_time < 3.0:
                # Still in 3-second buffer period, skip this frame
                time.sleep(0.1)
                continue
            
            # Capture screenshot
            screenshot = capture_window_screenshot(window_info)
            
            if screenshot is None:
                time.sleep(0.5)  # Wait before retry
                continue
            
            # Detect cards
            cards = detect_cards(screenshot, weights_path)
            
            # Only update output if cards changed
            if cards != last_cards:
                last_cards = cards
                
                # Print status
                if len(cards) > 0:
                    print(f"    ✓ Window {idx + 1}: {len(cards)} card(s) - {', '.join(cards)}")
                else:
                    print(f"    → Window {idx + 1}: No cards detected")
                
                # Update confirmed_cards and write to file if we have exactly 2 cards
                if len(cards) == 2:
                    confirmed_cards = cards
                    decoded_cards = decode_cards(cards)
                    card_output = "\n".join(decoded_cards)
                    
                    # Write to file
                    try:
                        with open(output_file, 'w') as f:
                            f.write(f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                            f.write(f"Window: {window_title}\n")
                            f.write(f"Cards Detected: {len(cards)}\n")
                            f.write("=" * 40 + "\n")
                            f.write(card_output + "\n")
                        # f.flush() is automatically called when exiting 'with' block
                    except Exception as write_error:
                        print(f"    ❌ Error writing to file: {write_error}")
                    
                    # Start 3-second buffer period
                    last_detection_time = time.time()
            
            # Small delay to prevent excessive CPU usage
            time.sleep(0.1)
            
        except Exception as e:
            print(f"    ❌ Error processing window {idx}: {e}")
            time.sleep(1)  # Wait before retry on error
    
    print(f"  → Stopped stream processing for window {idx + 1}")


def main():
    '''
    Main function to detect cards from multiple scrcpy windows in real-time.
    '''
    import os
    import signal
    import threading
    
    weights_path = 'weights/poker_best.pt'
    
    print("Checking for scrcpy windows...")
    scrcpy_windows = find_scrcpy_windows()
    
    if len(scrcpy_windows) == 0:
        print("\n❌ ERROR: No scrcpy windows detected.")
        print("Please ensure:")
        print("  1. scrcpy is installed and running")
        print("  2. At least one Android device is connected via USB")
        print("  3. scrcpy windows are visible on screen")
        exit(1)
    
    print(f"✓ Found {len(scrcpy_windows)} scrcpy window(s)")
    
    # Create output directory if it doesn't exist
    output_dir = 'cards_detected'
    os.makedirs(output_dir, exist_ok=True)
    
    print("\nStarting real-time card detection...")
    print("Processing video streams from scrcpy windows...")
    print("Press Ctrl+C to stop.\n")
    
    # Create stop event for threads
    stop_event = threading.Event()
    threads = []
    
    # Start a thread for each scrcpy window
    for idx, window_info in enumerate(scrcpy_windows):
        thread = threading.Thread(
            target=process_stream,
            args=(window_info, idx, weights_path, output_dir, stop_event),
            daemon=True
        )
        thread.start()
        threads.append(thread)
    
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\n\nStopping card detection...")
        stop_event.set()
        for thread in threads:
            thread.join(timeout=2)
        print("✓ All streams stopped")
        print(f"Results saved to '{output_dir}/' directory")
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Keep main thread alive
    try:
        while True:
            threading.Event().wait(timeout=1)
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == '__main__':
    # Check if running with scrcpy mode (command line argument or no args)
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--scrcpy':
        # Run in scrcpy mode
        main()
    elif len(sys.argv) == 1:
        # Default: run in scrcpy mode (no arguments)
        main()
    else:
        # Legacy mode: Test on images
        # Test on the first image
        image_path = 'images/test_img_1.png'
        weights_path = 'weights/poker_best.pt'
        cards = detect_cards(image_path, weights_path)
        print("\n".join(decode_cards(cards)))

        # Test on the second image
        image_path = 'images/test_img_2.png'
        weights_path = 'weights/poker_best.pt'
        cards = detect_cards(image_path, weights_path)
        print("\n".join(decode_cards(cards)))

        # Test on the third image
        image_path = 'images/test_img_3.png'
        weights_path = 'weights/poker_best.pt'
        cards = detect_cards(image_path, weights_path)
        print("\n".join(decode_cards(cards)))