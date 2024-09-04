import streamlit as st
from supabase import create_client
from functions import is_valid_email, new_verified, check_role
from gotrue.errors import AuthApiError
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, time, timedelta
import pytz
import random
import resend

resend.api_key = st.secrets["resend"]

india_tz = pytz.timezone('Asia/Kolkata')

# Initialize Supabase client
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]

supabase = create_client(url, key)

st.title("SIH Project")

def generate_time_slots(start_hour=10, end_hour=17, interval_minutes=30):
    slots = []
    current_time = time(start_hour, 0)
    end_time = time(end_hour, 0)
    while current_time < end_time:
        next_time = (datetime.combine(datetime.today(), current_time) + timedelta(minutes=interval_minutes)).time()
        slots.append(f"{current_time.strftime('%I:%M %p')} - {next_time.strftime('%I:%M %p')}")
        current_time = next_time
    return slots


@st.dialog("Get Details")
def postman_details(tracking_id, location, start_time, end_time, date, user_email, status):
    st.markdown(f"""
        <style>
            .location {{
                font-size: 20px;
                font-weight: bold;
                color: #2a9d8f;  /* Highlight color for location */
            }}
            .time-details {{
                font-size: 18px;
                font-weight: bold;
                color: #e76f51;  /* Highlight color for time details */
            }}
            .status {{
                font-size: 16px;
                font-weight: bold;
                color: #264653;  /* Darker color for status */
                background-color: #e9c46a;  /* Background color for status */
                padding: 5px;
                border-radius: 5px;
            }}
        </style>
        <div class="location">Location: {location}</div>
        <p>The tracking ID is: <strong>{tracking_id}</strong></p>
        <p class="time-details">Delivery Window: {start_time} - {end_time}</p>
        <p>Delivery Date: <strong>{date}</strong></p>
        <p>User Email: <strong>{user_email}</strong></p>
        <p class="status">Status: {status}</p>
    """, unsafe_allow_html=True)

    st.markdown("Update the status")
    with st.form(key="update_status"):
        response = supabase.table("package_details").select("otp").eq("tracking_id", tracking_id).execute()
        otp_real = str(response.data[0]['otp'])
        otp = st.text_input("Enter the OTP")
        submit = st.form_submit_button("Check")
        if submit:
            if otp_real==otp:
                supabase.table("package_details").update({"status": "Delivered"}).eq("tracking_id", tracking_id).execute()
                st.success("Changed status")
            else:
                st.error("Enter correct otp")

@st.dialog("Get Details")
def person_details(tracking_id, location, start_time, end_time, date, postman_email, status,otp):
    st.markdown(f"""
        <style>
            .location {{
                font-size: 20px;
                font-weight: bold;
                color: #2a9d8f;  /* Highlight color for location */
            }}
            .time-details {{
                font-size: 18px;
                font-weight: bold;
                color: #e76f51;  /* Highlight color for time details */
            }}
            .status {{
                font-size: 16px;
                font-weight: bold;
                color: #264653;  /* Darker color for status */
                background-color: #e9c46a;  /* Background color for status */
                padding: 5px;
                border-radius: 5px;
            }}
        </style>
        <div class="location">Location: {location}</div>
        <p>The tracking ID is: <strong>{tracking_id}</strong></p>
        <p class="time-details">Delivery Window: {start_time} to {end_time}</p>
        <p>Delivery Date: <strong>{date}</strong></p>
        <p>Postman Email: <strong>{postman_email}</strong></p>
        <p class="status">Status: {status}</p>
        <p> OTP:{otp}</p>
    """, unsafe_allow_html=True)

    st.markdown("You can change time slot below")
    with st.form(key="update_slot"):
        time_slots = generate_time_slots()
        time_slot = st.selectbox("Select Start Time:", time_slots)
        start_time_str, end_time_str = time_slot.split(" - ")
        start_time_obj = datetime.strptime(start_time_str, '%I:%M %p').time()
        end_time_obj = datetime.strptime(end_time_str, '%I:%M %p').time()
        start_index = start_time_obj.strftime('%H:%M:%S')
        end_index = end_time_obj.strftime('%H:%M:%S')
        submit = st.form_submit_button("Submit")
        if submit:
            supabase.table("package_details").update({"start_time": start_index, "end_time": end_index}).eq("tracking_id", tracking_id).execute()
            st.rerun()

if 'email' not in st.session_state:
    st.session_state['email'] = " "

if 'role' not in st.session_state:
    st.session_state['role'] = " "

