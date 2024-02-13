#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ----------------------------------------------------------------------------
# Created By  : George Popovici
# Created Date: 01.2022
# version ='1.0'
# ---------------------------------------------------------------------------
"""
    Script that sends email with reservation information
    Currently used with reservation near end triggered task from Velocity
"""
# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import os
import sys
import math
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import libs.libs_velocity.Velocity as Velocity
import datetime
from datetime import timezone
import smtplib
from email.message import EmailMessage
from parameters.global_parameters import Reporting as REPORTINGPARAMS
from parameters.global_parameters import Velocity as VELOCITYPARAMS
from parameters.global_parameters import Mail as MAILPARAMS

import helpers.Logger as Local_logger
log_worker = Local_logger.create_logger(__name__, REPORTINGPARAMS["log_level_default"],
                                        REPORTINGPARAMS["test_log_path"], "s_send_reservation_email.txt")


def main():

# Get Velocity details and start session
    velocity = VELOCITYPARAMS['host']
    velo_user = VELOCITYPARAMS['user']
    velo_password = VELOCITYPARAMS['pass']
    base_url = f"http://{velocity}"
    velocity_session = Velocity.API(velocity, velo_user, velo_password)

    reservation_id = "current"

# Reservation id used for testing purposes
#    reservation_id = "57003789-9d9d-4340-b2a7-5516954fd21d"

# Get reservation details
    reservation_json = velocity_session.get_reservation(reservation_id)
    if not reservation_json:
        log_worker.error(f"Failed to get reservation with id {reservation_id}")
        return

    reservation_id = reservation_json['id']
    reservation_name = reservation_json['name']
    reservation_owner_id = reservation_json['ownerId']
    reservation_end = reservation_json['end']
    reservation_end_mins_remaining = calculate_minutes(reservation_end)
    reservation_end = datetime.datetime.fromtimestamp(reservation_end/1000.0).strftime('%Y-%m-%d %H:%M:%S')
    reservation_link = f"{base_url}/velocity/schedule/reservations/{reservation_id}/info"
    log_worker.info(f"Found reservation: {reservation_name}")

# Get reservation user details
    user_json = velocity_session.get_user_profile(reservation_owner_id)
    if not user_json:
        log_worker.error(f"Failed to get user JSON for id {reservation_owner_id}")
        return

    reservation_user = user_json['name']
    reservation_user_email = user_json['email']
    if reservation_user_email is None:
        reservation_user_email = "no_email"
        print("Email not available, using default one")
    print("Owned by user: " + reservation_user)
    log_worker.info(f"Owned by user: {reservation_user}")
    print("User email: " + reservation_user_email)
    log_worker.info(f"User email: {reservation_user_email}")

# Get smtp server and email related details
    smtp_server = MAILPARAMS['smtp_server']
    from_address = MAILPARAMS['from_email']
    to_address = MAILPARAMS['default_to_email']
    cc_address = to_address

    if reservation_user_email != "no_email":
        to_address = reservation_user_email

# Set the email content
    email_content = f"""
        Reservation  {reservation_name} will end in ~ {reservation_end_mins_remaining} minute(s).
        
        Link to reservation: {reservation_link}
        Reservation id: {reservation_id}
    
        This message was sent automatically by Velocity: {base_url} to user {reservation_user} ({reservation_user_email})
    """

    print(f"Email will be sent to {to_address}")
    log_worker.info(f"Email will be sent to: {to_address}")
    print(email_content)
    log_worker.info(f"{email_content}")

    msg = EmailMessage()
    msg.set_content(email_content)
    msg['Subject'] = f"{reservation_name} will end on {reservation_end}"
    msg['From'] = from_address
    msg['To'] = to_address
    msg['Cc'] = cc_address


    try:
        s = smtplib.SMTP(smtp_server)
        s.send_message(msg)
        log_worker.info(f"Email sent to: {to_address}")
        s.quit()
    except:
        log_worker.warning(f"Email NOT sent to: {to_address}")

    log_worker.info(f"Finished: PASSED")


def calculate_minutes(timestamp):
    dt = datetime.datetime.now(timezone.utc)
    utc_time = dt.replace(tzinfo=timezone.utc)
    utc_timestamp = utc_time.timestamp()
    diff = timestamp / 1000.0 - utc_timestamp
    diff_min = math.ceil(diff / 60)

    return diff_min


if __name__ == "__main__":
    main()