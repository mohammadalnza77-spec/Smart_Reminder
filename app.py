import streamlit as st
import sqlite3
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date
import io

# ---------------------------------------------------------
# 1. إعداد وتوصيل قاعدة البيانات SQLite
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect('contracts_db.db')
    cursor = conn.cursor()
    # جدول العقود
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Contracts (
            ContractID INTEGER PRIMARY KEY AUTOINCREMENT,
            Title TEXT NOT NULL,
            Category TEXT NOT NULL,
            DueDate TEXT NOT NULL,
            Priority TEXT NOT NULL,
            EmployeeEmail TEXT NOT NULL,
            Status INTEGER NOT NULL,
            Description TEXT
        )
    ''')
    # جدول سجل الإيميلات (Foreign Key Relationship)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS EmailLogs (
            LogID INTEGER PRIMARY KEY AUTOINCREMENT,
            ContractID INTEGER NOT NULL,
            SentDate TEXT NOT NULL,
            EmailContent TEXT NOT NULL,
            FOREIGN KEY (ContractID) REFERENCES Contracts(ContractID) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# 2. دالة إرسال الإيميل التلقائي عبر Gmail SMTP مع Secrets
# ---------------------------------------------------------
def send_email_smtp(receiver_email, subject, body):
    try:
        # قراءة البريد وكلمة السر المحفوظة تلقائياً في Secrets
        sender_email = st.secrets["SENDER_EMAIL"]
        sender_password = st.secrets["SENDER_PASSWORD"]

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True, "تم إرسال البريد الإلكتروني بنجاح!"
    except Exception as e:
        return False, f"فشل الإرسال: {str(e)}"

# ---------------------------------------------------------
# 3. إعداد الواجهة والقائمة الجانبية (Navigation)
# ---------------------------------------------------------
st.set_page_config(page_title="نظام التذكير الذكي بالعقود", layout="wide", page_icon="📌")
st.title("📌 نظام الجدولة والتذكير الذكي بالعقود والمهام")

menu = [
    "إضافة عقد جديد (Create)",
    "إدارة وتعديل العقود (Read/Update/Delete)",
    "إرسال تنبيه بالذكاء الاصطناعي (SMTP & AI)",
    "تصدير التقارير (Export)"
]
choice = st.sidebar.selectbox("القائمة الرئيسية (Navigation)", menu)

# ---------------------------------------------------------
# 4. صفحة إضافة عقد جديد (Create + Controls + Validation)
# ---------------------------------------------------------
if choice == "إضافة عقد جديد (Create)":
    st.subheader("➕ إضافة عقد / مهمة جديدة")
    
    with st.form("add_form"):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("اسم العقد / المهمة * (Text Box)")
            category = st.selectbox("القسم / التصنيف (Drop down list)", ["تقنية المعلومات", "الصيانة والتشغيل", "الموارد البشرية", "المالية والعقود"])
            due_date = st.date_input("تاريخ الانتهاء", min_value=date.today())
        
        with col2:
            email = st.text_input("بريد الموظف المسؤول * (Text Box)")
            priority = st.radio("مستوى الأهمية (Radio Button)", ["عالية", "متوسطة", "منخفضة"])
            status = st.checkbox("العقد نشط حالياً (Checkbox)", value=True)
            
        description = st.text_area("تفاصيل وإرشادات إضافية")
        submit_btn = st.form_submit_button("حفظ العقد (Button)")
        
        if submit_btn:
            if not title.strip() or not email.strip():
                st.error("⚠️ خطأ: يرجى إدخال اسم العقد والبريد الإلكتروني.")
            elif "@" not in email or "." not in email:
                st.error("⚠️ خطأ: صياغة البريد الإلكتروني غير صحيحة.")
            else:
                conn = sqlite3.connect('contracts_db.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO Contracts (Title, Category, DueDate, Priority, EmployeeEmail, Status, Description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (title, category, str(due_date), priority, email, 1 if status else 0, description))
                conn.commit()
                conn.close()
                st.success("✅ تم حفظ البيانات بنجاح في قاعدة البيانات!")

# ---------------------------------------------------------
# 5. صفحة عرض وتعديل وحذف العقود (Read, Update, Delete)
# ---------------------------------------------------------
elif choice == "إدارة وتعديل العقود (Read/Update/Delete)":
    st.subheader("📋 قائمة العقود المسجلة (Grid view control)")
    
    conn = sqlite3.connect('contracts_db.db')
    df = pd.read_sql_query("SELECT * FROM Contracts", conn)
    conn.close()
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        
        st.markdown("---")
        col_edit, col_del = st.columns(2)
        
        with col_edit:
            st.subheader("✏️ تعديل عقد")
            selected_id = st.selectbox("اختر رقم العقد للتعديل", df['ContractID'].tolist(), key="edit_select")
            new_status = st.radio("تحديث حالة العقد", ["نشط", "مكتمل/ملغى"])
            
            if st.button("تحديث الحالة"):
                status_val = 1 if new_status == "نشط" else 0
                conn = sqlite3.connect('contracts_db.db')
                cursor = conn.cursor()
                cursor.execute("UPDATE Contracts SET Status = ? WHERE ContractID = ?", (status_val, selected_id))
                conn.commit()
                conn.close()
                st.success(f"تم تحديث العقد رقم {selected_id} بنجاح!")
                st.rerun()

        with col_del:
            st.subheader("🗑️ حذف عقد")
            delete_id = st.selectbox("اختر رقم العقد للحذف", df['ContractID'].tolist(), key="del_select")
            if st.button("حذف العقد المحدد", type="primary"):
                conn = sqlite3.connect('contracts_db.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Contracts WHERE ContractID = ?", (delete_id,))
                conn.commit()
                conn.close()
                st.success(f"تم حذف العقد رقم {delete_id} بنجاح!")
                st.rerun()
    else:
        st.info("لا توجد عقود مسجلة حالياً.")

# ---------------------------------------------------------
# 6. صفحة التذكير التلقائي المباشر (SMTP & AI)
# ---------------------------------------------------------
elif choice == "إرسال تنبيه بالذكاء الاصطناعي (SMTP & AI)":
    st.subheader("🤖 إرسال إيميل تذكيري مؤتمت")
    
    conn = sqlite3.connect('contracts_db.db')
    df = pd.read_sql_query("SELECT * FROM Contracts WHERE Status = 1", conn)
    conn.close()
    
    if not df.empty:
        contract_id = st.selectbox("اختر العقد المراد إرسال التنبيه له", df['ContractID'].tolist())
        selected_contract = df[df['ContractID'] == contract_id].iloc[0]
        
        st.write(f"**العقد:** {selected_contract['Title']} | **المسؤول:** {selected_contract['EmployeeEmail']} | **التاريخ:** {selected_contract['DueDate']}")
        
        default_body = f"""السلام عليكم ورحمة الله وبركاته،

نود تذكيركم بأن العقد/المهمة: ({selected_contract['Title']})
ينتهي بتاريخ: {selected_contract['DueDate']}.
مستوى الأهمية: {selected_contract['Priority']}.

يرجى اتخاذ الإجراءات اللازمة لتجديد العقد أو إنهاء المهمة في الموعد المحدد.

شاكرين لكم جهودكم."""

        email_body = st.text_area("نص البريد الإلكتروني (يمكنك تعديله قبل الإرسال):", value=default_body, height=180)
        
        st.markdown("---")
        
        if st.button("إرسال التنبيه البريدي الآن 📧"):
            success, msg = send_email_smtp(
                selected_contract['EmployeeEmail'],
                f"تذكير هام: قرب انتهاء عقد {selected_contract['Title']}",
                email_body
            )
            if success:
                st.success(msg)
                conn = sqlite3.connect('contracts_db.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO EmailLogs (ContractID, SentDate, EmailContent)
                    VALUES (?, datetime('now'), ?)
                ''', (contract_id, email_body))
                conn.commit()
                conn.close()
            else:
                st.error(msg)
    else:
        st.info("لا توجد عقود نشطة لإرسال تنبيهات لها.")

# ---------------------------------------------------------
# 7. تصدير التقارير (Export to Excel)
# ---------------------------------------------------------
elif choice == "تصدير التقارير (Export)":
    st.subheader("📊 تصدير سجلات العقود والإنذارات")
    
    conn = sqlite3.connect('contracts_db.db')
    df_contracts = pd.read_sql_query("SELECT * FROM Contracts", conn)
    conn.close()
    
    if not df_contracts.empty:
        st.dataframe(df_contracts)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_contracts.to_excel(writer, index=False, sheet_name='Contracts')
        processed_data = output.getvalue()
        
        st.download_button(
            label="📥 تحميل التقرير بصيغة Excel",
            data=processed_data,
            file_name="Contracts_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("لا توجد بيانات لتصديرها.")
