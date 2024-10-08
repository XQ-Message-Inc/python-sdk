from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
from Crypto.Util import Counter
import struct
import os
import warnings

class AESEncryption:
    """AES implemented encryption algorithm"""

    def __init__(self, key: bytes, scheme: int = 1):
        """Initialize AESEncryption class with an encryption key"""
        self.key = key
        self.scheme = scheme
    
    def add_header_salt(self, header=None, salt_size=16, iv_size=12):
        """Generates a salt and IV, and adds them to the header"""

        # Generate a random salt of the specified size
        salt = os.urandom(salt_size)
        # Generate a random IV of the specified size
        iv = os.urandom(iv_size)
        salt_code = b'Salted__'

        if header is None:
            # Create a new header with salt_code, salt, and iv
            header = bytearray(8 + salt_size + iv_size)
            header[:8] = salt_code  # Insert "Salted__" code
            header[8:8 + salt_size] = salt  # Insert salt
            header[8 + salt_size:] = iv  # Insert iv
        else:
            # Expand the existing header and append salt_code, salt, and iv
            expanded = bytearray(len(header) + 8 + salt_size + iv_size)
            expanded[:len(header)] = header  # Copy existing header
            expanded[len(header):len(header) + 8] = salt_code  # Insert "Salted__" code
            expanded[len(header) + 8:len(header) + 8 + salt_size] = salt  # Insert salt
            expanded[len(header) + 8 + salt_size:] = iv  # Insert iv
            header = expanded

        return {"header": header, "salt": salt, "iv": iv}
    
    def derive_key(self, salt: bytes, password: bytes = None, iterations: int = 1024, key_length: int = 32):
        """Derives a key using PBKDF2 with HMAC-SHA256."""
        key = PBKDF2(password, salt, dkLen=key_length, count=iterations, hmac_hash_module=SHA256)
        return key

    def encrypt(self, data: str, password: str=None, header=None):
        """Encrypts the provided data using AES-GCM"""
        # If no password is provided, use self.key
        if password is None:
            password = self.key
        
        if isinstance(password, str):
            password = password.encode()

        # Add salt and iv to the header
        context = self.add_header_salt(header)
        header = context['header']
        salt = context['salt']
        iv = context['iv']

        # Derive key using PBKDF2
        key = self.derive_key(salt, password)

        if self.scheme == 2:
            counter = Counter.new(128, initial_value=int.from_bytes(iv, byteorder='big'))
            cipher = AES.new(key, AES.MODE_CTR, counter=counter)
        else:
            # Create the AES-GCM cipher object using the derived IV
            cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
        
        # Encrypt the data
        if isinstance(data, str):
            data = data.encode()
        
        combined = bytearray()

        if self.scheme == 2:
            ciphertext = cipher.encrypt(data)
            # Return the combined result: Header + Ciphertext
            combined.extend(header)
            combined.extend(ciphertext)
        else:
            ciphertext, tag = cipher.encrypt_and_digest(data)
            # Return the combined result: Header + Ciphertext + Tag
            combined.extend(header)       # Add the header (with "Salted__", salt, and IV)
            combined.extend(ciphertext)   # Add ciphertext
            combined.extend(tag)          # Add authentication tag

        return combined

    def decrypt(self, data: bytes, password: str = None, salt_size=16, iv_size=12):
        # If no password is provided, use self.key
        if password is None:
            password = self.key
        
        if isinstance(password, str):
            password = password.encode()

        """Decrypts the provided data using AES-GCM"""
        # Find the position of 'Salted__' in the encrypted data
        salted_marker = b'Salted__'
        start_pos = data.find(salted_marker)
        if start_pos == -1:
            raise ValueError("Invalid data format")
        
        # Skip to after 'Salted__' (8 bytes)
        salt_start = start_pos + len(salted_marker)
    
        # Extract salt (16 bytes after the 'Salted__' marker)
        salt = data[salt_start:salt_start + salt_size]

        # Extract IV (12 bytes after the salt)
        iv_start = salt_start + salt_size
        iv = data[iv_start:iv_start + iv_size]

        # Extract ciphertext (everything after IV, excluding TAG_LENGTH at the end)
        ciphertext_start = iv_start + iv_size

        if self.scheme == 2:
            ciphertext = data[ciphertext_start:]
        else:
            ciphertext_end = -16  # TAG_LENGTH
            ciphertext = data[ciphertext_start:ciphertext_end]
            # Extract the authentication tag (last 16 bytes)
            tag = data[ciphertext_end:]

        # Derive the key using PBKDF2 and the extracted salt
        key = self.derive_key(salt , password)

        if self.scheme == 2:
            counter = Counter.new(128, initial_value=int.from_bytes(iv, byteorder='big'))
            cipher = AES.new(key, AES.MODE_CTR, counter=counter)
            plaintext = cipher.decrypt(ciphertext)
        else:
            # Create the AES-GCM cipher object for decryption
            cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
            # Decrypt the ciphertext and verify the tag
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)

        return plaintext.decode("utf-8")
    
    def decryptFile(self, data: bytes, password: str = None):
        # If no password is provided, use self.key
        if password is None:
            password = self.key
        
        if isinstance(password, str):
            password = password.encode()
        
        if password[0] == ord('.'):
            password = password[2:]

        header = self.get_file_header(data, 1)
        buf = data[header["length"]:]

        # Originally the filename was encrypted to be obfuscated, but that is no longer the case as per client requests.
        decrypted_filename = self.decrypt(header["filename"], password)

        decrypted_data = self.decrypt(buf, password)
        return decrypted_data.encode("utf-8")
    
    def encryptFile(self, filename, data, token, password):
        if filename:
            filename = filename.encode('utf-8')
        
        if filename:
            try:
                filename = self.encrypt(filename, password)
            except Exception as err:
                return None
        
        header = self.create_file_header(filename, token)

        data = data.read()
        encrypted = self.encrypt(data, password)

        return header + encrypted 

    
    def create_file_header(self, filename, token, version=1):
        token_size = 43
        token_bytes = token.encode('utf-8') 

        if isinstance(filename, str):
            name_bytes = filename.encode('utf-8') 
        else:
            name_bytes = filename

        name_size = len(name_bytes)
        tail = 0

        buffer = bytearray(4 + token_size + 4 + name_size + 1)

        # Write version number + token size
        struct.pack_into('I', buffer, tail, token_size + version)
        tail += 4

        # Write token bytes
        buffer[tail:tail + token_size] = token_bytes
        tail += token_size

        # Write name size as a 4-byte integer
        struct.pack_into('I', buffer, tail, name_size)
        tail += 4

        # Write the name bytes if name_size > 0
        if name_size > 0:
            buffer[tail:tail + name_size] = name_bytes
        tail += name_size

        # Write the algorithm mode (1 byte)
        if tail < len(buffer):
            buffer[tail] = 1
        else:
            raise IndexError(f"Tail index {tail} is out of range for buffer length {len(buffer)}")
        

        # Write the algorithm mode (1 byte)
        # buffer[tail] = 1

        return buffer

    def get_file_header(self, data, version, token_size=43):
        view = bytearray(data)
        tail = 0
        result = {"version": version, "length": 0}

        # Read the version (extract first 4 bytes and unpack as Uint32)
        v = struct.unpack('I', view[tail:tail + 4])[0] 
        result["version"] = v - token_size
        
        if result["version"] != version and v != token_size:
            warnings.warn(f'Cannot decrypt due to incompatible version: {result["version"]}')
            return result 

        tail += 4
        # Read the token (decode from bytes to string)
        result["token"] = view[tail:tail + token_size].decode('utf-8')
        tail += token_size

        # Read the nameSize (next 4 bytes as Uint32)
        name_size = struct.unpack('I', view[tail:tail + 4])[0]
        tail += 4

        # If there is a filename, extract it
        if name_size > 0:
            result["filename"] = view[tail:tail + name_size]
            tail += name_size
        else:
            result["filename"] = ""

        if result["version"] > 0:
            # Skip over the scheme (for compatibility)
            tail += 1

        result["length"] = tail
        return result
