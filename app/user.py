from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, email, password):
        self.id = id
        self.email = email
        self.password = password

# Single hard-coded user
HARDCODED_USER = User(
    id=1,
    email="admin@example.com",
    password="supersecret"  # Optional: hash for production
)
