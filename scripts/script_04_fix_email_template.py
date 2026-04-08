import re

# Read the file
with open('/Users/kevinmassengill/Automations/scripts/script_04_not_qualified_polite_decline_oauth.py', 'r') as f:
    content = f.read()

# Old signature block
old_signature = """    <p style="margin: 0;">Kevin Massengill</p>
    <p style="margin: 0;">Chairman & CEO</p>
    <p style="margin: 0;">Meraglim Holdings Corporation</p>
    <p style="margin: 0;">kmassengill@meraglim.com</p>"""

# New signature block with proper line breaks
new_signature = """    <p style="margin: 0;">Best regards,  
  

Kevin Massengill  

Meraglim Holdings Corporation  

KMassengill@Meraglim.com</p>"""

# Replace
content = content.replace(old_signature, new_signature)

# Write back
with open('/Users/kevinmassengill/Automations/scripts/script_04_not_qualified_polite_decline_oauth.py', 'w') as f:
    f.write(content)

print("Email template fixed!")
