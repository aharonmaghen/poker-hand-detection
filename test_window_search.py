from detect_cards import find_scrcpy_windows
import platform

# Get a list of all on-screen windows (cross-platform)
print(f"Platform: {platform.system()}")
print("Finding windows...")

try:
    windows = find_scrcpy_windows()
    print(f"\nFound {len(windows)} scrcpy window(s).")
    
    if len(windows) > 0:
        print("\n--- Window Details ---")
        for i, window in enumerate(windows):
            print(f"\nWindow {i+1}:")
            print(f"  Title: {window.get('title', 'N/A')}")
            print(f"  Owner: {window.get('owner', 'N/A')}")
            bounds = window.get('bounds', {})
            print(f"  Position: ({bounds.get('X', 0)}, {bounds.get('Y', 0)})")
            print(f"  Size: {bounds.get('Width', 0)}x{bounds.get('Height', 0)}")
    
    # Also show all window owners if on macOS for debugging
    if platform.system() == 'Darwin':
        try:
            from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
            window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
            print(f"\n--- All Window Owners (macOS) ---")
            app_names = set()
            for window in window_list:
                app_name = window.get('kCGWindowOwnerName', 'Unknown')
                app_names.add(app_name)
            for name in sorted(app_names):
                print(name)
        except ImportError:
            pass
except Exception as e:
    print(f"Error: {e}")