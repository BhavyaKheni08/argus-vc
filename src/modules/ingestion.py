import os
import time
from google import genai

class GoogleIngestion:
    def __init__(self):
        """Initialize and configure the Google GenAI client."""
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not found.")
        self.client = genai.Client(api_key=api_key)

    def upload_to_gemini(self, file_path, mime_type=None):
        """
        Uploads a file to the Google GenAI File API and waits for it to be active.
        
        Args:
            file_path (str): The path to the file to upload.
            mime_type (str): Optional mime type (deprecated/inferred in new SDK usually, but kept for sig compatibility).

        Returns:
            The uploaded and active file object.
        """
        print(f"Uploading file: {file_path}...")
        # The new SDK's upload method. file argument is used (not path).
        file_object = self.client.files.upload(file=file_path)
        print(f"Upload complete: {file_object.name}")
        
        # Wait for the file to be active
        return self.wait_for_active(file_object)

    def wait_for_active(self, file_object):
        """
        Waits for the uploaded file to become active.
        
        Args:
            file_object: The file object returned by upload.
            
        Returns:
            The updated file object once it is active.
            
        Raises:
            Exception: If the file processing fails.
        """
        print("Waiting for file processing...", end="")
        
        while True:
            # Refresh file object
            file_object = self.client.files.get(name=file_object.name)
            
            # Check state. safely accessing state.name or similar if it's an enum
            # The prompt requests: file.state.name == "ACTIVE"
            # In the new SDK, state is often an enum, let's convert to string to be safe or access .name
            current_state = file_object.state.name if hasattr(file_object.state, 'name') else str(file_object.state)
            
            if current_state == "PROCESSING":
                print(".", end="", flush=True)
                time.sleep(2)
            elif current_state == "ACTIVE":
                print() # Newline
                print("File is active and ready for use.")
                return file_object
            elif current_state == "FAILED":
                print()
                raise Exception(f"File processing failed with state: {current_state}")
            else:
                # Handle unknown states or just check loop again? 
                # Assuming standard lifecycle: PROCESSING -> ACTIVE or FAILED
                # Example: STATE_UNSPECIFIED could happen?
                print(f"[{current_state}]", end="", flush=True)
                time.sleep(2)

