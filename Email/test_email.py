import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email configuration
sender_email = "corridorinfinity@gmail.com"
receiver_email = "omrpatil98@gmail.com"  # Change this to your actual recipient email
app_password = "hsif zkvo lfil lgoi"  # Use the app password you generated

# Create the email content
subject = "Test Email"
body = "This is a test email to check if sending emails works with the app password."

# Set up the email server
try:
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    # Connect to the Gmail server
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()  # Upgrade the connection to a secure encrypted SSL/TLS connection
        server.login(sender_email, app_password)  # Login with email and app password
        server.send_message(msg)  # Send the email

    print("Email sent successfully.")
except Exception as e:
    print(f"Failed to send email: {e}")
