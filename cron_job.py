import sqlite3
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def check_and_send_reminders():
    # قراءة بيانات الإرسال من Secrets المحفوظة في GitHub
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")

    if not sender_email or not sender_password:
        print("⚠️ لم يتم العثور على بيانات الإرسال في Secrets!")
        return

    conn = sqlite3.connect('contracts_db.db')
    cursor = conn.cursor()
    
    # جلب العقود النشطة
    cursor.execute("SELECT ContractID, Title, DueDate, EmployeeEmail, Priority FROM Contracts WHERE Status = 1")
    contracts = cursor.fetchall()

    today = datetime.now().date()

    for contract in contracts:
        contract_id, title, due_date_str, email, priority = contract
        try:
            due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
            days_left = (due_date - today).days

            # إرسال تنبيه إذا كان المتبقي 7 أيام أو أقل
            if 0 <= days_left <= 7:
                subject = f"⏰ تنبيه تلقائي: قرب انتهاء عقد {title}"
                body = f"""السلام عليكم ورحمة الله وبركاته،

نود تذكيركم بأن العقد/المهمة: ({title})
ينتهي خلال: {days_left} أيام (بتاريخ: {due_date_str}).
مستوى الأهمية: {priority}.

يرجى اتخاذ الإجراءات اللازمة.

رسالة آليّة صَادرة عن نظام التذكير الذكي."""

                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = email
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain', 'utf-8'))

                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
                server.quit()

                print(f"✅ تم إرسال تنبيه تلقائي بنجاح للعقد: {title} إلى {email}")
        except Exception as e:
            print(f"❌ خطأ أثناء معالجة العقد {title}: {str(e)}")

    conn.close()

if __name__ == "__main__":
    check_and_send_reminders()
