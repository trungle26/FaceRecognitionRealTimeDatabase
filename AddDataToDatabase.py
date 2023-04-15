import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://faceattendancerealtime-c6597-default-rtdb.asia-southeast1.firebasedatabase.app/'
})

ref = db.reference('Students')
data = {
    '321654':
        {
            'id':321654,
            'name': 'Le Duc Trung',
            'major': 'IT',
            'starting_year': 2021,
            'total_attendance': 3,
            'standing': 'G',
            'year': 4,
            'last_attendance_time': '2023-03-29 00:15:30'
        },
    '852741':
        {
            'id': 852741,
            'name': 'Tran Quang Phuc',
            'major': 'IT',
            'starting_year': 2021,
            'total_attendance': 2,
            'standing': 'G',
            'year': 3,
            'last_attendance_time': '2023-03-28 00:15:30'
        },
    '963852':
        {
            'id': 963852,
            'name': 'Elong Ma',
            'major': 'IT',
            'starting_year': 2021,
            'total_attendance': 3,
            'standing': 'TOP-G',
            'year': 44,
            'last_attendance_time': '2023-03-29 00:15:30'
        },
    '999999':
        {
            'id': 999999,
            'name': 'Phuc Tran',
            'major': 'IT',
            'starting_year': 2021,
            'total_attendance': 3,
            'standing': 'TOP-G',
            'year': 44,
            'last_attendance_time': '2023-03-29 00:15:30'
        }

}

for key, value in data.items():
    ref.child(key).set(value)
