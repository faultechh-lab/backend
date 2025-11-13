from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import translation
from django.utils.translation import gettext as _


def get_client_ip(request):
    """Request'ten client IP adresini al"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """Request'ten user agent bilgisini al"""
    return request.META.get('HTTP_USER_AGENT', '')


def create_audit_log(user, action, request=None, details=None):
    """
    Audit log kaydı oluştur
    
    Args:
        user: User instance (None olabilir, anonim işlemler için)
        action: AuditLog.ActionChoices'dan bir seçim
        request: HttpRequest instance (opsiyonel)
        details: Ek detaylar dict formatında (opsiyonel)
    
    Returns:
        AuditLog instance
    """
    from .models import AuditLog
    
    ip_address = None
    user_agent = None
    
    if request:
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)
    
    return AuditLog.objects.create(
        user=user,
        action=action,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details
    )

def send_welcome_email(user, lang=None):
    
    if lang:
        translation.activate(lang)

    # Generate verification code
    code = user.generate_verification_code()

    # Email content (i18n)
    subject = _("Welcome to our platform")
    greeting = _("Hello {first_name},").format(first_name=(user.first_name or user.username or ""))
    intro = _("Thank you for registering. Please verify your email to activate your account.")
    instruction = _("Your verification code is:")
    code_note = _("This code will expire in 24 hours.")
    outro = _("If you didn’t create this account, you can ignore this email.")

    # Plain text
    text_body = "\n".join([
        subject,
        "",
        greeting,
        intro,
        "",
        f"{instruction} {code}",
        code_note,
        "",
        outro,
    ])

    # Branded HTML body inspired by the provided design (hero + dark intro band + features)
    html_body = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>{subject}</title>
      <style>
        body {{
          margin: 0 !important;
          padding: 0 !important;
          background-color: #f1f4f9;
          -webkit-text-size-adjust: 100%;
          -ms-text-size-adjust: 100%;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, Helvetica, sans-serif;
          color: #111827;
        }}
        .wrap {{
          width: 100%;
          padding: 24px 0;
          background: #f1f4f9;
        }}
        .card {{
          width: 100%;
          max-width: 720px;
          margin: 0 auto;
          background: #ffffff;
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 1px 2px rgba(0,0,0,0.05), 0 12px 24px rgba(0,0,0,0.06);
        }}
        .header {{
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 16px 20px;
          background: #ffffff;
          border-bottom: 1px solid #eef2f7;
        }}
        .logo {{
          width: 36px; height: 36px; border-radius: 8px; background:#0ea5e9; display:inline-block;
        }}
        .title {{ font-weight: 700; color:#0f172a; font-size: 16px; }}

        /* HERO - single image for maximum compatibility */
        .hero-single img {{ width:100%; height:auto; display:block; max-height:260px; object-fit:cover; }}
        .welcome-band {{ background:#111827; color:#ffffff; text-align:center; font-weight:800; font-size:20px; padding:14px 16px; }}

        /* DARK INTRO */
        .intro {{ background:#111827; color:#e5e7eb; padding: 22px 22px; text-align:center; }}
        .intro p {{ margin:0; line-height:1.7; font-size: 14px; }}

        /* CONTENT */
        .content {{ padding: 22px; }}
        .label {{ font-weight: 700; color:#111827; margin: 0 0 8px 0; }}
        .codebox {{ display:inline-block; background:#f3f4f6; border:1px solid #e5e7eb; padding: 14px 18px; border-radius:10px; letter-spacing: 6px; font-weight:800; font-size: 28px; color:#0f172a; font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; }}
        .note {{ color:#6b7280; margin: 10px 0 0 0; }}
        .divider {{ height:1px; background:#eef2f7; border:0; margin: 20px 0; }}

        /* FEATURES */
        .features {{ display:flex; justify-content: space-between; gap:12px; padding: 18px 22px 28px 22px; text-align:center; }}
        .feat {{ flex:1; color:#0f172a; }}
        .feat-icon {{ width:48px; height:48px; margin:0 auto 8px auto; color:#0f172a; }}
        .feat-title {{ font-weight: 700; font-size: 13px; color:#1f2937; }}

        .footer {{ text-align:center; color:#9ca3af; font-size:12px; padding: 0 22px 18px 22px; }}

        @media (max-width: 560px) {{
          .features {{ display:block; }}
          .feat {{ margin-bottom: 14px; }}
          .codebox {{ font-size: 22px; letter-spacing: 4px; }}
        }}
      </style>
    </head>
    <body>
      <div class="wrap">
        <div class="card">
          <!-- Header with logo and title -->
          <div class="header">
            <div class="title">FaultTech</div>
          </div>
          <div class="welcome-band">{subject}</div>

          <!-- Dark intro band -->
          <div class="intro">
            <p>{intro}</p>
          </div>

          <!-- Main content: greeting + code -->
          <div class="content">
            <p>{greeting}</p>
            <p class="label">{instruction}</p>
            <div class="codebox">{code}</div>
            <p class="note">{code_note}</p>
            <hr class="divider" />

            <!-- Features -->
   
            <p>{outro}</p>
          </div>

          <div class="footer">
            {getattr(settings, 'SITE_NAME', 'FaultTech')} · {getattr(settings, 'DEFAULT_FROM_EMAIL', '')}
          </div>
        </div>
      </div>
    </body>
    </html>
    """

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", None)
    to = [user.email]

    msg = EmailMultiAlternatives(subject=subject, body=text_body, from_email=from_email, to=to)
    msg.attach_alternative(html_body, "text/html")
    msg.send()


def send_new_device_email(user, lang=None):
    """Send an email notifying the user that a new device has been registered.

    This should be called right after a device renewal completes and the
    user's `device_id`/`device_info` are updated.
    """

    if lang:
        translation.activate(lang)

    subject = _("New device registered")
    greeting = _("Hello {first_name},").format(first_name=(user.first_name or user.username or ""))
    intro = _("A new device was just linked to your account.")
    details_label = _("Device details:")
    device_id_label = _("Device ID:")
    device_info_label = _("Device Info:")
    outro = _("If this wasn’t you, please secure your account immediately.")

    # Text body
    text_body = "\n".join([
        subject,
        "",
        greeting,
        intro,
        "",
        details_label,
        f"{device_id_label} {getattr(user, 'device_id', '') or '-'}",
        f"{device_info_label} {getattr(user, 'device_info', '') or '-'}",
        "",
        outro,
    ])

    # HTML body aligned with other templates
    html_body = f"""
    <!DOCTYPE html>
    <html lang=\"en\">
    <head>
      <meta charset=\"UTF-8\" />
      <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
      <title>{subject}</title>
      <style>
        body {{ margin:0; padding:0; background:#f1f4f9; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,Helvetica,sans-serif; color:#111827; }}
        .wrap {{ width:100%; padding:24px 0; }}
        .card {{ width:100%; max-width:720px; margin:0 auto; background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 1px 2px rgba(0,0,0,0.05),0 12px 24px rgba(0,0,0,0.06); }}
        .header {{ display:flex; align-items:center; gap:12px; padding:16px 20px; border-bottom:1px solid #eef2f7; }}
        .logo {{ width:36px; height:36px; border-radius:8px; background:#6366f1; display:inline-block; }}
        .title {{ font-weight:700; color:#0f172a; font-size:16px; }}
        .band {{ background:#111827; color:#fff; text-align:center; font-weight:800; font-size:20px; padding:14px 16px; }}
        .content {{ padding:22px; }}
        .label {{ font-weight:700; color:#111827; margin:0 0 8px 0; }}
        .row {{ margin:6px 0; color:#374151; }}
        .footer {{ text-align:center; color:#9ca3af; font-size:12px; padding:0 22px 18px 22px; }}
      </style>
    </head>
    <body>
      <div class=\"wrap\">
        <div class=\"card\">
          <div class="header">
            <div class="title">{getattr(settings, 'SITE_NAME', 'FaulTech')}</div>
          </div>
          <div class="band">{subject}</div>
          <div class=\"content\">
            <p>{greeting}</p>
            <p>{intro}</p>
            <p class=\"label\">{details_label}</p>
            <p class=\"row\"><strong>{device_id_label}</strong> {getattr(user, 'device_id', '') or '-'}</p>
            <p class=\"row\"><strong>{device_info_label}</strong> {getattr(user, 'device_info', '') or '-'}</p>
            <p style=\"margin-top:16px; color:#6b7280;\">{outro}</p>
          </div>
          <div class=\"footer\">{getattr(settings, 'SITE_NAME', 'FaulTech')} · {getattr(settings, 'DEFAULT_FROM_EMAIL', '')}</div>
        </div>
      </div>
    </body>
    </html>
    """

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", None)
    to = [user.email]

    msg = EmailMultiAlternatives(subject=subject, body=text_body, from_email=from_email, to=to)
    msg.attach_alternative(html_body, "text/html")
    msg.send()


def send_device_renewals_email(user, lang=None):
    """Send an email that contains the device renewal (device verification) code.

    Note: This function does NOT generate a new code; it uses the code already
    stored on the user (user.device_renewals_code). Ensure that
    user.generate_device_renewals_code() is called before invoking this.
    """

    if lang:
        translation.activate(lang)

    # Use existing code; fallback to generating if missing for safety
    code = user.device_renewals_code or user.generate_device_renewals_code()

    subject = _("Confirm device renewal")
    greeting = _("Hello {first_name},").format(first_name=(user.first_name or user.username or ""))
    intro = _("You requested to renew or change your login device. Use the code below to proceed.")
    instruction = _("Your device renewal code is:")
    code_note = _("This code will expire in 24 hours.")
    outro = _("If you didn’t request this, you can ignore this email.")

    # Text body
    text_body = "\n".join([
        subject,
        "",
        greeting,
        intro,
        "",
        f"{instruction} {code}",
        code_note,
        "",
        outro,
    ])

    # HTML body (aligned with other templates)
    html_body = f"""
    <!DOCTYPE html>
    <html lang=\"en\">
    <head>
      <meta charset=\"UTF-8\" />
      <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
      <title>{subject}</title>
      <style>
        body {{ margin:0; padding:0; background:#f1f4f9; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,Helvetica,sans-serif; color:#111827; }}
        .wrap {{ width:100%; padding:24px 0; }}
        .card {{ width:100%; max-width:720px; margin:0 auto; background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 1px 2px rgba(0,0,0,0.05),0 12px 24px rgba(0,0,0,0.06); }}
        .header {{ display:flex; align-items:center; gap:12px; padding:16px 20px; border-bottom:1px solid #eef2f7; }}
        .logo {{ width:36px; height:36px; border-radius:8px; background:#10b981; display:inline-block; }}
        .title {{ font-weight:700; color:#0f172a; font-size:16px; }}
        .band {{ background:#111827; color:#fff; text-align:center; font-weight:800; font-size:20px; padding:14px 16px; }}
        .content {{ padding:22px; }}
        .label {{ font-weight:700; color:#111827; margin:0 0 8px 0; }}
        .codebox {{ display:inline-block; background:#f3f4f6; border:1px solid #e5e7eb; padding:14px 18px; border-radius:10px; letter-spacing:6px; font-weight:800; font-size:28px; color:#0f172a; font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace; }}
        .note {{ color:#6b7280; margin:10px 0 0 0; }}
        .footer {{ text-align:center; color:#9ca3af; font-size:12px; padding:0 22px 18px 22px; }}
        @media (max-width:560px) {{ .codebox {{ font-size:22px; letter-spacing:4px; }} }}
      </style>
    </head>
    <body>
      <div class=\"wrap\">
        <div class=\"card\">
          <div class=\"header\">
            <div class=\"title\">{getattr(settings, 'SITE_NAME', 'FaulTech')}</div>
          </div>
          <div class=\"band\">{subject}</div>
          <div class=\"content\">
            <p>{greeting}</p>
            <p>{intro}</p>
            <p class=\"label\">{instruction}</p>
            <div class=\"codebox\">{code}</div>
            <p class=\"note\">{code_note}</p>
            <p style=\"margin-top:16px; color:#6b7280;\">{outro}</p>
          </div>
          <div class=\"footer\">{getattr(settings, 'SITE_NAME', 'FaulTech')} · {getattr(settings, 'DEFAULT_FROM_EMAIL', '')}</div>
        </div>
      </div>
    </body>
    </html>
    """

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", None)
    to = [user.email]

    msg = EmailMultiAlternatives(subject=subject, body=text_body, from_email=from_email, to=to)
    msg.attach_alternative(html_body, "text/html")
    msg.send()


def send_password_reset_email(user, lang=None):
    """Send a password reset email containing a one-time reset code.

    Args:
        user: User instance (must have email and generate_password_reset_code()).
        lang: Optional language code to activate translations for this email.
        reset_url: Optional deep link URL to a password reset page. If provided,
                   it will be included in the email alongside the code.
    """

    if lang:
        translation.activate(lang)

    # Generate password reset code
    code = user.generate_password_reset_code()

    # Localized content
    subject = _("Reset your password")
    greeting = _("Hello {first_name},").format(first_name=(user.first_name or user.username or ""))
    intro = _("You requested to reset your password. Use the code below to proceed")
    instruction = _("Your password reset code is:")
    code_note = _("This code will expire in 24 hours.")
    outro = _("If you didn’t request this, you can ignore this email.")

    # Optional CTA text
    cta_label = _("Reset Password")

    # Plain text body
    text_lines = [
        subject,
        "",
        greeting,
        intro,
        "",
        f"{instruction} {code}",
        code_note,
    ]
    text_lines.extend(["", outro])
    text_body = "\n".join(text_lines)

    # HTML body (reuses general styling used in welcome email)
    html_body = f"""
    <!DOCTYPE html>
    <html lang=\"en\">
    <head>
      <meta charset=\"UTF-8\" />
      <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
      <title>{subject}</title>
      <style>
        body {{
          margin: 0 !important;
          padding: 0 !important;
          background-color: #f1f4f9;
          -webkit-text-size-adjust: 100%;
          -ms-text-size-adjust: 100%;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, Helvetica, sans-serif;
          color: #111827;
        }}
        .wrap {{ width: 100%; padding: 24px 0; background: #f1f4f9; }}
        .card {{ width: 100%; max-width: 720px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 2px rgba(0,0,0,0.05), 0 12px 24px rgba(0,0,0,0.06); }}
        .header {{ display: flex; align-items: center; gap: 12px; padding: 16px 20px; background: #ffffff; border-bottom: 1px solid #eef2f7; }}
        .logo {{ width: 36px; height: 36px; border-radius: 8px; background:#ef4444; display:inline-block; }}
        .title {{ font-weight: 700; color:#0f172a; font-size: 16px; }}
        .hero-single img {{ width:100%; height:auto; display:block; max-height:260px; object-fit:cover; }}
        .band {{ background:#111827; color:#ffffff; text-align:center; font-weight:800; font-size:20px; padding:14px 16px; }}
        .intro {{ background:#111827; color:#e5e7eb; padding: 22px 22px; text-align:center; }}
        .intro p {{ margin:0; line-height:1.7; font-size: 14px; }}
        .content {{ padding: 22px; }}
        .label {{ font-weight: 700; color:#111827; margin: 0 0 8px 0; }}
        .codebox {{ display:inline-block; background:#f3f4f6; border:1px solid #e5e7eb; padding: 14px 18px; border-radius:10px; letter-spacing: 6px; font-weight:800; font-size: 28px; color:#0f172a; font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace; }}
        .note {{ color:#6b7280; margin: 10px 0 0 0; }}
        .divider {{ height:1px; background:#eef2f7; border:0; margin: 20px 0; }}
        .cta {{ display:inline-block; background:#ef4444; color:#ffffff !important; text-decoration:none; padding: 12px 18px; border-radius:10px; font-weight:700; margin-top: 12px; }}
        .footer {{ text-align:center; color:#9ca3af; font-size:12px; padding: 0 22px 18px 22px; }}
        @media (max-width: 560px) {{ .codebox {{ font-size: 22px; letter-spacing: 4px; }} }}
      </style>
    </head>
    <body>
      <div class=\"wrap\">
        <div class=\"card\">
          <div class=\"header\">
            <div class=\"title\">{getattr(settings, 'SITE_NAME', 'FaulTech')}</div>
          </div>
          <div class=\"band\">{subject}</div>
          <div class=\"content\">
            <p>{greeting}</p>
            <p>{intro}</p>
            <p class=\"label\">{instruction}</p>
            <div class=\"codebox\">{code}</div>
            <p class=\"note\">{code_note}</p>
            <hr class=\"divider\" />
            <p style=\"margin-top:16px; color:#6b7280;\">{outro}</p>
          </div>
          <div class=\"footer\">{getattr(settings, 'SITE_NAME', 'FaulTech')} · {getattr(settings, 'DEFAULT_FROM_EMAIL', '')}</div>
        </div>
      </div>
    </body>
    </html>
    """

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", None)
    to = [user.email]

    msg = EmailMultiAlternatives(subject=subject, body=text_body, from_email=from_email, to=to)
    msg.attach_alternative(html_body, "text/html")
    msg.send()