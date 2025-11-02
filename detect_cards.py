from ultralytics import YOLO
import numpy as np
from PIL import Image
import platform

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
    Finds all scrcpy windows across different platforms (Windows, macOS, Linux).
    
    Returns:
        list: List of dictionaries containing window information with title, bounds, etc.
    '''
    system = platform.system()
    
    if system == 'Darwin':  # macOS
        return _find_scrcpy_windows_macos()
    elif system == 'Windows':
        return _find_scrcpy_windows_windows()
    elif system == 'Linux':
        return _find_scrcpy_windows_linux()
    else:
        raise NotImplementedError(f"Unsupported platform: {system}")


def _find_scrcpy_windows_macos():
    '''macOS implementation using Quartz API.'''
    try:
        from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
        
        window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
        
        # Filter for scrcpy windows
        scrcpy_windows = []
        for window in window_list:
            owner = window.get('kCGWindowOwnerName', '')
            title = window.get('kCGWindowName', '')
            
            # Look for windows with 'scrcpy' in the owner or title
            if 'scrcpy' in owner.lower() or 'scrcpy' in title.lower():
                # Normalize window info to match expected format
                bounds = window.get('kCGWindowBounds', {})
                scrcpy_windows.append({
                    'title': title,
                    'owner': owner,
                    'window_id': window.get('kCGWindowNumber', 0),
                    'bounds': {
                        'X': bounds.get('X', 0),
                        'Y': bounds.get('Y', 0),
                        'Width': bounds.get('Width', 0),
                        'Height': bounds.get('Height', 0)
                    },
                    '_platform': 'macos',
                    '_raw_info': window  # Keep raw info for screenshot
                })
        
        return scrcpy_windows
    except ImportError:
        raise ImportError("PyObjC (Quartz) is required on macOS. Install with: pip install pyobjc-framework-Quartz")


def _find_scrcpy_windows_windows():
    '''Windows implementation using pywin32.'''
    try:
        import win32gui
        import win32con
        
        scrcpy_windows = []
        
        def enum_handler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                
                # Get window rectangle to check size
                try:
                    rect = win32gui.GetWindowRect(hwnd)
                    left, top, right, bottom = rect
                    width = right - left
                    height = bottom - top
                except:
                    return
                
                # Skip very small windows (likely not the main scrcpy window)
                if width < 100 or height < 100:
                    return
                
                # Look for scrcpy windows - check multiple criteria
                window_text_lower = window_text.lower()
                class_name_lower = class_name.lower()
                
                # Check for 'scrcpy' in title or class
                # Also check for common scrcpy window class names
                is_scrcpy = (
                    'scrcpy' in window_text_lower or 
                    'scrcpy' in class_name_lower or
                    class_name_lower == 'wxwindowclassnr'  # Common scrcpy window class on Windows
                )
                
                if is_scrcpy:
                    scrcpy_windows.append({
                        'title': window_text,
                        'owner': class_name,
                        'window_id': hwnd,
                        'bounds': {
                            'X': left,
                            'Y': top,
                            'Width': width,
                            'Height': height
                        },
                        '_platform': 'windows'
                    })
        
        win32gui.EnumWindows(enum_handler, None)
        return scrcpy_windows
    except ImportError:
        raise ImportError("pywin32 is required on Windows. Install with: pip install pywin32")


def _find_scrcpy_windows_linux():
    '''Linux implementation using Xlib or fallback method.'''
    try:
        from Xlib import display
        from Xlib import X
        
        d = display.Display()
        root = d.screen().root
        
        # Get all windows
        windows = root.query_tree().children
        
        scrcpy_windows = []
        
        for window in windows:
            try:
                # Get window name
                window_name = window.get_wm_name()
                window_class = window.get_wm_class()
                
                if window_name and 'scrcpy' in window_name.lower():
                    # Get window geometry
                    geom = window.get_geometry()
                    
                    scrcpy_windows.append({
                        'title': window_name,
                        'owner': window_class[0] if window_class else '',
                        'window_id': window.id,
                        'bounds': {
                            'X': geom.x,
                            'Y': geom.y,
                            'Width': geom.width,
                            'Height': geom.height
                        },
                        '_platform': 'linux',
                        '_raw_window': window  # Keep raw window for screenshot
                    })
            except:
                continue
        
        return scrcpy_windows
    except ImportError:
        # Fallback: try using wmctrl if available, or return empty list
        import subprocess
        try:
            result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                scrcpy_windows = []
                for line in result.stdout.split('\n'):
                    if 'scrcpy' in line.lower():
                        parts = line.split(None, 3)
                        if len(parts) >= 4:
                            scrcpy_windows.append({
                                'title': parts[3],
                                'owner': '',
                                'window_id': parts[0],
                                'bounds': {'X': 0, 'Y': 0, 'Width': 0, 'Height': 0},
                                '_platform': 'linux'
                            })
                return scrcpy_windows
        except:
            pass
        
        raise ImportError("python-xlib is required on Linux. Install with: pip install python-xlib")


def capture_window_screenshot(window_info):
    '''
    Captures a screenshot of a specific window across different platforms.
    
    Args:
        window_info (dict): Window information dictionary from platform-specific API.
        
    Returns:
        np.ndarray or None: Image as numpy array, or None if capture failed.
    '''
    platform_type = window_info.get('_platform', platform.system().lower())
    
    if platform_type == 'macos':
        return _capture_window_screenshot_macos(window_info)
    elif platform_type == 'windows':
        return _capture_window_screenshot_windows(window_info)
    elif platform_type == 'linux':
        return _capture_window_screenshot_linux(window_info)
    else:
        raise NotImplementedError(f"Unsupported platform: {platform_type}")


def _capture_window_screenshot_macos(window_info):
    '''macOS implementation using Quartz API.'''
    try:
        from Quartz import CGWindowListCreateImage, CGRectMake, kCGWindowImageDefault, kCGWindowListOptionIncludingWindow
        import AppKit
        import io
        
        # Get window bounds - use normalized format
        bounds = window_info.get('bounds', {})
        x = int(bounds.get('X', 0))
        y = int(bounds.get('Y', 0))
        width = int(bounds.get('Width', 0))
        height = int(bounds.get('Height', 0))
        
        if width == 0 or height == 0:
            return None
        
        # Create window ID
        window_id = window_info.get('window_id', 0)
        if window_id == 0:
            # Fallback to raw_info if available
            raw_info = window_info.get('_raw_info', {})
            if raw_info:
                window_id = raw_info.get('kCGWindowNumber', 0)
                # Get bounds from raw_info if not in normalized format
                if not bounds:
                    raw_bounds = raw_info.get('kCGWindowBounds', {})
                    x = int(raw_bounds.get('X', 0))
                    y = int(raw_bounds.get('Y', 0))
                    width = int(raw_bounds.get('Width', 0))
                    height = int(raw_bounds.get('Height', 0))
        
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
            bitmap = AppKit.NSBitmapImageRep.alloc().initWithCGImage_(image_ref)
            data = bitmap.representationUsingType_properties_(AppKit.NSBitmapImageFileTypePNG, None)
            
            # Read PNG data into PIL Image
            img = Image.open(io.BytesIO(data))
            
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            return np.array(img)
        except Exception as e:
            print(f"Error capturing window on macOS: {e}")
            return None
    except ImportError:
        raise ImportError("PyObjC (Quartz, AppKit) is required on macOS. Install with: pip install pyobjc-framework-Quartz")


def _capture_window_screenshot_windows(window_info):
    '''Windows implementation using pywin32.'''
    try:
        import win32gui
        import win32ui
        import win32con
        from ctypes import windll
        
        window_id = window_info.get('window_id', 0)
        bounds = window_info.get('bounds', {})
        
        if window_id == 0:
            return None
        
        # Get window rectangle
        left, top, right, bottom = win32gui.GetWindowRect(window_id)
        width = right - left
        height = bottom - top
        
        if width == 0 or height == 0:
            return None
        
        try:
            # Create device context
            hwndDC = win32gui.GetWindowDC(window_id)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            
            # Create bitmap
            bitmap = win32ui.CreateBitmap()
            bitmap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(bitmap)
            
            # Copy window content
            result = windll.user32.PrintWindow(window_id, saveDC.GetSafeHdc(), 3)
            
            # Convert to PIL Image
            if result == 1:
                bmpinfo = bitmap.GetInfo()
                bmpstr = bitmap.GetBitmapBits(True)
                
                # Windows bitmap is in BGRA format, convert to RGB using numpy
                width = bmpinfo['bmWidth']
                height = bmpinfo['bmHeight']
                
                # Convert bytes to numpy array (BGRA format, stored bottom-to-top)
                img_array = np.frombuffer(bmpstr, dtype=np.uint8).reshape((height, width, 4))
                
                # Flip vertically (Windows bitmaps are stored bottom-to-top)
                img_array = np.flipud(img_array)
                
                # Convert BGRA to RGB by extracting B, G, R channels (discard alpha)
                img_rgb = img_array[:, :, [2, 1, 0]]
                
                # Clean up
                win32gui.DeleteObject(bitmap.GetHandle())
                saveDC.DeleteDC()
                mfcDC.DeleteDC()
                win32gui.ReleaseDC(window_id, hwndDC)
                
                return img_rgb
            else:
                # Clean up on failure
                win32gui.DeleteObject(bitmap.GetHandle())
                saveDC.DeleteDC()
                mfcDC.DeleteDC()
                win32gui.ReleaseDC(window_id, hwndDC)
                return None
        except Exception as e:
            print(f"Error capturing window on Windows: {e}")
            return None
    except ImportError:
        raise ImportError("pywin32 is required on Windows. Install with: pip install pywin32")


def _capture_window_screenshot_linux(window_info):
    '''Linux implementation using Xlib or mss fallback.'''
    try:
        from Xlib import display
        from Xlib import X
        import io
        
        raw_window = window_info.get('_raw_window')
        if raw_window is None:
            # Fallback to mss if Xlib window not available
            return _capture_window_screenshot_linux_mss(window_info)
        
        d = display.Display()
        bounds = window_info.get('bounds', {})
        
        x = int(bounds.get('X', 0))
        y = int(bounds.get('Y', 0))
        width = int(bounds.get('Width', 0))
        height = int(bounds.get('Height', 0))
        
        if width == 0 or height == 0:
            return None
        
        try:
            # Get window image using XGetImage
            # Use 0,0 for offset since we want the window content from top-left
            image = raw_window.get_image(0, 0, width, height, X.ZPixmap, 0xffffffff)
            
            # Convert Xlib image to PIL Image
            img = Image.frombytes('RGB', (width, height), image.data, 'raw', 'BGRX')
            
            return np.array(img)
        except Exception as e:
            print(f"Error capturing window on Linux (Xlib): {e}")
            return _capture_window_screenshot_linux_mss(window_info)
    except ImportError:
        # Fallback to mss
        return _capture_window_screenshot_linux_mss(window_info)


def _capture_window_screenshot_linux_mss(window_info):
    '''Linux fallback implementation using mss (less accurate but works).'''
    try:
        import mss
        
        bounds = window_info.get('bounds', {})
        x = int(bounds.get('X', 0))
        y = int(bounds.get('Y', 0))
        width = int(bounds.get('Width', 0))
        height = int(bounds.get('Height', 0))
        
        if width == 0 or height == 0:
            return None
        
        with mss.mss() as sct:
            # Capture the region
            monitor = {'top': y, 'left': x, 'width': width, 'height': height}
            screenshot = sct.grab(monitor)
            
            # Convert to PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
            
            return np.array(img)
    except ImportError:
        raise ImportError("mss is required on Linux as fallback. Install with: pip install mss")
    except Exception as e:
        print(f"Error capturing window on Linux (mss): {e}")
        return None


def process_stream(window_info, idx, weights_path, output_dir, stop_event):
    '''
    Continuously process video stream from a scrcpy window.
    
    Args:
        window_info (dict): Window information dictionary from platform-specific API.
        idx (int): Window index.
        weights_path (str): Path to YOLO weights file.
        output_dir (str): Output directory for results.
        stop_event: Threading event to signal stop.
    '''
    import os
    import time
    from datetime import datetime
    
    window_title = window_info.get('title', window_info.get('kCGWindowName', f'Window_{idx}'))
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