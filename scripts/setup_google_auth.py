#!/usr/bin/env python3
"""
Google OAuth Setup Script
=========================

This script sets up Google API authentication for Gmail, Google Sheets, and Google Calendar.
Run this script ONCE to authorize your Google account. It will create the necessary credential files.

STEP-BY-STEP INSTRUCTIONS:
==========================

1. Create a Google Cloud Project:
   - Go to https://console.cloud.google.com/
   - Click "Select a Project" at the top
   - Click "NEW PROJECT"
   - Name it "Meraglim Automations"
   - Click "CREATE"
   - Wait for the project to be created (may take a minute)

2. Enable Required APIs:
   - In the Google Cloud Console, go to "APIs & Services" > "Library"
   - Search for and enable these APIs:
     a) Gmail API
     b) Google Sheets API
     c) Google Calendar API
   - For each one, click it, then click "ENABLE"

3. Create OAuth 2.0 Credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - If prompted, click "Configure Consent Screen"
   - Select "External" user type
   - Fill in the form:
     * App name: "Meraglim Automations"
     * User support email: KMassengill@Meraglim.com
     * Developer contact: KMassengill@Meraglim.com
   - Click "Save and Continue"
   - On "Scopes" page, click "Add or Remove Scopes"
   - Add these scopes:
     * https://www.googleapis.com/auth/gmail.modify
     * https://www.googleapis.com/auth/spreadsheets
     * https://www.googleapis.com/auth/calendar
   - Click "Update" and then "Save and Continue"
   - Skip the "Optional info" section
   - Click "Save and Continue"
   - Go back to "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop application"
   - Name it "Meraglim Automations"
   - Click "Create"
   - Click the download button (looks like a down arrow) to download the JSON file
   - Save it as: /Users/kevinmassengill/Automations/config/google_credentials.json

4. Run this script:
   - Open Terminal
   - Run: python3 /Users/kevinmassengill/Automations/setup_google_auth.py
   - A browser window will open asking you to sign in with your Google account
   - Sign in with KMassengill@Meraglim.com
   - Click "Allow" when asked to grant permissions
   - The script will create the token file automatically

5. Done!
   - The script will create /Users/kevinmassengill/Automations/config/google_token.json
   - Your automations can now access Gmail, Google Sheets, and Google Calendar
   - You only need to run this setup script ONCE

TROUBLESHOOTING:
================

Q: I get "FileNotFoundError: google_credentials.json"
A: Make sure you downloaded the credentials.json file from Google Cloud Console and saved it to:
   /Users/kevinmassengill/Automations/config/google_credentials.json

Q: I get "invalid_client" error
A: The credentials.json file may be corrupted. Download it again from Google Cloud Console.

Q: I get "redirect_uri_mismatch" error
A: This is usually because the redirect URI in the credentials doesn't match. Try deleting the
   credentials.json file and creating a new OAuth client ID (choose "Desktop application").

Q: The browser doesn't open automatically
A: Copy the URL that appears in the terminal and paste it into your browser manually.
"""

import os
import sys
import json
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials as OAuth2Credentials

# Configuration
CREDENTIALS_FILE = "/Users/kevinmassengill/Automations/config/google_credentials.json"
TOKEN_FILE = "/Users/kevinmassengill/Automations/config/google_token.json"

# Scopes required for our automations
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/calendar'
]


def setup_google_auth():
    """Set up Google OAuth authentication."""
    
    print("\n" + "="*70)
    print("Google OAuth Setup for Meraglim Automations")
    print("="*70 + "\n")
    
    # Check if credentials file exists
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"ERROR: Credentials file not found at: {CREDENTIALS_FILE}")
        print("\nPlease follow these steps:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a new project called 'Meraglim Automations'")
        print("3. Enable Gmail API, Google Sheets API, and Google Calendar API")
        print("4. Go to APIs & Services > Credentials")
        print("5. Create OAuth 2.0 credentials (Desktop application)")
        print("6. Download the JSON file and save it to:")
        print(f"   {CREDENTIALS_FILE}")
        print("\nThen run this script again.")
        sys.exit(1)
    
    print(f"✓ Found credentials file: {CREDENTIALS_FILE}")
    
    # Create the flow
    print("\nStarting OAuth flow...")
    print("A browser window will open. Sign in with your Google account and grant permissions.")
    print("(If the browser doesn't open, copy the URL from below and paste it manually)\n")
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE,
            SCOPES
        )
        
        # Run the local server to receive the authorization code
        creds = flow.run_local_server(port=8080, open_browser=True)
        
        # Save the credentials for future use
        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
        
        print("\n" + "="*70)
        print("✓ SUCCESS! Google authentication is set up.")
        print("="*70)
        print(f"\nToken saved to: {TOKEN_FILE}")
        print("\nYour automations can now access:")
        print("  • Gmail (read, send, and manage emails)")
        print("  • Google Sheets (read and write)")
        print("  • Google Calendar (read and manage events)")
        print("\nYou only need to run this setup script ONCE.")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Make sure the credentials.json file is valid")
        print("2. Try deleting the credentials.json file and creating a new one")
        print("3. Make sure you're using the correct Google account (KMassengill@Meraglim.com)")
        sys.exit(1)


if __name__ == "__main__":
    setup_google_auth()
