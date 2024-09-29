from flask import Flask, jsonify, render_template, request
import psutil
import platform
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

# Define the minimum system requirements
REQUIRED_RAM_GB = 8  # 8 GB
REQUIRED_DISK_GB = 50  # 50 GB free space
REQUIRED_CORES = 4  # 4 CPU cores

# Email settings
SENDER_EMAIL = os.getenv('EMAIL_USER')
SENDER_PASSWORD = os.getenv('EMAIL_PASSWORD')  # Use the app-specific password here
ADMIN_EMAIL = "selfpaceadmin@codingtemple.com"  # Email where you'd like to receive failure notifications

def send_failure_email(user_email):
    subject = "Tech Check Failed"
    body = f"The following user failed the tech check: {user_email}"
    
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = ADMIN_EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Connect to the Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Secure the connection
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, ADMIN_EMAIL, text)
        server.quit()
        print(f"Failure email sent for {user_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

def check_system_specs():
    # Get system information
    os_name = platform.system()
    os_version = platform.release()
    cpu_count = psutil.cpu_count(logical=False)
    total_ram_gb = psutil.virtual_memory().total / (1024 ** 3)  # Convert from bytes to GB
    free_disk_gb = psutil.disk_usage('/').free / (1024 ** 3)  # Convert from bytes to GB

    # Check if the system meets the requirements
    cpu_ok = cpu_count >= REQUIRED_CORES
    ram_ok = total_ram_gb >= REQUIRED_RAM_GB
    disk_ok = free_disk_gb >= REQUIRED_DISK_GB

    # Return a dictionary of the results
    return {
        "os_name": os_name,
        "os_version": os_version,
        "cpu_ok": cpu_ok,
        "ram_ok": ram_ok,
        "disk_ok": disk_ok,
        "cpu_count": cpu_count,
        "total_ram_gb": total_ram_gb,
        "free_disk_gb": free_disk_gb
    }
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check_system')
def check_system():
    user_email = request.args.get('email')

    if not user_email:
        return jsonify({"error": "No email provided"}), 400
    
    # Run the tech check (you should have a function like check_system_specs)
    specs = check_system_specs()  # Example of what this function should return

    if specs["cpu_ok"] and specs["ram_ok"] and specs["disk_ok"]:
        message = "You're good to go!"
        status = "success"
    else:
        message = "You need new tech!"
        status = "fail"
        # Send failure email
        send_failure_email(user_email)

    return jsonify({
        "status": status,
        "message": message,
        "specs": {  # Ensure you are returning specs here
            "os_name": specs.get("os_name", "Unknown"),
            "os_version": specs.get("os_version", "Unknown"),
            "cpu_count": specs.get("cpu_count", 0),
            "total_ram_gb": specs.get("total_ram_gb", 0),
            "free_disk_gb": specs.get("free_disk_gb", 0)
        }
    })

if __name__ == '__main__':
    app.run(debug=True)