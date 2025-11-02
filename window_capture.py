"""
Window Capture Utility for Windows
כלי לכידת חלון ל-Windows

Captures content from a specific window by title.
לוכד תוכן מחלון ספציפי לפי כותרת.
"""

import win32gui
import win32ui
import win32con
import numpy as np
import cv2

def find_window_by_title(title_keywords):
    """
    Find window handle by title keywords.
    מוצא handle של חלון לפי מילות מפתח בכותרת.
    
    Args:
        title_keywords: List of keywords that should be in the window title (case-insensitive)
        
    Returns:
        Window handle (hwnd) or None if not found
    """
    def enum_handler(hwnd, results):
        if win32gui.IsWindowVisible(hwnd):
            window_title = win32gui.GetWindowText(hwnd).lower()
            # Check if any keyword is in the title
            if any(keyword.lower() in window_title for keyword in title_keywords):
                results.append((hwnd, win32gui.GetWindowText(hwnd)))
    
    results = []
    win32gui.EnumWindows(enum_handler, results)
    
    if results:
        return results[0][0]  # Return first match's handle
    return None

def capture_window(hwnd):
    """
    Capture the content of a window by its handle.
    לוכד את התוכן של חלון לפי handle שלו.
    
    Args:
        hwnd: Window handle
        
    Returns:
        numpy array (BGR format) or None if failed
    """
    try:
        # Get window dimensions
        left, top, right, bottom = win32gui.GetWindowRect(hwnd)
        width = right - left
        height = bottom - top
        
        if width <= 0 or height <= 0:
            return None
        
        # Get device context
        hwnd_dc = win32gui.GetWindowDC(hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()
        
        # Create bitmap
        bitmap = win32ui.CreateBitmap()
        bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
        save_dc.SelectObject(bitmap)
        
        # Copy window content to bitmap
        save_dc.BitBlt((0, 0), (width, height), mfc_dc, (0, 0), win32con.SRCCOPY)
        
        # Convert to numpy array
        bits = bitmap.GetBitmapBits(True)
        img = np.frombuffer(bits, dtype=np.uint8).reshape((height, width, 4))
        
        # Convert BGRA to BGR (remove alpha channel)
        img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        # Cleanup
        win32gui.DeleteObject(bitmap.GetHandle())
        save_dc.DeleteDC()
        mfc_dc.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwnd_dc)
        
        return img_bgr
        
    except Exception as e:
        print(f"Error capturing window: {e}")
        print(f"שגיאה בלכידת חלון: {e}")
        return None

def list_windows_with_keywords(keywords):
    """
    List all visible windows that contain the keywords.
    מציג רשימה של כל החלונות הנראים שמכילים את מילות המפתח.
    """
    def enum_handler(hwnd, results):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and any(kw.lower() in title.lower() for kw in keywords):
                results.append((hwnd, title))
    
    results = []
    win32gui.EnumWindows(enum_handler, results)
    return results

def list_all_visible_windows():
    """
    List all visible windows (for debugging).
    מציג רשימה של כל החלונות הנראים (לדיבוג).
    """
    def enum_handler(hwnd, results):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:  # Only windows with titles
                left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                width = right - left
                height = bottom - top
                if width > 0 and height > 0:  # Valid size
                    results.append((hwnd, title, width, height))
    
    results = []
    win32gui.EnumWindows(enum_handler, results)
    return results

