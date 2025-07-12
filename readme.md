[![Open in Codespaces](https://classroom.github.com/assets/launch-codespace-2972f46106e565e64193e422d61a12cf1da4916b45550586e14ef0a7c637dd04.svg)](https://classroom.github.com/open-in-codespaces?assignment_repo_id=17425689)
# transactionAcquirerSystem


# Getting started


1. Configure the Python Virtual Environment

   `python -m venv venv --prompt="transactionAcquirerSystem"`

2. Activate the Virtual Environment

   `venv\Scripts\activate`

3. Install dependencies (note addition of `supabase`)

   `pip install fastapi uvicorn jinja2 python-multipart httpx supabase`

4. Setup the `.env` file, e.g. based on `.env.example` - you will need to add your Supabase URL and API Key

5. To run the application

   `uvicorn app.main:app --reload --port=5000`



# Name: Elisha Tavagadza         Student Number: X00193877 

# Project Proposal: POS and ATM transaction Acquirer System

Project Title: POS and ATM transaction Acquirer System for Merchants and Financial Institutions

Project Overview:

This project covers the development of a POS and ATM transaction acquirer system designed to enable secure, real-time transaction processing between merchants and financial institutions. It will support a variety of payment types, including ATM cash withdrawals, balance inquiries, mini-statements, contact/contactless POS purchases, refunds, and e-commerce transactions. Additionally, the system will also facilitate payments using modern methods like Google Pay, Apple Pay, and digital wallets. The System will also support card networks such as Visa, MasterCard, Amex, Diners, and UPI.
The system will be developed using Python for backend operations, SQL for database management, and HTML, CSS, and JavaScript for frontend development. It will feature secure transaction processing, user-friendly interfaces for both merchants and financial institutions
