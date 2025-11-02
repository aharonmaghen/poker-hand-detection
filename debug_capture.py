import AppKit
import io
import os
from PIL import Image
from Quartz import (
    CGWindowListCreateImage,
    CGRectMake,
    kCGWindowImageDefault,
    kCGWindowListOptionIncludingWindow,
    CGWindowListCopyWindowInfo,
    kCGWindowListOptionOnScreenOnly,
    kCGNullWindowID
)

def find_scrcpy_window():
    """Finds the main scrcpy window."""
    window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
    for window in window_list:
        owner_name = window.get('kCGWindowOwnerName', '')
        window_layer = window.get('kCGWindowLayer', -1)
        # Find the main scrcpy window (layer 0)
        if owner_name == 'scrcpy' and window_layer == 0:
            return window
    return None

def capture_raw_window(window_info):
    """
    Captures a "raw" screenshot using the original fast method,
    WITHOUT any color correction.
    """
    bounds = window_info.get("kCGWindowBounds", {})
    x = int(bounds.get("X", 0))
    y = int(bounds.get("Y", 0))
    width = int(bounds.get("Width", 0))
    height = int(bounds.get("Height", 0))

    if width == 0 or height == 0:
        return None

    window_id = window_info.get("kCGWindowNumber", 0)

    try:
        # 1. Capture the fast, raw window image (in Display P3)
        image_ref = CGWindowListCreateImage(
            CGRectMake(x, y, width, height),
            kCGWindowListOptionIncludingWindow,
            window_id,
            kCGWindowImageDefault,
        )

        if image_ref is None:
            return None

        # 2. Convert to PIL Image
        bitmap = AppKit.NSBitmapImageRep.alloc().initWithCGImage_(image_ref)
        data = bitmap.representationUsingType_properties_(
            AppKit.NSBitmapImageFileTypePNG, None
        )
        
        # 3. Return the raw, uncorrected PIL image
        img = Image.open(io.BytesIO(data))
        return img

    except Exception as e:
        print(f"Error capturing raw window: {e}")
        return None

if __name__ == "__main__":
    print("Finding scrcpy window...")
    scrcpy_window = find_scrcpy_window()
    
    if scrcpy_window:
        print("Found window. Capturing raw, uncorrected image...")
        
        # This is the image as your script sees it
        raw_image = capture_raw_window(scrcpy_window)
        
        if raw_image:
            save_path = "debug_raw_capture.png"
            # Save the image to a file
            raw_image.save(save_path)
            
            print(f"\n--- SUCCESS ---")
            print(f"Raw, uncorrected image saved to: {os.path.abspath(save_path)}")
            print("Open this file to see what your script sees.")
        else:
            print("Error: Failed to capture the image.")
    else:
        print("Error: scrcpy window not found. Is it running?")