if st.session_state['email'] ==" ":
    option = st.selectbox("What are your??",("User", "Postman", "Admin"))

    if option=="User":
        tab1,tab2 = st.tabs(["Register", "Login"])

        with tab1:
            with st.form(key="user_register"):
                email = st.text_input(label="Email*", help="Enter your email")
                password = st.text_input(label="Password*",help="Enter your password")
                confirm_password = st.text_input(label="Confirm Password*",help="Enter same password as above")
                st.markdown("**required*")
                submit = st.form_submit_button("Register")
                if submit:
                    if not email or not password or not confirm_password :
                        st.error("Enter all the mandatory fields")
                    elif not is_valid_email(email):
                        st.error("Enter a proper email")
                    elif password != confirm_password:
                        st.error("Password and Confirm Password should be same")
                    else:
                        try:
                            supabase.auth.sign_up({"email": email, "password": password})
                            st.success("Thanks for signing up! Check your email and confirm the email")
                        except Exception as e:
                            st.error(f"An unexpected error occurred during registration: {e}")

        with tab2:
            with st.form(key="user_login"):
                email = st.text_input(label="Email*",help="Enter the email you have used while registering")
                password = st.text_input(label="Password*",help="Enter the respective password")
                st.markdown("**required*")
                submit = st.form_submit_button("Login")
                if submit:
                    if not email or not password:
                        st.error("Enter all the mandatory fields")
                    elif not is_valid_email(email):
                        st.error("Enter a proper email")
                    else:
                        try:
                            session = supabase.auth.sign_in_with_password({"email": email, "password": password})
                            st.session_state['email'] = email
                            st.session_state['role'] = "User"
                        except AuthApiError as e:
                            if "Email not confirmed" in str(e):
                                st.warning("Error: Email not confirmed. Please confirm your email before logging in.")
                            else:
                                st.warning(f"AuthApiError: {e}")
                        except Exception as e:
                            st.warning(f"An unexpected error occurred during login: {e}")
                        with ThreadPoolExecutor() as executor:
                            if not st.session_state['email']==" ":
                                role = "User"
                                future = executor.submit(new_verified,email,role)
                                future.result()
                                st.rerun()

    elif option == "Postman":
        st.markdown("""
                    <h2>Postman Login</h2>
                    """,unsafe_allow_html=True)
        with st.form(key="postman_login"):
            email = st.text_input(label="Email*",help="Enter the email you have used while registering")
            password = st.text_input(label="Password*",help="Enter the respective password")
            st.markdown("**required*")
            submit = st.form_submit_button("Login")
            if submit:
                if not email or not password:
                    st.error("Enter all the mandatory fields")
                elif not is_valid_email(email):
                    st.error("Enter a proper email")
                elif not check_role(email,"Postman"):
                    st.warning("Invalid Login")
                else:
                    try:
                        session = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state['email'] = email
                        st.session_state['role'] = "Postman"
                    except AuthApiError as e:
                        if "Email not confirmed" in str(e):
                            st.warning("Error: Email not confirmed. Please confirm your email before logging in.")
                        else:
                            st.warning(f"AuthApiError: {e}")
                    except Exception as e:
                        st.warning(f"An unexpected error occurred during login: {e}")
                    with ThreadPoolExecutor() as executor:
                        if not st.session_state['email']==" ":
                            role = "Postman"
                            future = executor.submit(new_verified,email,role)
                            future.result()
                            st.rerun()

    elif option=="Admin":
        st.markdown("""
                    <h2>Admin Login</h2>
                    """,unsafe_allow_html=True)
        with st.form(key="admin_login"):
            email = st.text_input(label="Email*",help="Enter the email you have used while registering")
            password = st.text_input(label="Password*",help="Enter the respective password")
            st.markdown("**required*")
            submit = st.form_submit_button("Login")
            if submit:
                if not email or not password:
                    st.error("Enter all the mandatory fields")
                elif not is_valid_email(email):
                    st.error("Enter a proper email")
                elif not check_role(email,"Admin"):
                    st.warning("Invalid Login")
                else:
                    try:
                        session = supabase.auth.sign_in_with_password({"email": email, "password": password})
                        st.session_state['email'] = email
                        st.session_state['role'] = "Admin"
                    except AuthApiError as e:
                        if "Email not confirmed" in str(e):
                            st.warning("Error: Email not confirmed. Please confirm your email before logging in.")
                        else:
                            st.warning(f"AuthApiError: {e}")
                    except Exception as e:
                        st.warning(f"An unexpected error occurred during login: {e}")
                    with ThreadPoolExecutor() as executor:
                        if not st.session_state['email']==" ":
                            role = "Admin"
                            future = executor.submit(new_verified,email,role)
                            future.result()
                            st.rerun()
