import shutil
import os

src = r"C:\Typing Project\assets\icons\slywriter_logo.ico"
dst = r"C:\Typing Project\slywriter-electron\assets\icon.ico"

# Create directory if it doesn't exist
os.makedirs(os.path.dirname(dst), exist_ok=True)

# Copy the file
shutil.copy2(src, dst)
print(f"Icon copied successfully to {dst}")