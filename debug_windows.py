"""
Debug script to list all visible windows on Windows.
This helps identify what scrcpy windows are actually called.
"""

import platform

if platform.system() == 'Windows':
    try:
        import win32gui
        import win32con
        
        print("=== All Visible Windows on Windows ===\n")
        
        all_windows = []
        
        def enum_handler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                
                # Skip empty windows
                if window_text or class_name:
                    rect = win32gui.GetWindowRect(hwnd)
                    left, top, right, bottom = rect
                    width = right - left
                    height = bottom - top
                    
                    # Skip very small windows (likely tooltips, etc.)
                    if width > 50 and height > 50:
                        all_windows.append({
                            'hwnd': hwnd,
                            'title': window_text,
                            'class': class_name,
                            'size': f"{width}x{height}"
                        })
        
        win32gui.EnumWindows(enum_handler, None)
        
        # Sort by title for easier reading
        all_windows.sort(key=lambda x: x['title'].lower())
        
        print(f"Found {len(all_windows)} visible windows:\n")
        print(f"{'Title':<60} {'Class Name':<40} {'Size'}")
        print("-" * 110)
        
        for window in all_windows:
            title = window['title'] or '(No title)'
            class_name = window['class']
            size = window['size']
            print(f"{title:<60} {class_name:<40} {size}")
        
        # Now check specifically for scrcpy
        print("\n\n=== Checking for 'scrcpy' in windows ===")
        scrcpy_windows = []
        for window in all_windows:
            if 'scrcpy' in window['title'].lower() or 'scrcpy' in window['class'].lower():
                scrcpy_windows.append(window)
        
        if scrcpy_windows:
            print(f"\nFound {len(scrcpy_windows)} window(s) containing 'scrcpy':\n")
            for i, window in enumerate(scrcpy_windows, 1):
                print(f"{i}. Title: '{window['title']}'")
                print(f"   Class: '{window['class']}'")
                print(f"   Size: {window['size']}\n")
        else:
            print("\n❌ No windows found containing 'scrcpy'")
            print("\n💡 Tips:")
            print("   1. Make sure scrcpy window is visible (not minimized)")
            print("   2. Check if the window title contains 'scrcpy' (case-insensitive)")
            print("   3. The window might be a child window - check all windows above")
            print("   4. Try searching for 'android' or 'device' in the window list above")
        
        # Check for common alternatives
        print("\n\n=== Checking for Android/Device related windows ===")
        android_windows = []
        keywords = ['android', 'device', 'phone', 'mobile', 'adb', 'screen', 'mirror']
        for window in all_windows:
            title_lower = window['title'].lower()
            class_lower = window['class'].lower()
            for keyword in keywords:
                if keyword in title_lower or keyword in class_lower:
                    android_windows.append((window, keyword))
                    break
        
        if android_windows:
            print(f"\nFound {len(android_windows)} potentially related window(s):\n")
            for window, keyword in android_windows:
                print(f"  Title: '{window['title']}' (matched keyword: '{keyword}')")
                print(f"  Class: '{window['class']}'")
                print(f"  Size: {window['size']}\n")
        
    except ImportError:
        print("ERROR: pywin32 is not installed. Install it with: pip install pywin32")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"This script is for Windows only. Current platform: {platform.system()}")
    print("For macOS, use the existing test_window_search.py script.")