m = st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: rgb(204, 49, 49);
        width: 100%; /* Default to full width */
        max-width: 700px; /* Maximum width */
        padding: 10px 20px;
        border: none;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 12px;
    }
    </style>""", unsafe_allow_html=True)

if st.session_state['role'] == "Admin":
    with st.sidebar:
        logout = st.button("Logout")
        if logout:
            supabase.auth.sign_out()
            st.session_state['email'] = " "
            st.session_state['role'] = " "
            st.rerun()
    with st.form(key="admin_add"):
        tracking_id = st.text_input(label="Tracking id",help="Enter the unique tracking id for the product")
        response_postman = supabase.table("users").select("email").eq("role", "Postman").execute()
        emails_postman = [user['email'] for user in response_postman.data]
        postman_email = st.selectbox("Select a postman email:", emails_postman)
        location = st.text_input(label="Location",help="Enter the location where the product needs to be delivered")
        time_slots = generate_time_slots()
        time_slot = st.selectbox("Select Start Time:", time_slots)
        start_time_str, end_time_str = time_slot.split(" - ")
        start_time_obj = datetime.strptime(start_time_str, '%I:%M %p').time()
        end_time_obj = datetime.strptime(end_time_str, '%I:%M %p').time()
        start_time = start_time_obj.strftime('%H:%M:%S')
        end_time = end_time_obj.strftime('%H:%M:%S')
        date_str = st.date_input(label="Delivery Date")
        date = date_str.strftime('%Y/%m/%d')
        response_user = supabase.table("users").select("email").eq("role", "User").execute()
        emails_user = [user['email'] for user in response_user.data]
        user_email = st.selectbox("Select a user email:", emails_user)
        status = "Undelivered"
        otp = random.randint(100000, 999999)
        website_url = "https://optipost.streamlit.app/"
        submit = st.form_submit_button("Submit")
        if submit:
            if not tracking_id or not postman_email or not location or not start_time or not end_time or not date or not user_email or not status:
                st.warning("Enter all the attributes")
            else:
                supabase.table("package_details").insert({"tracking_id": tracking_id, "postman_email":postman_email, "location":location, "start_time":start_time, "end_time":end_time, "date":date, "user_email":user_email, "status":status, "otp":otp}).execute()
                st.success("Sucessfully added")
                params: resend.Emails.SendParams = {
                    "from": "OptiPost <no-reply@optipost.live>",
                    "to": [user_email],
                    "subject": "Your Delivery Details for the product {tracking_id}",
                    "html": f"""
                    <p>Hello,</p>
                    <p>Your tracking ID is: <strong>{tracking_id}</strong></p>
                    <p>Your time slot is: <strong>{start_time} - {end_time}</strong></p>
                    <p>Date of Delivery: <strong>{date}</strong></p>
                    <p>Postman email: <strong>{postman_email}</strong></p>
                    <p>Otp is : <strong>{otp}</strong></p>
                    <p>You can change the time slot using the website <a href='{website_url}'>here</a>.</p>
                    <p>Thank you for choosing our service!</p>
                """
                }
                resend.Emails.send(params)


elif st.session_state['role'] == "Postman":
    with st.sidebar:
        logout = st.button("Logout")
        if logout:
            supabase.auth.sign_out()
            st.session_state['email'] = " "
            st.session_state['role'] = " "
            st.rerun()
    st.markdown("""
                <h2>Todays Deliveries</h2>
                """, unsafe_allow_html=True)
    email = st.session_state['email']
    india_time = datetime.now(india_tz)
    today_date = india_time.date()
    query = supabase.table("package_details").select("*").eq("postman_email", email).eq("date", today_date).execute()
    for row in query.data:
        if st.button(row['tracking_id'], key=row['tracking_id']):
            postman_details(row['tracking_id'], row['location'], row['start_time'], row['end_time'], row['date'],row['user_email'],row['status'])

elif st.session_state['role'] == "User":
    with st.sidebar:
        logout = st.button("Logout")
        if logout:
            supabase.auth.sign_out()
            st.session_state['email'] = " "
            st.session_state['role'] = " "
            st.rerun()
    st.markdown("""
                <h2>All Deliveries</h2>
                """, unsafe_allow_html=True) 
    email = st.session_state['email']
    query = supabase.table("package_details").select("*").eq("user_email", email).execute()
    for row in query.data:
        if st.button(row['tracking_id'], key=row['tracking_id']):
            person_details(row['tracking_id'], row['location'], row['start_time'], row['end_time'], row['date'],row['postman_email'],row['status'],row['otp'])
