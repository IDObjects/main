from datetime import datetime

def is_over_21(dob_string):
    dob = datetime.strptime(dob_string, '%Y-%m-%d')
    today = datetime.now()
    age_21_date = datetime(dob.year + 21, dob.month, dob.day)
    return today >= age_21_date

# Example usage
input_data = {
    'user': {
        'name': 'Jane Doe',
        'dob': '2000-04-30'
    }
}

input_data['user']['is_over_21'] = is_over_21(input_data['user']['dob'])

import json
print(json.dumps(input_data, indent=2))