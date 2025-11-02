"""
Script to capture a screenshot of a scrcpy window and save it to images/
"""

from detect_cards import find_scrcpy_windows, capture_window_screenshot
from PIL import Image
import os

def capture_scrcpy_screenshot():
    '''
    Capture a screenshot from a scrcpy window and save it.
    '''
    print("Finding scrcpy windows...")
    scrcpy_windows = find_scrcpy_windows()
    
    if len(scrcpy_windows) == 0:
        print("\n❌ ERROR: No scrcpy windows detected.")
        print("Please ensure scrcpy is running with at least one device connected.")
        return False
    
    print(f"✓ Found {len(scrcpy_windows)} scrcpy window(s)")
    
    # Capture the first scrcpy window
    window_info = scrcpy_windows[0]
    window_title = window_info.get('kCGWindowName', 'scrcpy')
    
    print(f"\nCapturing screenshot from: {window_title}")
    
    # Capture the screenshot
    screenshot_array = capture_window_screenshot(window_info)
    
    if screenshot_array is None:
        print("❌ Failed to capture screenshot")
        return False
    
    # Convert numpy array to PIL Image
    img = Image.fromarray(screenshot_array)
    
    # Save to images directory
    output_dir = 'images'
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate unique filename with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'scrcpy_screenshot_{timestamp}.png')
    
    img.save(output_file)
    print(f"✓ Screenshot saved to: {output_file}")
    print(f"  Size: {img.size[0]}x{img.size[1]}")
    
    return True

if __name__ == '__main__':
    capture_scrcpy_screenshot()

