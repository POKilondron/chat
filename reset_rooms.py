
from app import app, db
from models import ChatRoom

def reset_rooms():
    with app.app_context():
        try:
            # Delete all chat rooms
            rooms = ChatRoom.query.all()
            room_count = len(rooms)
            
            for room in rooms:
                db.session.delete(room)
            
            db.session.commit()
            print(f"Successfully deleted {room_count} chat rooms.")
        except Exception as e:
            print(f"Error deleting rooms: {e}")
            db.session.rollback()

if __name__ == "__main__":
    reset_rooms()
