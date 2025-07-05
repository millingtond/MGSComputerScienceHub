import os
import uuid
import firebase_admin
from firebase_admin import credentials, firestore, storage

# --- CONFIGURATION ---
# IMPORTANT: Place your Firebase service account key JSON file in the same
# directory as this script and rename it to 'serviceAccountKey.json'.
# You have previously uploaded this file as 'mgscompsci-dda86-firebase-adminsdk-fbsvc-a8342d8af0.json'.
SERVICE_ACCOUNT_KEY_PATH = 'mgscompsci-dda86-firebase-adminsdk-fbsvc-a8342d8af0.json'

# --- INITIALIZE FIREBASE ADMIN SDK ---
try:
    cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
    # FIX: Corrected the storageBucket URL to match your project's configuration.
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'mgscompsci-dda86.firebasestorage.app'
    })
    db = firestore.client()
    bucket = storage.bucket()
    print("✅ Firebase Admin SDK initialized successfully.")
except Exception as e:
    print(f"❌ ERROR: Firebase Admin SDK initialization failed.")
    print(f"   Please ensure '{SERVICE_ACCOUNT_KEY_PATH}' is in the same directory as this script.")
    print(f"   Error details: {e}")
    exit()

def upload_worksheet_package(local_directory_path, main_html_filename, title, topic):
    """
    Uploads a directory of files as a worksheet package to Firebase Storage
    and creates a corresponding document in the 'worksheets' collection in Firestore.

    Args:
        local_directory_path (str): The local path to the folder containing the worksheet files.
        main_html_filename (str): The filename of the main HTML file within the directory.
        title (str): The title of the worksheet.
        topic (str): The curriculum topic for the worksheet.
    """
    if not os.path.isdir(local_directory_path):
        print(f"❌ ERROR: Directory not found at '{local_directory_path}'")
        return

    print(f"\nProcessing package from '{local_directory_path}'...")

    # Create a single unique identifier for this worksheet package folder in Storage
    package_uuid = str(uuid.uuid4())
    remote_folder_path = f'worksheets/{package_uuid}/'
    main_html_public_url = None

    try:
        # 1. Iterate through all files in the local directory and upload them
        files_to_upload = os.listdir(local_directory_path)
        if not files_to_upload:
            print("   ⚠️  Warning: The specified directory is empty.")
            return

        print(f"   Found {len(files_to_upload)} file(s) to upload.")

        for filename in files_to_upload:
            local_file_path = os.path.join(local_directory_path, filename)
            if os.path.isfile(local_file_path):
                destination_blob_name = f'{remote_folder_path}{filename}'
                
                blob = bucket.blob(destination_blob_name)
                
                print(f"   -> Uploading '{filename}' to Storage...")
                # Determine content type, default to octet-stream if unknown
                content_type = 'text/html' if filename.endswith('.html') else 'text/javascript' if filename.endswith('.js') else 'text/css' if filename.endswith('.css') else None
                blob.upload_from_filename(local_file_path, content_type=content_type)

                # 2. Make the file publicly accessible
                blob.make_public()

                # 3. If this is the main HTML file, store its public URL
                if filename == main_html_filename:
                    main_html_public_url = blob.public_url
        
        if not main_html_public_url:
            print(f"❌ ERROR: The main HTML file '{main_html_filename}' was not found in the directory.")
            return

        print(f"   All files uploaded. Main worksheet URL: {main_html_public_url}")

        # 4. Create a document in the 'worksheets' collection in Firestore
        worksheet_data = {
            'title': title,
            'topic': topic,
            'worksheetURL': main_html_public_url
        }
        
        doc_ref = db.collection('worksheets').add(worksheet_data)
        print(f"   ✅ Successfully created Firestore document with ID: {doc_ref[1].id}")

    except Exception as e:
        print(f"❌ An error occurred during the upload process: {e}")


if __name__ == '__main__':
    # --- HOW TO USE ---
    # 1. Create a folder on your computer (e.g., 'cpu-performance-worksheet').
    # 2. Place all the related files for that worksheet (HTML, JS, CSS, etc.) inside that folder.
    # 3. Update the variables below with your folder's name, the main HTML file's name, and the worksheet details.
    
    # Example for your new worksheet:
    worksheet_folder = 'cpu-performance-worksheet' # The name of your local folder
    main_file = 'U1.1-L2-gcse-sysarch-performance.html'
    worksheet_title = "CPU Performance Factors"
    worksheet_topic = "1.2 CPU Performance"

    # To run the upload, create the folder, put your files in it,
    # and then uncomment the line below.
    upload_worksheet_package(worksheet_folder, main_file, worksheet_title, worksheet_topic)

    print("\nScript finished. To upload a new worksheet package, edit the 'if __name__ == '__main__':' block and run the script.")
