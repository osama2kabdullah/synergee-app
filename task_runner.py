from app import create_app
from app.routes.api import loop_over_all_stores

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        loop_over_all_stores()
