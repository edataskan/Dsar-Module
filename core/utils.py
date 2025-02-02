import gnupg

import gnupg

def encrypt_message(message, recipient_email, public_key):
    gpg = gnupg.GPG(gpgbinary='C:\\Program Files (x86)\\GnuPG\\bin\\gpg.exe')  # GPG binary path
    import_result = gpg.import_keys(public_key)
    if not import_result.count:
        print("Error importing public key:", import_result.stderr)
        return None
    
    # Şifrelemeden önce mesajı UTF-8 olarak kodlayın
    encrypted_data = gpg.encrypt(message.encode('utf-8'), recipient_email)
    if not encrypted_data.ok:
        print("Error encrypting message:", encrypted_data.stderr)
        return None
    
    return str(encrypted_data)

def decrypt_message(encrypted_message):
    gpg = gnupg.GPG(gpgbinary='C:\\Program Files (x86)\\GnuPG\\bin\\gpg.exe')  # GPG binary path
    decrypted_data = gpg.decrypt(encrypted_message)
    if not decrypted_data.ok:
        print("Error decrypting message:", decrypted_data.stderr)
        return None
    
    return str(decrypted_data)
