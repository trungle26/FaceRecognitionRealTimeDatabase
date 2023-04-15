import os
import pickle

import cv2
import cvzone
import face_recognition
import numpy as np
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage

from flask import Flask, jsonify, request
from flask_cors import CORS
from PIL import Image

app = Flask(__name__)
CORS(app)


@app.route('/api/is_image_valid', methods=['POST'])
def is_image_valid():
    # Check if the request contains an image file
    if 'image' not in request.files:
        return jsonify({'valid': False, 'message': 'No image provided'})

    # Open the image file using the Pillow library
    image = Image.open(request.files['image'].stream)

    # Check if the image is valid
    try:
        # xu ly anh
        return jsonify({'valid': True})
    except:
        return jsonify({'valid': False, 'message': 'Invalid image file'})


if __name__ == '__main__':
    app.run()

#-----
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://faceattendancerealtime-c6597-default-rtdb.asia-southeast1.firebasedatabase.app/',
    'storageBucket': 'faceattendancerealtime-c6597.appspot.com'
})
bucket = storage.bucket()

# cap = cv2.VideoCapture(0)
# cap.set(3, 640)
# cap.set(4, 480)

imgBackground = cv2.imread('Resources/background.png')



# load the encoding file
print('loading encode file...')
file = open("EncodeFile.p", 'rb')
encodeListKnownWithIds = pickle.load(file)
file.close()
encodeListKnown, studentIds = encodeListKnownWithIds
# print(studentIds)
print('encode file loaded')

modeType = 0
counter = 0
id = -1
imgStudent = []

while True:
    success, img = cap.read()

    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)  # encode phan mat tren webcam

    imgBackground[162:162 + 480, 55:55 + 640] = img
    imgBackground[44:44 + 633, 808:808 + 414] = imgModeList[modeType]

    for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
        matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
        # print("matches",matches)
        # print("faceDis",faceDis) #facedis cang thap thi cang giong

        matchIndex = np.argmin(faceDis)
        if matches[matchIndex]:
            # print("known face detected")
            # print(studentIds[matchIndex])
            y1, x2, y2, x1 = faceLoc
            y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
            bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
            imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
            id = studentIds[matchIndex]

            if counter == 0:
                counter = 1
                modeType = 1
    if counter != 0:
        if counter == 1:
            # get data
            studentInfo = db.reference('Students/' + id).get()
            print(studentInfo)
            # get image from storage
            blob = bucket.get_blob('Images/' + id + '.png')
            array = np.frombuffer(blob.download_as_string(), np.uint8)
            imgStudent = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)

        cv2.putText(imgBackground, str(studentInfo['total_attendance']), (861, 125), cv2.FONT_HERSHEY_COMPLEX, 1,
                    (0, 0, 255), 1)
        cv2.putText(imgBackground, str(studentInfo['name']), (808, 445), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 1)
        cv2.putText(imgBackground, str(studentInfo['major']), (1006, 550), cv2.FONT_HERSHEY_COMPLEX, 0.5,
                    (255, 255, 255), 1)
        cv2.putText(imgBackground, str(studentInfo['id']), (1006, 493), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255),
                    1)
        cv2.putText(imgBackground, str(studentInfo['standing']), (910, 625), cv2.FONT_HERSHEY_COMPLEX, 0.6,
                    (111, 111, 111),
                    1)
        cv2.putText(imgBackground, str(studentInfo['year']), (1025, 625), cv2.FONT_HERSHEY_COMPLEX, 0.6,
                    (111, 111, 111),
                    1)
        cv2.putText(imgBackground, str(studentInfo['starting_year']), (1125, 625), cv2.FONT_HERSHEY_COMPLEX, 0.6,
                    (111, 111, 111),
                    1)

        imgBackground[175:175 + 216, 909:909 + 216] = imgStudent

        counter += 1

    cv2.imshow("Face", imgBackground)
    cv2.waitKey(1)
