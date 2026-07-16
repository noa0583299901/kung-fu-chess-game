import cv2
import numpy as np

data = np.fromfile(r"CTD26/pieces1/PW/states/idle/sprites/1.png", dtype=np.uint8)
img = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
print("Image shape:", img.shape)  # 3 channels = BGR

# מחפש pixels כחולים (BGR: B high)
h, w = img.shape[:2]
blues = img[(img[:,:,0] > 100) & (img[:,:,2] < 100)]
print(f"Blue pixels (B>100, R<100): {len(blues)}")
if len(blues) > 0:
    print(f"  B range: {blues[:,0].min()}-{blues[:,0].max()}")
    print(f"  G range: {blues[:,1].min()}-{blues[:,1].max()}")
    print(f"  R range: {blues[:,2].min()}-{blues[:,2].max()}")
else:
    # Try wider
    print("Trying wider filter...")
    blues2 = img[(img[:,:,0] > 80)]
    print(f"  B>80: {len(blues2)} pixels")
    # Sample unique bright non-grayscale pixels
    for y in range(0, h, 5):
        for x in range(0, w, 5):
            b, g, r = img[y, x]
            if abs(int(b)-int(g)) > 30 or abs(int(b)-int(r)) > 30:
                if b > 80 or g > 80 or r > 80:
                    print(f"  ({x},{y}): B={b} G={g} R={r}")
