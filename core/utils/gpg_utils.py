import gnupg
import os

# GPG binary path
GPG_BINARY_PATH = 'C:\\Program Files (x86)\\GnuPG\\bin\\gpg.exe'

# Initialize GPG
def initialize_gpg():
    if os.path.isfile(GPG_BINARY_PATH) and os.access(GPG_BINARY_PATH, os.X_OK):
        gpg = gnupg.GPG(gpgbinary=GPG_BINARY_PATH)
        return gpg
    else:
        raise FileNotFoundError(f"GPG binary not found or not executable at {GPG_BINARY_PATH}")
import gnupg

def import_public_key(gpg, public_key):
    print("Importing public key:", public_key)
    import_result = gpg.import_keys(public_key)
    print("Import result:", import_result.results)

    if not import_result.count:
        print("Error importing public key:", import_result.stderr)
        raise ValueError("Failed to import public key.")

# Assuming you have initialized `gpg` and `public_key` variables correctly:
gpg = gnupg.GPG()
public_key = "your_public_key_here"

try:
    import_public_key(gpg, public_key)
except ValueError as e:
    print("An error occurred:", e)

def encrypt_message(message, recipient_email, public_key):
    gpg = gnupg.GPG()
    
    try:
        import_public_key(gpg, public_key)
    except ValueError as e:
        print(f"Error importing public key for {recipient_email}: {e}")
        return None
    
    encrypted_data = gpg.encrypt(message, recipient_email)
    
    if not encrypted_data.ok:
        print(f"Encryption failed: {encrypted_data.stderr}")
        return None
    
    return str(encrypted_data)

def decrypt_message(encrypted_message):
    gpg = initialize_gpg()

    # Decrypt the message
    decrypted_data = gpg.decrypt(encrypted_message)
    if not decrypted_data.ok:
        raise ValueError("Decryption failed: " + decrypted_data.status)

    return str(decrypted_data)
