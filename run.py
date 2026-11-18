import sys
import os

# Ensure current folder is in Python sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, bootstrap_application

if __name__ == "__main__":
    print("=" * 65)
    print(" CinemaPredict - Digital Cinema Delivery Intelligence (PBL) ")
    print("=" * 65)
    bootstrap_application()
    print("[CinemaPredict] Server starting on http://127.0.0.1:5000 ...")
    app.run(host="127.0.0.1", port=5000, debug=False)
