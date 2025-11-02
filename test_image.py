"""
Test script for card detection on static images.
Uses the legacy image mode from detect_cards.py
"""

from detect_cards import detect_cards, decode_cards

# Test on images from the images folder
test_images = [
    'debug_raw_capture.png'
]

weights_path = 'weights/poker_best.pt'

print("=" * 60)
print("Testing Card Detection on Static Images")
print("=" * 60)

for image_path in test_images:
    print(f"\nTesting: {image_path}")
    
    try:
        cards = detect_cards(image_path, weights_path)
        
        if len(cards) > 0:
            print(f"✓ Detected {len(cards)} card(s): {', '.join(cards)}")
            decoded = decode_cards(cards)
            for card in decoded:
                print(f"  - {card}")
        else:
            print("→ No cards detected")
            
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("Testing complete!")

