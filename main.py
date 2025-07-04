from cvzone.HandTrackingModule import HandDetector
import cv2
import os
import numpy as np

# Parameters
width, height = 1920, 1080
gestureThreshold = 300
folderPath = "Presentation"

# Camera Setup
camera_width, camera_height = 320, 240  # Reduced camera resolution
cap = cv2.VideoCapture(0)
cap.set(3, camera_width)
cap.set(4, camera_height)

# Hand Detector
detectorHand = HandDetector(detectionCon=0.8, maxHands=1)

# Variables
imgList = []
delay = 30
buttonPressed = False
counter = 0
imgNumber = 0
delayCounter = 0
annotations = [[]]
annotationNumber = -1
annotationStart = False
hs, ws = camera_height, camera_width  # width and height of small image

# Get list of presentation images
pathImages = sorted(os.listdir(folderPath), key=len)
print(pathImages)

while True:
    # Get image frame
    success, img = cap.read()

    pathFullImage = os.path.join(folderPath, pathImages[imgNumber])
    imgCurrent = cv2.imread(pathFullImage)

    # Find the hand and its landmarks
    hands, img = detectorHand.findHands(img)  # with draw
    # Draw Gesture Threshold line
    cv2.line(img, (0, gestureThreshold), (width, gestureThreshold), (0, 255, 0), 10)

    if hands and buttonPressed is False:  # If hand is detected
        hand = hands[0]
        cx, cy = hand["center"]
        lmList = hand["lmList"]  # List of 21 Landmark points
        fingers = detectorHand.fingersUp(hand)  # List of which fingers are up

        # Mirror x-coordinates to match flipped image
        for point in lmList:
            point[0] = camera_width - point[0]

        # Constrain values for easier drawing
        xVal = int(np.interp(lmList[8][0], [0, camera_width], [0, width]))
        yVal = int(np.interp(lmList[8][1], [0, camera_height], [0, height]))
        indexFinger = xVal, yVal

        # Slide change gestures
        if cy <= gestureThreshold:  # If hand is at the height of the face
            if fingers == [1, 0, 0, 0, 0]:  # Thumb and Pinky Up
                print("Previous Slide")
                buttonPressed = True
                if imgNumber > 0:
                    imgNumber -= 1
                    annotations = [[]]
                    annotationNumber = -1
                    annotationStart = False
            if fingers == [0, 0, 0, 0, 1]:  # Pinky Up
                print("Next Slide")
                buttonPressed = True
                if imgNumber < len(pathImages) - 1:
                    imgNumber += 1
                    annotations = [[]]
                    annotationNumber = -1
                    annotationStart = False

        # Pointer Gesture: Index and Thumb up (gun shape)
        if fingers == [1, 1, 0, 0, 0]:  # Pointer Mode
            print("Pointer Mode Active")
            cv2.circle(imgCurrent, indexFinger, 20, (0, 255, 0), cv2.FILLED)

        # Erase All Annotations Gesture
        if fingers == [1, 1, 1, 0, 0]:  # Fist
            print("Erasing All Annotations")
            annotations = [[]]
            annotationNumber = -1
            annotationStart = False
            buttonPressed = True

        # Drawing Mode: Index finger only
        if fingers == [0, 1, 0, 0, 0]:
            if annotationStart is False:
                annotationStart = True
                annotationNumber += 1
                annotations.append([])
            annotations[annotationNumber].append(indexFinger)
            cv2.circle(imgCurrent, indexFinger, 12, (0, 0, 255), cv2.FILLED)
        else:
            annotationStart = False

        # Undo last annotation
        if fingers == [0, 1, 1, 1, 0]:
            if annotations:
                annotations.pop(-1)
                annotationNumber -= 1
                buttonPressed = True

    if buttonPressed:
        counter += 1
        if counter > delay:
            counter = 0
            buttonPressed = False

    # Draw annotations
    for annotation in annotations:
        for j in range(len(annotation)):
            if j != 0:
                cv2.line(imgCurrent, annotation[j - 1], annotation[j], (0, 0, 200), 12)

    # Resize and place the camera feed in the top-right corner
    imgSmall = cv2.resize(img, (camera_width, camera_height))
    h, w, _ = imgCurrent.shape
    x_offset = w - camera_width
    y_offset = 0
    imgCurrent[y_offset:y_offset + camera_height, x_offset:x_offset + camera_width] = imgSmall

    # Display the slides and the small camera feed
    cv2.imshow("Slides", imgCurrent)
    cv2.imshow("Image", img)

    key = cv2.waitKey(1)
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()