from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID

# Get a list of all on-screen windows
window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)

print(f"Found {len(window_list)} windows.")
print("--- Window Owners ---")

app_names = set()
for window in window_list:
    # Each 'window' is a dictionary
    app_name = window.get('kCGWindowOwnerName', 'Unknown')
    app_names.add(app_name)

for name in sorted(app_names):
    print(name)