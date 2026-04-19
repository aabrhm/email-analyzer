import streamlit as st
import pdfplumber
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

PERSONAL_DOMAINS = [
    'gmail.com', 'hotmail.com', 'yahoo.com',
    'outlook.com', 'icloud.com', 'live.com',
    'mail.com', 'protonmail.com'
]

st.title("🔍 محلل الإيميلات")

uploaded_file = st.file_uploader("ارفع ملف PDF", type="pdf")
linkedin_email = st.text_input("إيميل LinkedIn")
linkedin_pass = st.text_input("كلمة مرور LinkedIn", type="password")

if uploaded_file and linkedin_email and linkedin_pass:
    if st.button("🚀 ابدأ التحليل"):
        with pdfplumber.open(uploaded_file) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
        
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        company_emails = [e for e in emails if e.split('@')[1] not in PERSONAL_DOMAINS]
        personal_emails = [e for e in emails if e.split('@')[1] in PERSONAL_DOMAINS]
        
        st.info(f"📧 إجمالي: {len(emails)} | 🏢 شركات: {len(company_emails)} | 👤 شخصي: {len(personal_emails)}")
        
        data = []
        
        for email in company_emails:
            domain = email.split('@')[1]
            company = domain.split('.')[0].capitalize()
            data.append({
                'الإيميل': email,
                'الاسم': '-',
                'الشركة': company,
                'المسمى': '-',
                'النوع': '🏢 شركة'
            })
        
        if personal_emails:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            driver = webdriver.Chrome(options=options)
            
            driver.get('https://www.linkedin.com/login')
            time.sleep(2)
            driver.find_element(By.ID, 'username').send_keys(linkedin_email)
            driver.find_element(By.ID, 'password').send_keys(linkedin_pass)
            driver.find_element(By.ID, 'password').send_keys(Keys.RETURN)
            time.sleep(3)
            
            progress = st.progress(0)
            
            for i, email in enumerate(personal_emails):
                try:
                    driver.get(f'https://www.linkedin.com/search/results/people/?keywords={email}')
                    time.sleep(2)
                    name = driver.find_element(By.CLASS_NAME, 'entity-result__title-text').text
                    company = driver.find_element(By.CLASS_NAME, 'entity-result__primary-subtitle').text
                    title = driver.find_element(By.CLASS_NAME, 'entity-result__secondary-subtitle').text
                    data.append({
                        'الإيميل': email,
                        'الاسم': name,
                        'الشركة': company,
                        'المسمى': title,
                        'النوع': '👤 شخصي'
                    })
                except:
                    data.append({
                        'الإيميل': email,
                        'الاسم': 'غير موجود',
                        'الشركة': 'غير موجود',
                        'المسمى': 'غير موجود',
                        'النوع': '👤 شخصي'
                    })
                progress.progress((i + 1) / len(personal_emails))
            
            driver.quit()
        
        df = pd.DataFrame(data)
        col1, col2, col3 = st.columns(3)
        col1.metric("إجمالي", len(df))
        col2.metric("شركات", len(df[df['النوع'] == '🏢 شركة']))
        col3.metric("شخصي", len(df[df['النوع'] == '👤 شخصي']))
        
        st.dataframe(df)
        
        df.to_excel('النتائج.xlsx', index=False)
        with open('النتائج.xlsx', 'rb') as f:
            st.download_button(
                label="📥 تحميل Excel",
                data=f,
                file_name='النتائج.xlsx'
            )
