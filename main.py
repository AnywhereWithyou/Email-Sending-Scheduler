from flask import Flask, render_template, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from datetime import datetime, timedelta
app = Flask(__name__)

SENDGRID_API_KEY = 'YOUR_SENDGRID_API_KEY '

scheduler = BackgroundScheduler()
scheduler.start()

scheduled_emails = {}  # Dictionary to store scheduled emails

def send_scheduled_email(email, subject, message):
    try:
        sg = sendgrid.SendGridAPIClient(api_key=SENDGRID_API_KEY)
        from_email = Email("Your email address")
        to_email = To(email)
        content = Content("text/plain", message)
        mail = Mail(from_email, to_email, subject, content)
        response = sg.client.mail.send.post(request_body=mail.get())
        print("Scheduled email sent successfully!")
    except Exception as e:
        print("An error occurred:", str(e))

@app.route('/')
def index():
    return render_template('index.html', scheduled_emails=scheduled_emails)

@app.route('/schedule_email', methods=['GET'])
def schedule_email():
    try:
        recipient_email_list = request.args.get('recipient_email').split(',')  # Split the comma-separated list into a Python list
        subject = request.args.get('subject')
        message = request.args.get('message')
        scheduled_datetime_str = request.args.get('scheduled_datetime')

        timezone_str = request.args.get('offset')  # Get the timezone from the query parameters

        # Use pytz to get the specified time zone
        i = 1
        for recipient_email in recipient_email_list:
            job_id = str(request.args.get('id'))
            job_id = job_id + " " + str(i)
            # job_id = str(hash(scheduled_datetime_str + recipient_email + subject + message))  # Generate a unique job ID based on the parameters

            datetime_obj = datetime.fromisoformat(scheduled_datetime_str)
            formatted_datetime_str = datetime_obj.strftime("%Y-%m-%d %H:%M")
            scheduled_datetime = datetime.strptime(formatted_datetime_str, "%Y-%m-%d %H:%M")

            local_time = datetime.now()
            # Get the current UTC time
            utc_time = datetime.utcnow()
            # Calculate the timezone offset
            timezone_offset = local_time - utc_time
            # Extract the hours and minutes from the offset
            seconds = timezone_offset.total_seconds()
            hours, seconds = divmod(seconds, 3600)
            delta = hours + float(timezone_str)
            scheduled_datetime = scheduled_datetime + timedelta(hours=delta)
            # Schedule the email sending task with the unique job ID for each recipient
            job = scheduler.add_job(send_scheduled_email, 'date', run_date=scheduled_datetime, args=[recipient_email, subject, message], id=job_id)

            # Store the job in the dictionary with the unique job ID
            scheduled_emails[job_id] = {
                'email': recipient_email,
                'subject': subject,
                'message': message,
                'scheduled_datetime': scheduled_datetime,
            }
            i = i+1

        return jsonify({"message": f"Email scheduled for {scheduled_datetime} with Job IDs: {job_id}", "job_ids": job_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

canceled_emails = {}
@app.route('/cancel_email', methods=['GET'])
def cancel_schedule_by_id():
    try:
        # Get the job ID to cancel from the URL parameter
        job_id = str(request.args.get('ID'))
        
        if job_id:
            # Check if the job exists in the scheduled_emails dictionary
            if job_id in scheduled_emails:
                # Remove the job from the scheduler
                scheduler.remove_job(job_id)
                # Move the job from scheduled_emails to canceled_emails
                canceled_emails[job_id] = scheduled_emails.pop(job_id)
                return jsonify({"message": f"Scheduled email with Job ID {job_id} canceled"}), 200
            else:
                return jsonify({"error": f"Job with Job ID {job_id} not found"}), 404
        else:
            return jsonify({"error": "No Job ID provided in the URL parameter"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Other Flask routes and functions

if __name__ == '__main__':
    app.run(host='Hosting server IP', port=80)
