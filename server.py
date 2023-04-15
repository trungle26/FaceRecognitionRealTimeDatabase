import os
import secrets

import numpy as np
from flask import Flask, jsonify, request
import base64
from io import BytesIO
from flask_cors import CORS
from PIL import Image

import cv2
import face_recognition
import pickle
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage
from firebase_admin import db

from PIL import Image
from io import BytesIO

app = Flask(__name__)
CORS(app)

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://faceattendancerealtime-c6597-default-rtdb.asia-southeast1.firebasedatabase.app/',
    'storageBucket': 'faceattendancerealtime-c6597.appspot.com'
})


def findEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)

    return encodeList


@app.route('/api/init_face', methods=["POST"], strict_slashes=False)
def init_face():
    image_data = request.json['image_data']
    email = request.json['email']
    # Remove the prefix using string slicing
    b64_image = image_data[22:]
    # Decode the Base64 string to bytes
    imgdata = base64.b64decode(b64_image)
    image_id = email
    filename = f'{image_id}.png'
    # Save the image to a file
    with open(os.path.join('Images', filename), 'wb') as f:
        f.write(imgdata)

    # return jsonify({'valid': True, 'message': 'Image uploaded successfully'})
    # Importting student imgs
    folderPath = 'Images'
    pathList = os.listdir(folderPath)  # ['321654.png', '852741.png', '963852.png']
    print(pathList)
    imgList = []
    studentIds = []
    for path in pathList:
        imgList.append(cv2.imread(os.path.join(folderPath, path)))
        print(path)
        print(os.path.splitext(path)[0])  # tach duoi file ra
        studentIds.append(os.path.splitext(path)[0])
        fileName = folderPath + '/' + path
        bucket = storage.bucket()
        blob = bucket.blob(fileName)
        blob.upload_from_filename(fileName)
        os.remove(fileName)


    return jsonify({'valid': True, 'message': 'gui thanh cong'})


@app.route('/api/is_image_valid', methods=['POST'], strict_slashes=False)
def is_image_valid():
    # down load tu firebase
    bucket = storage.bucket()
    email = request.json['email']
    file_path = "Images/" + email + ".png"
    # Check if the file exists in Firebase Storage
    blob = bucket.blob(file_path)
    if not blob.exists():
        print('File does not exist in Firebase Storage')
    else:
        # Download the file to your local machine
        os.makedirs(os.path.dirname(file_path), exist_ok=True)  # create local directories if they don't exist
        blob.download_to_filename(file_path)
        print('File downloaded successfully')
    #--------------------

    # nhan anh tu user
    image_data = request.json['image_data']
    # Remove the prefix using string slicing
    b64_image = image_data[22:]
    # Decode the Base64 string to bytes
    imgdata = base64.b64decode(b64_image)
    with open('anh.png', 'wb') as f:
        f.write(imgdata)

    #encode anh tu firebase
    print("encoding started...")
    firebase_image = cv2.imread(file_path)
    encodeImageKnown = findEncodings([firebase_image])
    encodeImageKnownWithIds = [encodeImageKnown, [email]]
    print("encoding complete")
    # luu file vua encode
    file = open("EncodeFile.p", 'wb')
    pickle.dump(encodeImageKnownWithIds, file)
    file.close()
    print("file saved")

    # load the encoding file of firebase image
    print('loading encode file...')
    file = open("EncodeFile.p", 'rb')
    encodeListKnownWithIds = pickle.load(file)
    file.close()
    encodeListKnown, studentIds = encodeListKnownWithIds
    print('encode file loaded')

    # Open the image from user using Pillow
    image = cv2.imread("anh.png")
    #convert sang rgb
    imgConverted = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    faceCurFrame = face_recognition.face_locations(imgConverted)
    encodeCurFrame = face_recognition.face_encodings(imgConverted, faceCurFrame)  # encode phan mat tren anh user
    # delete file not used anymore
    if os.path.exists('anh.png'):
        os.remove('anh.png')

    if faceCurFrame:
        for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
            print("matches", matches)
            print("faceDis", faceDis)

            matchIndex = np.argmin(faceDis)
            print("Match Index", matchIndex)

            if matches[matchIndex] and matches[matchIndex] < 2.1:
                print("Known Face Detected")
                print(studentIds[matchIndex])
                return jsonify({'valid': True, 'message': 'Trung mat'})
        else:
            print("The two images do not match.")
    else:
        print("No face detected in one or both images.")
    return jsonify({'valid': False, 'message': 'Khong trung mat'})


if __name__ == '__main__':
    app.run()
