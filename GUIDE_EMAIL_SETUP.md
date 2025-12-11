# How to Set Up Email for Viral Creator

To enable email notifications (like the login alert), you need to configure an SMTP server. The easiest way is to use a **Gmail** account with an **App Password**.

## Step 1: Get Google App Credentials

1.  Go to your [Google Account Security Settings](https://myaccount.google.com/security).
2.  Enable **2-Step Verification** if it isn't already enabled (this is required to use App Passwords).
3.  Search for **"App passwords"** in the search bar at the top, or look for it under the "How you sign in to Google" section.
    *   *Note: If you don't see "App passwords", it might be because:*
        *   *2-Step Verification is not set up.*
        *   *2-Step Verification is set up for security keys only.*
        *   *Your account is through work, school, or other organization.*
4.  Create a new App Password:
    *   **App name**: Enter "Viral Creator" (or any name you like).
    *   Click **Create**.
5.  Copy the 16-character password generated (it will look like `xxxx xxxx xxxx xxxx`).

## Step 2: Update Your `.env` File

Open the file `backend/.env` and add/update the following lines:

```env
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-16-char-app-password
MAIL_FROM=your-email@gmail.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
```

### Explanation of Variables
- `MAIL_USERNAME`: Your full Gmail address.
- `MAIL_PASSWORD`: The 16-character App Password you just generated (NOT your regular Google password).
- `MAIL_FROM`: The email address enabling the "From" field (usually same as USERNAME).
- `MAIL_PORT`: `587` (standard for TLS).
- `MAIL_SERVER`: `smtp.gmail.com` (for Google).

## Step 3: Restart Backend

After saving the `.env` file, you must **restart** the backend server for the changes to take effect.
