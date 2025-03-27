from pymongo import MongoClient
from flask_pymongo import PyMongo

# For storing user sessions/history (optional)
app.config["MONGO_URI"] = "mongodb://localhost:27017/normalizationDB"
mongo = PyMongo(app)

def save_normalization_result(user_id, input_data, result):
    """Store normalization history in MongoDB"""
    return mongo.db.history.insert_one({
        'user_id': user_id,
        'input': input_data,
        'result': result,
        'timestamp': datetime.datetime.utcnow()
    }) 