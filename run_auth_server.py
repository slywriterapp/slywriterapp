#!/usr/bin/env python
"""Run the auth server with SMTP configuration"""
import os
import subprocess

# Set SMTP environment variables
os.environ['SMTP_SERVER'] = 'smtp.gmail.com'
os.environ['SMTP_PORT'] = '587'
os.environ['SMTP_USERNAME'] = 'support@slywriter.ai'
os.environ['SMTP_PASSWORD'] = 'icvvvhygzkccpuzg'

# Set Google OAuth Client ID
os.environ['GOOGLE_CLIENT_ID'] = '675434683795-shrls6suu68dj0cuvqct28gf3o6u3jav.apps.googleusercontent.com'

print("Starting Authentication Server with SMTP...")
print(f"  Server: {os.environ.get('SMTP_SERVER')}")
print(f"  Port: {os.environ.get('SMTP_PORT')}")
print(f"  Username: {os.environ.get('SMTP_USERNAME')}")
print(f"  Password: [CONFIGURED]")
print()

# Import and run the server
import slywriter_server
slywriter_server.app.run(host='0.0.0.0', port=5000)