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
    <html>
    <body style="margin:0;padding:0;background:#0f172a;">
      <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background:#0f172a;padding:24px 12px;">
        <tr>
          <td align="center">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width:640px;">
              <tr>
                <td style="padding:0 0 12px 0;text-align:center;">
                  <span style="display:inline-block;padding:6px 14px;border-radius:999px;background:#1e3a8a;color:#bfdbfe;font-family:Arial,Helvetica,sans-serif;font-size:12px;font-weight:700;letter-spacing:0.5px;">FAULTECH</span>
                </td>
              </tr>
              <tr>
                <td style="background:linear-gradient(135deg,#2563eb 0%,#0a84ff 100%);padding:24px 24px 20px 24px;border-radius:16px 16px 0 0;">
                  <div style="font-family:Arial,Helvetica,sans-serif;font-size:12px;font-weight:700;color:#dbeafe;letter-spacing:0.8px;text-transform:uppercase;">Hesap Doğrulama</div>
                  <h1 style="margin:8px 0 0 0;font-family:Arial,Helvetica,sans-serif;font-size:28px;line-height:1.25;color:#ffffff;font-weight:800;">{subject}</h1>
                </td>
              </tr>
              <tr>
                <td style="background:#ffffff;border:1px solid #dbe3f0;border-top:0;border-radius:0 0 16px 16px;padding:24px;">
                  <p style="margin:0 0 14px 0;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.6;color:#0f172a;">
                    {greeting}
                  </p>
                  
                  <div style="margin:0 0 18px 0;padding:16px;border-radius:12px;background:#f8fafc;border:1px solid #e5e7eb;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.75;color:#1f2937;">
                    {intro}
                  </div>

                  <p style="margin:0 0 8px 0;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.6;color:#0f172a;font-weight:700;">
                    {instruction}
                  </p>

                  <div style="display:inline-block;background:#f3f4f6;border:1px solid #e5e7eb;padding:14px 18px;border-radius:10px;letter-spacing:6px;font-weight:800;font-size:28px;color:#0f172a;font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace;margin-bottom:10px;">
                    {code}
                  </div>
                  
                  <p style="margin:0 0 18px 0;font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#6b7280;">
                    {code_note}
                  </p>

                  <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin:0 0 16px 0;">
                    <tr>
                      <td style="padding:0 0 0 14px;border-left:4px solid #2563eb;">
                        <div style="font-family:Arial,Helvetica,sans-serif;font-size:13px;line-height:1.7;color:#475569;">
                          {outro}
                        </div>
                      </td>
                    </tr>
                  </table>
                  <p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:1.6;color:#334155;">
                    Sevgiler,<br/>
                    <strong style="color:#0f172a;">{getattr(settings, 'SITE_NAME', 'FaulTech')} Ekibi</strong>
                  </p>
                </td>
              </tr>
              <tr>
                <td style="padding:12px 8px 0 8px;text-align:center;">
                  <span style="font-family:Arial,Helvetica,sans-serif;font-size:12px;line-height:1.6;color:#94a3b8;">Bu e-posta {getattr(settings, 'SITE_NAME', 'FaulTech')} bildirim sistemi üzerinden gönderilmiştir.</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", None)
    to = [user.email]

    msg = EmailMultiAlternatives(subject=subject, body=text_body, from_email=from_email, to=to)
    msg.attach_alternative(html_body, "text/html")
    msg.send()


