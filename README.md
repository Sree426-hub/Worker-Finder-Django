# Worker Finder — Hyperlocal Service Marketplace (Django Full-Stack)

**Live Demo:** [https://pythonanywhere.com](https://pythonanywhere.com)

## Project Overview
**Worker Finder** is a two-sided full-stack web application built with **Python, Django, SQLite, and Bootstrap 5** that connects local customers with verified home-service professionals (Plumbers, Electricians, Carpenters, AC Technicians, and Painters) across Bengaluru neighborhoods.

## Key Features & Business Logic
* **Hyperlocal Search & Urgent Filtering:** Filter workers by trade skill, neighborhood (Marathahalli, Whitefield, HSR Layout, Bellandur, Indiranagar), and real-time availability (**Available Now** vs. **Available by Appointment**).
* **Trust & Verification System:** Admin-approved **Verified** badges and transparent **Rate Cards** displayed upfront on worker profiles.
* **Double-Booking Prevention:** Backend date and time-slot conflict validation prevents overlapping bookings for the same worker.
* **4-Digit Job Start OTP Verification:** Generates a unique 4-digit PIN upon booking acceptance that the customer shares with the worker on-site to authenticate job completion.
* **Verified-Only Reviews & WhatsApp Connect:** Unlocks customer ratings strictly after a booking reaches `Completed` status, paired with 1-click pre-filled WhatsApp messaging.
* **1-Click Recruiter Demo Mode:** Built-in **Demo User Login** and **Demo Worker Login** with pre-seeded data for instant end-to-end testing.

## Tech Stack
* **Backend:** Python 3.13, Django 6.0
* **Frontend:** HTML5, CSS3, Bootstrap 5, Animate.css
* **Database:** SQLite3 (Django ORM)
* **Deployment:** PythonAnywhere

## Quick Demo Instructions
1. Visit **[://pythonanywhere.com](https://pythonanywhere.com)**.
2. Click **User Login → Demo User Login** to browse workers, view active OTP codes, and check booking statuses.
3. Click **Worker Login → Demo Worker Login** to toggle live availability, accept incoming requests, and verify customer start OTPs.
4.
