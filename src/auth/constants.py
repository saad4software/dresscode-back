ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"
BEARER_TOKEN_TYPE = "bearer"

USER_ROLE_CLIENT = "c"
USER_ROLE_ADMIN = "a"

JWT_SUBJECT_CLAIM = "sub"
JWT_USER_ID_CLAIM = "uid"
JWT_TYPE_CLAIM = "type"
JWT_ISSUED_AT_CLAIM = "iat"
JWT_EXPIRES_AT_CLAIM = "exp"
JWT_ID_CLAIM = "jti"

VERIFY_EMAIL_CODE_TYPE = "verify_email"
FORGET_PASSWORD_CODE_TYPE = "forget_password"
CHANGE_EMAIL_CODE_TYPE = "change_email"
EMAIL_CODE_TYPE_VALUES = frozenset(
    {
        VERIFY_EMAIL_CODE_TYPE,
        FORGET_PASSWORD_CODE_TYPE,
        CHANGE_EMAIL_CODE_TYPE,
    }
)

EMAIL_REGEX = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
MIN_VERIFICATION_CODE_LENGTH = 4
MAX_VERIFICATION_CODE_LENGTH = 12

AUTH_ROUTER_PREFIX = "/auth"
AUTH_ROUTER_TAG = "auth"
REGISTER_PATH = "/register"
LOGIN_SWAGGER_PATH = "/login_swagger"
LOGIN_PATH = "/login"
VERIFY_EMAIL_PATH = "/verify-email"
RESEND_VERIFICATION_CODE_PATH = "/resend-verification-code"
REFRESH_PATH = "/refresh"
CHANGE_PASSWORD_PATH = "/change-password"
ME_PATH = "/me"
OAUTH_TOKEN_URL = f"{AUTH_ROUTER_PREFIX}{LOGIN_SWAGGER_PATH}"

USER_TABLE_NAME = "user"
VERIFICATION_CODE_TABLE_NAME = "verification_code"
USER_ID_FOREIGN_KEY = "user.id"

BEARER_AUTH_HEADER = {"WWW-Authenticate": "Bearer"}
EMAIL_SUBJECT_TEMPLATE = "Your {app_name} verification code"
EMAIL_CODE_LINE_TEMPLATE = "Your {app_name} verification code is: {code}"
EMAIL_CODE_EXPIRY_LINE_TEMPLATE = "This code expires in {minutes} minutes."
EMAIL_IGNORE_LINE = "If you did not request this code, you can ignore this email."
EMAIL_HEADER_SUBJECT = "Subject"
EMAIL_HEADER_FROM = "From"
EMAIL_HEADER_TO = "To"
LOG_VERIFICATION_CODE_TEMPLATE = (
    "%s verification code for %s: %s. Configure SMTP_HOST to send emails."
)

DETAIL_INVALID_USERNAME_OR_PASSWORD = "Invalid username or password"
DETAIL_INVALID_ACCESS_TOKEN = "Invalid access token"
DETAIL_USERNAME_MUST_BE_EMAIL = "Username must be a valid email address"
DETAIL_EMAIL_NOT_VERIFIED = "Email address is not verified"
DETAIL_EMAIL_ALREADY_VERIFIED = "Email address is already verified"
DETAIL_INVALID_OR_EXPIRED_CODE = "Invalid or expired verification code"
DETAIL_VERIFICATION_EMAIL_NOT_SENT = (
    "Verification email could not be sent. Please try again later."
)
DETAIL_USER_MUST_BE_SAVED = "User must be saved before creating a verification code"
DETAIL_COULD_NOT_VALIDATE_CREDENTIALS = "Could not validate credentials"
DETAIL_INVALID_REFRESH_TOKEN = "Invalid refresh token"
DETAIL_USER_NO_LONGER_ACTIVE = "User no longer active"
DETAIL_USER_NOT_FOUND = "User not found"
DETAIL_USER_DISABLED = "User account is disabled"
DETAIL_TOKEN_INVALIDATED = "Token has been invalidated, please log in again"
DETAIL_USERNAME_TAKEN = "Username already taken"
DETAIL_CURRENT_PASSWORD_INCORRECT = "Current password is incorrect"
DETAIL_NEW_PASSWORD_MUST_DIFFER = "New password must differ from current password"
