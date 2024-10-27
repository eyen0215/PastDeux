import datetime
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from openai import OpenAI
import os
from typing import List, Tuple
from henry import Database

class TaskMonitor:
    def __init__(self, sender_email: str, sender_password: str, openai_api_key: str):
        """
        Initialize TaskMonitor with email and OpenAI credentials
        
        Args:
            email_address (str): Recipient email address
            sender_email (str): Sender email address
            sender_password (str): Sender email password
            openai_api_key (str): OpenAI API key
        """
        self.D = Database()
        load_dotenv()
        #self.email_address = email_address
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.tasks = []  # List of [task_name, category, due_datetime]
        self.client = OpenAI(api_key=openai_api_key)

    def add_task(self, task_name: str, category: str, due_date: str, due_time: str, user_ID: str, task_ID: str, to_email: str) -> None:
        """
        Add a new task to the monitor
        
        Args:
            task_name (str): Name of the task
            category (str): Category of the task
            due_date (str): Due date in format 'YYYY-MM-DD'
            due_time (str): Due time in format 'HH:MM'
        """
        due_datetime = datetime.datetime.strptime(f"{due_date} {due_time}", "%Y-%m-%d %H:%M")
        self.tasks.append([task_name, category, due_datetime, user_ID, task_ID, to_email])

    def get_ai_roast(self, task_name: str, category: str) -> str:
        """
        Get a roast message from OpenAI about missing the task
        
        Args:
            task_name (str): Name of the missed task
            category (str): Category of the missed task
            
        Returns:
            str: AI-generated roast message with solutions
        """

        if (category == "Homework") or (category == "exam"):
            prompt = (
                f"I missed - {task_name} ({category}). "
                "Roast me really badly based on me missing the event. "
                "Then give me possible solutions. Give a few good solutions and few joke solutions. Don't differentiate between the good and joke ones. Just put them all in one list. Also give sample format for email to send to professor to fix the situation."
            )
        else:
            prompt = (
                f"I missed - {task_name} ({category}). "
                "Roast me really badly based on me missing the event. "
                "Then give me possible solutions. Give a few good solutions and few joke solutions. Don't differentiate between the good and joke ones. Just put them all in one list."
            )
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful but sarcastic and little mean assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content

    def send_email(self, task_name: str, message: str, user_ID: str, task_ID: str, to_email: str) -> None:
        """
        Send an email about the missed task
        
        Args:
            task_name (str): Name of the missed task
            message (str): Message body (AI roast)
        """
        msg = MIMEMultipart()
        msg['From'] = self.sender_email
        msg['To'] = to_email
        msg['Subject'] = f"Missed Task: {task_name}"

        body = f"You missed the task {task_name}\n\n{message}"
        msg.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            print(f"Email sent for missed task: {task_name}")
            self.send_overdue(user_ID, task_ID)
            print("Task set to overdue")
        except Exception as e:
            print(f"Error sending email: {e}")
    

    def send_overdue(self, user_ID: str, task_ID: str) -> None:
        self.D.set_overdue(user_ID, task_ID)


    def check_tasks(self) -> None:
        """
        Check all tasks against current time and process missed tasks
        """
        current_time = datetime.datetime.now()
        missed_tasks = []

        for task in self.tasks:
            print("All tasks:",task)
            time_difference = current_time - task[2]
            if time_difference > datetime.timedelta(hours=1):
                # Get roast message from AI
                roast_message = self.get_ai_roast(task[0], task[1])
                
                # Send email
                self.send_email(task[0], roast_message, task[3], task[4], task[5])
                
                # Mark task for removal
                missed_tasks.append(task)

        # Remove processed tasks
        for task in missed_tasks:
            self.tasks.remove(task)

    def run(self) -> None:
        """
        Main loop to check tasks every minute
        """
        try:
            while True:
                self.tasks.clear()
                user_IDs = self.D.get_user_ids()
                print(user_IDs)
                for ID in user_IDs:
                    L = self.D.get_calendar(ID)
                    if L == []:
                        continue
                    print("List:",L)
                    for single_task in L:
                        print("single task:",single_task)
                        monitor.add_task(
                        task_name=single_task[0],
                        category=single_task[1],
                        due_date=single_task[2],
                        due_time=single_task[3],
                        user_ID=single_task[4],
                        task_ID=single_task[5],
                        to_email=single_task[6]
                    )
                        print("finished assigning")
                print("All tasks in list:",self.tasks)
                self.check_tasks()
                time.sleep(60)  # Wait for 1 minute
        except KeyboardInterrupt:
            print("\nTask monitoring stopped.")

# Example usage
if __name__ == "__main__":
    load_dotenv()
    # Initialize with your credentials
    monitor = TaskMonitor(
        #email_address="naomi.chirawala@gmail.com",
        sender_email="naomichirawala.spam@gmail.com",
        sender_password=os.getenv("SEND_PASSWORD"),  # Use app-specific password for Gmail
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    # Add some sample tasks
   
    '''monitor.add_task(
        task_name="math hw",
        category="assignment",
        due_date="2024-10-26",
        due_time="14:30"
    )
    
    monitor.add_task(
        task_name="do laundry",
        category="chores",
        due_date="2024-10-27",
        due_time="00:00"
    )'''

    # Start monitoring
    monitor.run()