def send_new_device_email(user, lang=None):
    """Send a simplified email notifying the user that the device was changed.

    No device identifiers or details are included for privacy. Only a generic
    confirmation message is sent.
    """

    if lang:
        translation.activate(lang)

    subject = _("Device changed")
    greeting = _("Hello {first_name},").format(first_name=(user.first_name or user.username or ""))
    message_line = _("Your login device has been changed successfully.")
    outro = _("If this wasn’t you, please secure your account immediately.")

    # Text body (no device details)
    text_body = "\n".join([
        subject,
        "",
        greeting,
        message_line,
        "",
        outro,
    ])

    # Minimal HTML body
    html_body = f"""
    <html>
    <body style="margin:0;padding:0;background:#0f172a;">
      <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background:#0f172a;padding:24px 12px;">
        <tr>
          <td align="center">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width:640px;">
              <tr>
                <td style="padding:0 0 12px 0;text-align:center;">
                  <span style="display:inline-block;padding:6px 14px;border-radius:999px;background:#1e3a8a;color:#bfdbfe;font-family:Arial,Helvetica,sans-serif;font-size:12px;font-weight:700;letter-spacing:0.5px;">FAULTECH</span>
                </td>
              </tr>
              <tr>
                <td style="background:linear-gradient(135deg,#2563eb 0%,#0a84ff 100%);padding:24px 24px 20px 24px;border-radius:16px 16px 0 0;">
                  <div style="font-family:Arial,Helvetica,sans-serif;font-size:12px;font-weight:700;color:#dbeafe;letter-spacing:0.8px;text-transform:uppercase;">Güvenlik Uyarısı</div>
                  <h1 style="margin:8px 0 0 0;font-family:Arial,Helvetica,sans-serif;font-size:28px;line-height:1.25;color:#ffffff;font-weight:800;">{subject}</h1>
                </td>
              </tr>
              <tr>
                <td style="background:#ffffff;border:1px solid #dbe3f0;border-top:0;border-radius:0 0 16px 16px;padding:24px;">
                  <p style="margin:0 0 14px 0;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.6;color:#0f172a;">
                    {greeting}
                  </p>
                  
                  <div style="margin:0 0 18px 0;padding:16px;border-radius:12px;background:#f8fafc;border:1px solid #e5e7eb;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.75;color:#1f2937;">
                    {message_line}
                  </div>

                  <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin:0 0 16px 0;">
                    <tr>
                      <td style="padding:0 0 0 14px;border-left:4px solid #2563eb;">
                        <div style="font-family:Arial,Helvetica,sans-serif;font-size:13px;line-height:1.7;color:#475569;">
                          {outro}
                        </div>
                      </td>
                    </tr>
                  </table>
                  <p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:1.6;color:#334155;">
                    Sevgiler,<br/>
                    <strong style="color:#0f172a;">{getattr(settings, 'SITE_NAME', 'FaulTech')} Ekibi</strong>
                  </p>
                </td>
              </tr>
              <tr>
                <td style="padding:12px 8px 0 8px;text-align:center;">
                  <span style="font-family:Arial,Helvetica,sans-serif;font-size:12px;line-height:1.6;color:#94a3b8;">Bu e-posta {getattr(settings, 'SITE_NAME', 'FaulTech')} bildirim sistemi üzerinden gönderilmiştir.</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
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
    <html>
    <body style="margin:0;padding:0;background:#0f172a;">
      <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background:#0f172a;padding:24px 12px;">
        <tr>
          <td align="center">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width:640px;">
              <tr>
                <td style="padding:0 0 12px 0;text-align:center;">
                  <span style="display:inline-block;padding:6px 14px;border-radius:999px;background:#1e3a8a;color:#bfdbfe;font-family:Arial,Helvetica,sans-serif;font-size:12px;font-weight:700;letter-spacing:0.5px;">FAULTECH</span>
                </td>
              </tr>
              <tr>
                <td style="background:linear-gradient(135deg,#2563eb 0%,#0a84ff 100%);padding:24px 24px 20px 24px;border-radius:16px 16px 0 0;">
                  <div style="font-family:Arial,Helvetica,sans-serif;font-size:12px;font-weight:700;color:#dbeafe;letter-spacing:0.8px;text-transform:uppercase;">Güvenlik Kodu</div>
                  <h1 style="margin:8px 0 0 0;font-family:Arial,Helvetica,sans-serif;font-size:28px;line-height:1.25;color:#ffffff;font-weight:800;">{{subject}}</h1>
                </td>
              </tr>
              <tr>
                <td style="background:#ffffff;border:1px solid #dbe3f0;border-top:0;border-radius:0 0 16px 16px;padding:24px;">
                  <p style="margin:0 0 14px 0;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.6;color:#0f172a;">
                    {{greeting}}
                  </p>
                  
                  <div style="margin:0 0 18px 0;padding:16px;border-radius:12px;background:#f8fafc;border:1px solid #e5e7eb;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.75;color:#1f2937;">
                    {{intro}}
                  </div>

                  <p style="margin:0 0 8px 0;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.6;color:#0f172a;font-weight:700;">
                    {{instruction}}
                  </p>

                  <div style="display:inline-block;background:#f3f4f6;border:1px solid #e5e7eb;padding:14px 18px;border-radius:10px;letter-spacing:6px;font-weight:800;font-size:28px;color:#0f172a;font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace;margin-bottom:10px;">
                    {{code}}
                  </div>
                  
                  <p style="margin:0 0 18px 0;font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#6b7280;">
                    {{code_note}}
                  </p>

                  <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin:0 0 16px 0;">
                    <tr>
                      <td style="padding:0 0 0 14px;border-left:4px solid #2563eb;">
                        <div style="font-family:Arial,Helvetica,sans-serif;font-size:13px;line-height:1.7;color:#475569;">
                          {{outro}}
                        </div>
                      </td>
                    </tr>
                  </table>
                  <p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:1.6;color:#334155;">
                    Sevgiler,<br/>
                    <strong style="color:#0f172a;">{getattr(settings, 'SITE_NAME', 'FaulTech')} Ekibi</strong>
                  </p>
                </td>
              </tr>
              <tr>
                <td style="padding:12px 8px 0 8px;text-align:center;">
                  <span style="font-family:Arial,Helvetica,sans-serif;font-size:12px;line-height:1.6;color:#94a3b8;">Bu e-posta {getattr(settings, 'SITE_NAME', 'FaulTech')} bildirim sistemi üzerinden gönderilmiştir.</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
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
    <html>
    <body style="margin:0;padding:0;background:#0f172a;">
      <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background:#0f172a;padding:24px 12px;">
        <tr>
          <td align="center">
            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="max-width:640px;">
              <tr>
                <td style="padding:0 0 12px 0;text-align:center;">
                  <span style="display:inline-block;padding:6px 14px;border-radius:999px;background:#1e3a8a;color:#bfdbfe;font-family:Arial,Helvetica,sans-serif;font-size:12px;font-weight:700;letter-spacing:0.5px;">FAULTECH</span>
                </td>
              </tr>
              <tr>
                <td style="background:linear-gradient(135deg,#2563eb 0%,#0a84ff 100%);padding:24px 24px 20px 24px;border-radius:16px 16px 0 0;">
                  <div style="font-family:Arial,Helvetica,sans-serif;font-size:12px;font-weight:700;color:#dbeafe;letter-spacing:0.8px;text-transform:uppercase;">Şifre Sıfırlama</div>
                  <h1 style="margin:8px 0 0 0;font-family:Arial,Helvetica,sans-serif;font-size:28px;line-height:1.25;color:#ffffff;font-weight:800;">{subject}</h1>
                </td>
              </tr>
              <tr>
                <td style="background:#ffffff;border:1px solid #dbe3f0;border-top:0;border-radius:0 0 16px 16px;padding:24px;">
                  <p style="margin:0 0 14px 0;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.6;color:#0f172a;">
                    {greeting}
                  </p>
                  
                  <div style="margin:0 0 18px 0;padding:16px;border-radius:12px;background:#f8fafc;border:1px solid #e5e7eb;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.75;color:#1f2937;">
                    {intro}
                  </div>

                  <p style="margin:0 0 8px 0;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.6;color:#0f172a;font-weight:700;">
                    {instruction}
                  </p>

                  <div style="display:inline-block;background:#f3f4f6;border:1px solid #e5e7eb;padding:14px 18px;border-radius:10px;letter-spacing:6px;font-weight:800;font-size:28px;color:#0f172a;font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace;margin-bottom:10px;">
                    {code}
                  </div>
                  
                  <p style="margin:0 0 18px 0;font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#6b7280;">
                    {code_note}
                  </p>

                  <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="margin:0 0 16px 0;">
                    <tr>
                      <td style="padding:0 0 0 14px;border-left:4px solid #2563eb;">
                        <div style="font-family:Arial,Helvetica,sans-serif;font-size:13px;line-height:1.7;color:#475569;">
                          {outro}
                        </div>
                      </td>
                    </tr>
                  </table>
                  <p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:1.6;color:#334155;">
                    Sevgiler,<br/>
                    <strong style="color:#0f172a;">{getattr(settings, 'SITE_NAME', 'FaulTech')} Ekibi</strong>
                  </p>
                </td>
              </tr>
              <tr>
                <td style="padding:12px 8px 0 8px;text-align:center;">
                  <span style="font-family:Arial,Helvetica,sans-serif;font-size:12px;line-height:1.6;color:#94a3b8;">Bu e-posta {getattr(settings, 'SITE_NAME', 'FaulTech')} bildirim sistemi üzerinden gönderilmiştir.</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None) or getattr(settings, "EMAIL_HOST_USER", None)
    to = [user.email]

    msg = EmailMultiAlternatives(subject=subject, body=text_body, from_email=from_email, to=to)
    msg.attach_alternative(html_body, "text/html")
    msg.send()
