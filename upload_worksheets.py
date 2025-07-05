import os
import firebase_admin
from firebase_admin import credentials, firestore

# --- SCRIPT CONFIGURATION ---

# 1. SERVICE ACCOUNT KEY:
#    Replace 'path/to/your/serviceAccountKey.json' with the actual path to the JSON file you downloaded from Firebase.
SERVICE_ACCOUNT_KEY_PATH = 'mgscompsci-dda86-firebase-adminsdk-fbsvc-a8342d8af0.json'

# 2. WORKSHEETS DIRECTORY:
#    This should be the full path to the folder containing your GCSE worksheet HTML files.
#    Based on your file structure, this would be a good starting point.
#    FIX: Added 'r' before the string to make it a raw string, preventing unicode escape errors on Windows.
WORKSHEETS_DIR = r'C:\Users\Dan Mill\OneDrive - Manchester Grammar School\MGSCompSciHub\GCSE\Worksheets'

# 3. WORKSHEET URL PREFIX (OPTIONAL):
#    If you upload your worksheets to a specific folder in Firebase Storage, you can set the base URL here.
#    For now, we will leave it as a placeholder.
#    Example: 'https://firebasestorage.googleapis.com/v0/b/your-project-id.appspot.com/o/worksheets%2F'
WORKSHEET_URL_PREFIX = 'https://mgscompsci.org/worksheets/'

# --- DATA MAPPING ---
# This dictionary maps the codes from your filenames to the full topic names from the OCR J277 spec.
TOPIC_MAP = {
    'sysarch': '1.1 Systems Architecture',
    'memstore': '1.2 Memory and Storage',
    'net': '1.3 Computer Networks, Connections and Protocols',
    'sec': '1.4 Network Security',
    'syssoft': '1.5 Systems Software',
    'ethics': '1.6 Ethical, Legal, Cultural and Environmental Concerns',
    'algo': '2.1 Algorithms',
    'prog': '2.2 Programming Fundamentals',
    'robprog': '2.3 Producing Robust Programs',
    'boolog': '2.4 Boolean Logic',
    'proglang': '2.5 Programming Languages and IDEs'
}

def initialize_firebase():
    """Initializes the Firebase Admin SDK."""
    try:
        cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
        firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK initialized successfully.")
        return firestore.client()
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        print("Please ensure 'SERVICE_ACCOUNT_KEY_PATH' is correct and the file exists.")
        return None

def parse_filename(filename):
    """
    Parses a filename like 'gcse-sysarch-performance.html' into a topic and title.
    Returns a dictionary with 'topic', 'title', and 'worksheetURL' or None if parsing fails.
    """
    if not filename.startswith('gcse-') or not filename.endswith('.html'):
        return None

    # Remove 'gcse-' prefix and '.html' suffix
    parts = filename[5:-5].split('-')
    
    if len(parts) < 2:
        return None

    topic_code = parts[0]
    title_words = parts[1:]

    topic = TOPIC_MAP.get(topic_code, "Unknown Topic")
    # Capitalize each word and join with a space for a clean title
    title = ' '.join(word.capitalize() for word in title_words)
    
    # Construct a placeholder URL
    url = f"{WORKSHEET_URL_PREFIX}{filename}"

    return {
        'topic': topic,
        'title': title,
        'worksheetURL': url
    }

def upload_worksheets_to_firestore(db):
    """
    Scans the directory, parses filenames, and uploads worksheet data to Firestore.
    """
    if not os.path.isdir(WORKSHEETS_DIR):
        print(f"Error: Directory not found at '{WORKSHEETS_DIR}'")
        print("Please check the 'WORKSHEETS_DIR' path.")
        return

    worksheets_collection = db.collection('worksheets')
    
    print(f"\nScanning directory: {WORKSHEETS_DIR}")
    
    # Get existing worksheets to avoid duplicates
    existing_docs_raw = worksheets_collection.stream()
    existing_titles = {doc.to_dict().get('title') for doc in existing_docs_raw}
    print(f"Found {len(existing_titles)} existing worksheets in Firestore.")

    files_to_upload = 0
    for filename in os.listdir(WORKSHEETS_DIR):
        worksheet_data = parse_filename(filename)
        
        if worksheet_data:
            if worksheet_data['title'] in existing_titles:
                print(f"  - Skipping '{filename}' (title '{worksheet_data['title']}' already exists).")
                continue

            try:
                # Add a new document with a generated ID
                worksheets_collection.add(worksheet_data)
                print(f"  + Uploaded '{filename}' as '{worksheet_data['title']}'.")
                files_to_upload += 1
            except Exception as e:
                print(f"  ! Error uploading '{filename}': {e}")
    
    print(f"\nUpload complete. Added {files_to_upload} new worksheet(s) to Firestore.")


if __name__ == "__main__":
    print("--- Firestore Worksheet Uploader ---")
    db_client = initialize_firebase()
    if db_client:
        upload_worksheets_to_firestore(db_client)
    print("\n--- Script Finished ---")
