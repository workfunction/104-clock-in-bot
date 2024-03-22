class ExitCode:
    SUCCESS = 0
    SKIP_CLOCK_IN = 1
    NEED_SMS_AUTH = 2
    CANNOT_SOLVE_PUZZLE = 3
    OPERATION_TIMEOUT_EXCEEDED = 4
    NEED_EMAIL_AUTH = 7
    LOGIN_DENIED = 6
    TOO_MUCH_TRY = 69
    INVALID_OPTIONS = 77
    WRONG_PASSWORD = 87
    UNKNOWN_ERROR = 88

class Text:
    COIN_RECEIVED = '打卡成功'
    FAILURE = '很抱歉，您的身份驗證已遭到拒絕。'
    COIN_RECEIVED_EN = 'Clock punch was successful!'
    RECEIVE_COIN = '打卡成功'
    CLOCK_IN_TC = '打卡'
    CLOCK_IN_EN = 'Clock in/out'
    USE_LINK = '使用連結驗證'
    EMAIL_VERIFY = '身分驗證'
    CHROME_BOX = '注意！Google Chrome為唯一企業大師指定瀏覽器，'
    LOGIN_PROMPT = '會員登入'
    WRONG_PASSWORDS = [  '你的帳號或密碼不正確，請再試一次',
        '登入失敗，請稍後再試或使用其他登入方法',
        '您輸入的帳號或密碼不正確，若遇到困難，請重設您的密碼。'
    ]

class Config:
    TIMEOUT_AUTH = 10 * 60 * 1000     # 10 min
    TIMEOUT_OPERATION = 2 * 60 * 1000 # 2 min
    HEADERS_PATH = './104_http_headers.json'
    FB_CRED_PATH = './firebase-cred.json'
    COOKIE_PATH  = './cookie.json'
