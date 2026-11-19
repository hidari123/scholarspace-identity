"""生成 identity-ui 的 12 种语言文案。

⚠️ 关键设计：**以 en-US 为基准生成**，保证 key 集合与占位符**结构上一致**。

    生成器做两件事：
      ① 复制 en-US 的 key 集合与占位符
      ② 把每条文案替换成对应语言的译文

    这样 L2 语言即使翻译不全，key 也不会缺 —— 回退到 en-US 的文案
    至少是**一致的一种语言**（这是 packages/ui 的 5 级回退链设计的初衷）。
"""

from pathlib import Path
import unicodedata

MESSAGES = Path(__file__).parent

# ⚠️ Biome 的 formatter 换行宽度 —— 必须与 conventions 一致，
#    否则生成器产出的文件永远过不了 format 检查。
#    见 packages/conventions/typescript/biome.json 的 formatter.lineWidth。
MAX_LINE_WIDTH = 100


def quote(value: str) -> str:
    """按 Biome 的偏好加引号。

    ⚠️ Biome 的 formatter 规则：字符串里**含单引号**时改用双引号，
    含双引号时改用单引号，都没有就用单引号。
    跟这个规则不一致 → 每次生成后都要手动 biome check --write。

    见 Biome 的 `useDoubleQuotes` / `quoteStyle` 规则。
    """
    if "'" in value and '"' not in value:
        return f'"{value}"'
    if '"' in value and "'" not in value:
        return f"'{value}'"
    # 两种引号都有 → 转义单引号（JS 惯例）
    escaped = value.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def display_width(text: str) -> int:
    """按**显示宽度**算长度（CJK 算 2 个字符宽）。

    ⚠️ 不能用 len() —— 中日韩字符在终端里占两列，
    但 Python 的 len() 只算 1。Biome 按显示宽度折行，
    所以这里必须用同样的算法，否则折行位置对不上。
    """
    width = 0
    for char in text:
        if unicodedata.east_asian_width(char) in ("F", "W"):
            width += 2
        elif unicodedata.combining(char):
            # ⚠️ 组合字符（如变音符号）占 0 列
            continue
        else:
            width += 1
    return width

# 各语言的翻译表 —— key → 译文
TRANSLATIONS: dict[str, dict[str, str]] = {
    "zh-TW": {
        "identity.title.signIn": "登入",
        "identity.title.signUp": "註冊",
        "identity.subtitle.signIn": "登入以繼續使用學術工作空間",
        "identity.subtitle.signUp": "建立帳號，開始你的學術旅程",
        "identity.tab.signIn": "登入",
        "identity.tab.signUp": "註冊",
        "identity.field.email": "電子郵件",
        "identity.field.emailPlaceholder": "name@example.com",
        "identity.field.password": "密碼",
        "identity.field.passwordPlaceholder": "至少 10 位，含數字與字母",
        "identity.field.phone": "手機號碼",
        "identity.field.phonePlaceholder": "13800138000",
        "identity.field.code": "驗證碼",
        "identity.field.codePlaceholder": "6 位數字",
        "identity.field.displayName": "暱稱",
        "identity.field.displayNamePlaceholder": "選填",
        "identity.action.signIn": "登入",
        "identity.action.signUp": "註冊",
        "identity.action.sendCode": "傳送驗證碼",
        "identity.action.resendCode": "重新傳送（{seconds} 秒）",
        "identity.action.wechat": "微信掃碼登入",
        "identity.action.google": "使用 Google 登入",
        "identity.action.github": "使用 GitHub 登入",
        "identity.action.switchToSignUp": "沒有帳號？去註冊",
        "identity.action.switchToSignIn": "已有帳號？去登入",
        "identity.action.back": "返回",
        "identity.divider.or": "或",
        "identity.state.sending": "傳送中…",
        "identity.state.verifying": "驗證中…",
        "identity.state.redirecting": "正在跳轉…",
        "identity.error.emailRequired": "請輸入電子郵件",
        "identity.error.emailInvalid": "電子郵件格式不正確",
        "identity.error.emailTaken": "該電子郵件已被註冊",
        "identity.error.passwordRequired": "請輸入密碼",
        "identity.error.passwordTooShort": "密碼至少 10 位",
        "identity.error.passwordNeedsNumber": "密碼需包含數字",
        "identity.error.passwordNeedsLetter": "密碼需包含字母",
        "identity.error.phoneRequired": "請輸入手機號碼",
        "identity.error.phoneInvalid": "手機號碼格式不正確",
        "identity.error.codeRequired": "請輸入驗證碼",
        "identity.error.codeInvalid": "驗證碼無效或已過期",
        "identity.error.credentialsInvalid": "電子郵件或密碼錯誤",
        "identity.error.accountSuspended": "帳號已被停用，請聯絡管理員",
        "identity.error.network": "網路異常，請檢查連線後重試",
        "identity.error.unknown": "發生未知錯誤",
        "identity.hint.emailRequired": "我們需要驗證您的電子郵件",
        "identity.hint.emailRequiredDescription":
            "電子郵件用於接收驗證郵件與找回密碼。部分登入方式（如微信）不提供電子郵件，需要手動補充。",
        "identity.hint.codeSent": "驗證碼已傳送至 {email}",
        "identity.hint.agreeToTerms": "註冊即表示同意服務條款與隱私政策",
    },
    "zh-HK": {
        "identity.title.signIn": "登入",
        "identity.title.signUp": "註冊",
        "identity.subtitle.signIn": "登入以繼續使用學術工作空間",
        "identity.subtitle.signUp": "建立帳戶，開始你的學術旅程",
        "identity.tab.signIn": "登入",
        "identity.tab.signUp": "註冊",
        "identity.field.email": "電郵",
        "identity.field.emailPlaceholder": "name@example.com",
        "identity.field.password": "密碼",
        "identity.field.passwordPlaceholder": "至少 10 位，含數字與字母",
        "identity.field.phone": "手機號碼",
        "identity.field.phonePlaceholder": "13800138000",
        "identity.field.code": "驗證碼",
        "identity.field.codePlaceholder": "6 位數字",
        "identity.field.displayName": "暱稱",
        "identity.field.displayNamePlaceholder": "選填",
        "identity.action.signIn": "登入",
        "identity.action.signUp": "註冊",
        "identity.action.sendCode": "發送驗證碼",
        "identity.action.resendCode": "重新發送（{seconds} 秒）",
        "identity.action.wechat": "微信掃碼登入",
        "identity.action.google": "使用 Google 登入",
        "identity.action.github": "使用 GitHub 登入",
        "identity.action.switchToSignUp": "沒有帳戶？去註冊",
        "identity.action.switchToSignIn": "已有帳戶？去登入",
        "identity.action.back": "返回",
        "identity.divider.or": "或",
        "identity.state.sending": "發送中…",
        "identity.state.verifying": "驗證中…",
        "identity.state.redirecting": "正在跳轉…",
        "identity.error.emailRequired": "請輸入電郵",
        "identity.error.emailInvalid": "電郵格式不正確",
        "identity.error.emailTaken": "該電郵已被註冊",
        "identity.error.passwordRequired": "請輸入密碼",
        "identity.error.passwordTooShort": "密碼至少 10 位",
        "identity.error.passwordNeedsNumber": "密碼需包含數字",
        "identity.error.passwordNeedsLetter": "密碼需包含字母",
        "identity.error.phoneRequired": "請輸入手機號碼",
        "identity.error.phoneInvalid": "手機號碼格式不正確",
        "identity.error.codeRequired": "請輸入驗證碼",
        "identity.error.codeInvalid": "驗證碼無效或已過期",
        "identity.error.credentialsInvalid": "電郵或密碼錯誤",
        "identity.error.accountSuspended": "帳戶已被停用，請聯絡管理員",
        "identity.error.network": "網絡異常，請檢查連線後重試",
        "identity.error.unknown": "發生未知錯誤",
        "identity.hint.emailRequired": "我們需要驗證您的電郵",
        "identity.hint.emailRequiredDescription":
            "電郵用於接收驗證郵件與找回密碼。部分登入方式（如微信）不提供電郵，需要手動補充。",
        "identity.hint.codeSent": "驗證碼已發送至 {email}",
        "identity.hint.agreeToTerms": "註冊即表示同意服務條款與私隱政策",
    },
    "ja-JP": {
        "identity.title.signIn": "ログイン",
        "identity.title.signUp": "新規登録",
        "identity.subtitle.signIn": "ログインして学術ワークスペースを使い続けましょう",
        "identity.subtitle.signUp": "アカウントを作成して学術の旅を始めましょう",
        "identity.tab.signIn": "ログイン",
        "identity.tab.signUp": "新規登録",
        "identity.field.email": "メールアドレス",
        "identity.field.emailPlaceholder": "name@example.com",
        "identity.field.password": "パスワード",
        "identity.field.passwordPlaceholder": "10 文字以上、数字と英字を含めてください",
        "identity.field.phone": "電話番号",
        "identity.field.phonePlaceholder": "13800138000",
        "identity.field.code": "確認コード",
        "identity.field.codePlaceholder": "6 桁の数字",
        "identity.field.displayName": "表示名",
        "identity.field.displayNamePlaceholder": "任意",
        "identity.action.signIn": "ログイン",
        "identity.action.signUp": "登録",
        "identity.action.sendCode": "確認コードを送信",
        "identity.action.resendCode": "再送信（{seconds} 秒）",
        "identity.action.wechat": "WeChat でログイン",
        "identity.action.google": "Google でログイン",
        "identity.action.github": "GitHub でログイン",
        "identity.action.switchToSignUp": "アカウントがありませんか？新規登録",
        "identity.action.switchToSignIn": "すでにアカウントをお持ちですか？ログイン",
        "identity.action.back": "戻る",
        "identity.divider.or": "または",
        "identity.state.sending": "送信中…",
        "identity.state.verifying": "確認中…",
        "identity.state.redirecting": "転送中…",
        "identity.error.emailRequired": "メールアドレスを入力してください",
        "identity.error.emailInvalid": "メールアドレスの形式が正しくありません",
        "identity.error.emailTaken": "このメールアドレスは既に登録されています",
        "identity.error.passwordRequired": "パスワードを入力してください",
        "identity.error.passwordTooShort": "パスワードは 10 文字以上必要です",
        "identity.error.passwordNeedsNumber": "パスワードには数字が必要です",
        "identity.error.passwordNeedsLetter": "パスワードには英字が必要です",
        "identity.error.phoneRequired": "電話番号を入力してください",
        "identity.error.phoneInvalid": "電話番号の形式が正しくありません",
        "identity.error.codeRequired": "確認コードを入力してください",
        "identity.error.codeInvalid": "確認コードが無効か、有効期限が切れています",
        "identity.error.credentialsInvalid": "メールアドレスまたはパスワードが正しくありません",
        "identity.error.accountSuspended": "このアカウントは停止されています。管理者にお問い合わせください。",
        "identity.error.network": "ネットワークエラーです。接続を確認して再試行してください。",
        "identity.error.unknown": "不明なエラーが発生しました",
        "identity.hint.emailRequired": "メールアドレスの確認が必要です",
        "identity.hint.emailRequiredDescription":
            "メールアドレスは確認メールの送信とパスワード復旧に使用されます。WeChat など一部のログイン方法はメールアドレスを提供しないため、手動で追加する必要があります。",
        "identity.hint.codeSent": "確認コードを {email} に送信しました",
        "identity.hint.agreeToTerms": "登録により利用規約とプライバシーポリシーに同意したものとみなされます",
    },
    "ko-KR": {
        "identity.title.signIn": "로그인",
        "identity.title.signUp": "회원가입",
        "identity.subtitle.signIn": "로그인하고 학술 작업 공간을 계속 사용하세요",
        "identity.subtitle.signUp": "계정을 만들고 학술 여정을 시작하세요",
        "identity.tab.signIn": "로그인",
        "identity.tab.signUp": "회원가입",
        "identity.field.email": "이메일",
        "identity.field.emailPlaceholder": "name@example.com",
        "identity.field.password": "비밀번호",
        "identity.field.passwordPlaceholder": "10자 이상, 숫자와 문자 포함",
        "identity.field.phone": "전화번호",
        "identity.field.phonePlaceholder": "13800138000",
        "identity.field.code": "인증 코드",
        "identity.field.codePlaceholder": "6자리 숫자",
        "identity.field.displayName": "닉네임",
        "identity.field.displayNamePlaceholder": "선택 사항",
        "identity.action.signIn": "로그인",
        "identity.action.signUp": "가입",
        "identity.action.sendCode": "인증 코드 전송",
        "identity.action.resendCode": "다시 보내기 ({seconds}초)",
        "identity.action.wechat": "WeChat으로 로그인",
        "identity.action.google": "Google로 로그인",
        "identity.action.github": "GitHub로 로그인",
        "identity.action.switchToSignUp": "계정이 없으신가요? 가입하기",
        "identity.action.switchToSignIn": "이미 계정이 있으신가요? 로그인",
        "identity.action.back": "뒤로",
        "identity.divider.or": "또는",
        "identity.state.sending": "전송 중…",
        "identity.state.verifying": "확인 중…",
        "identity.state.redirecting": "이동 중…",
        "identity.error.emailRequired": "이메일을 입력하세요",
        "identity.error.emailInvalid": "이메일 형식이 올바르지 않습니다",
        "identity.error.emailTaken": "이미 등록된 이메일입니다",
        "identity.error.passwordRequired": "비밀번호를 입력하세요",
        "identity.error.passwordTooShort": "비밀번호는 10자 이상이어야 합니다",
        "identity.error.passwordNeedsNumber": "비밀번호에 숫자가 포함되어야 합니다",
        "identity.error.passwordNeedsLetter": "비밀번호에 문자가 포함되어야 합니다",
        "identity.error.phoneRequired": "전화번호를 입력하세요",
        "identity.error.phoneInvalid": "전화번호 형식이 올바르지 않습니다",
        "identity.error.codeRequired": "인증 코드를 입력하세요",
        "identity.error.codeInvalid": "인증 코드가 유효하지 않거나 만료되었습니다",
        "identity.error.credentialsInvalid": "이메일 또는 비밀번호가 올바르지 않습니다",
        "identity.error.accountSuspended": "계정이 정지되었습니다. 관리자에게 문의하세요.",
        "identity.error.network": "네트워크 오류입니다. 연결을 확인하고 다시 시도하세요.",
        "identity.error.unknown": "알 수 없는 오류가 발생했습니다",
        "identity.hint.emailRequired": "이메일 확인이 필요합니다",
        "identity.hint.emailRequiredDescription":
            "이메일은 인증 메일 발송과 비밀번호 복구에 사용됩니다. WeChat 등 일부 로그인 방식은 이메일을 제공하지 않으므로 직접 추가해야 합니다.",
        "identity.hint.codeSent": "인증 코드를 {email}(으)로 보냈습니다",
        "identity.hint.agreeToTerms": "가입하면 서비스 약관 및 개인정보 처리방침에 동의하게 됩니다",
    },
    "fr-FR": {
        "identity.title.signIn": "Se connecter",
        "identity.title.signUp": "S'inscrire",
        "identity.subtitle.signIn": "Connectez-vous pour continuer à utiliser votre espace académique",
        "identity.subtitle.signUp": "Créez un compte pour commencer votre parcours académique",
        "identity.tab.signIn": "Connexion",
        "identity.tab.signUp": "Inscription",
        "identity.field.email": "E-mail",
        "identity.field.emailPlaceholder": "name@example.com",
        "identity.field.password": "Mot de passe",
        "identity.field.passwordPlaceholder": "Au moins 10 caractères, avec un chiffre et une lettre",
        "identity.field.phone": "Numéro de téléphone",
        "identity.field.phonePlaceholder": "13800138000",
        "identity.field.code": "Code de vérification",
        "identity.field.codePlaceholder": "6 chiffres",
        "identity.field.displayName": "Nom affiché",
        "identity.field.displayNamePlaceholder": "Facultatif",
        "identity.action.signIn": "Se connecter",
        "identity.action.signUp": "S'inscrire",
        "identity.action.sendCode": "Envoyer le code",
        "identity.action.resendCode": "Renvoyer dans {seconds} s",
        "identity.action.wechat": "Se connecter avec WeChat",
        "identity.action.google": "Se connecter avec Google",
        "identity.action.github": "Se connecter avec GitHub",
        "identity.action.switchToSignUp": "Pas de compte ? Inscrivez-vous",
        "identity.action.switchToSignIn": "Déjà un compte ? Connectez-vous",
        "identity.action.back": "Retour",
        "identity.divider.or": "ou",
        "identity.state.sending": "Envoi…",
        "identity.state.verifying": "Vérification…",
        "identity.state.redirecting": "Redirection…",
        "identity.error.emailRequired": "L'e-mail est requis",
        "identity.error.emailInvalid": "Adresse e-mail invalide",
        "identity.error.emailTaken": "Cette adresse e-mail est déjà enregistrée",
        "identity.error.passwordRequired": "Le mot de passe est requis",
        "identity.error.passwordTooShort": "Le mot de passe doit contenir au moins 10 caractères",
        "identity.error.passwordNeedsNumber": "Le mot de passe doit contenir un chiffre",
        "identity.error.passwordNeedsLetter": "Le mot de passe doit contenir une lettre",
        "identity.error.phoneRequired": "Le numéro de téléphone est requis",
        "identity.error.phoneInvalid": "Numéro de téléphone invalide",
        "identity.error.codeRequired": "Le code de vérification est requis",
        "identity.error.codeInvalid": "Code de vérification invalide ou expiré",
        "identity.error.credentialsInvalid": "E-mail ou mot de passe incorrect",
        "identity.error.accountSuspended": "Ce compte est suspendu. Contactez un administrateur.",
        "identity.error.network": "Erreur réseau. Vérifiez votre connexion et réessayez.",
        "identity.error.unknown": "Une erreur inconnue est survenue",
        "identity.hint.emailRequired": "Nous devons vérifier votre e-mail",
        "identity.hint.emailRequiredDescription":
            "Votre e-mail sert à recevoir les messages de vérification et à récupérer votre mot de passe. Certaines méthodes de connexion (comme WeChat) ne fournissent pas d'e-mail : vous devrez en ajouter un manuellement.",
        "identity.hint.codeSent": "Code de vérification envoyé à {email}",
        "identity.hint.agreeToTerms": "En vous inscrivant, vous acceptez les Conditions d'utilisation et la Politique de confidentialité",
    },
    "de-DE": {
        "identity.title.signIn": "Anmelden",
        "identity.title.signUp": "Registrieren",
        "identity.subtitle.signIn": "Melden Sie sich an, um Ihren akademischen Arbeitsbereich weiter zu nutzen",
        "identity.subtitle.signUp": "Erstellen Sie ein Konto für Ihre akademische Reise",
        "identity.tab.signIn": "Anmelden",
        "identity.tab.signUp": "Registrieren",
        "identity.field.email": "E-Mail",
        "identity.field.emailPlaceholder": "name@example.com",
        "identity.field.password": "Passwort",
        "identity.field.passwordPlaceholder": "Mindestens 10 Zeichen, mit Ziffer und Buchstabe",
        "identity.field.phone": "Telefonnummer",
        "identity.field.phonePlaceholder": "13800138000",
        "identity.field.code": "Bestätigungscode",
        "identity.field.codePlaceholder": "6 Ziffern",
        "identity.field.displayName": "Anzeigename",
        "identity.field.displayNamePlaceholder": "Optional",
        "identity.action.signIn": "Anmelden",
        "identity.action.signUp": "Registrieren",
        "identity.action.sendCode": "Code senden",
        "identity.action.resendCode": "Erneut senden ({seconds} Sek.)",
        "identity.action.wechat": "Mit WeChat anmelden",
        "identity.action.google": "Mit Google anmelden",
        "identity.action.github": "Mit GitHub anmelden",
        "identity.action.switchToSignUp": "Kein Konto? Registrieren",
        "identity.action.switchToSignIn": "Schon ein Konto? Anmelden",
        "identity.action.back": "Zurück",
        "identity.divider.or": "oder",
        "identity.state.sending": "Wird gesendet…",
        "identity.state.verifying": "Wird geprüft…",
        "identity.state.redirecting": "Weiterleitung…",
        "identity.error.emailRequired": "E-Mail ist erforderlich",
        "identity.error.emailInvalid": "Ungültige E-Mail-Adresse",
        "identity.error.emailTaken": "Diese E-Mail-Adresse ist bereits registriert",
        "identity.error.passwordRequired": "Passwort ist erforderlich",
        "identity.error.passwordTooShort": "Das Passwort muss mindestens 10 Zeichen lang sein",
        "identity.error.passwordNeedsNumber": "Das Passwort muss eine Ziffer enthalten",
        "identity.error.passwordNeedsLetter": "Das Passwort muss einen Buchstaben enthalten",
        "identity.error.phoneRequired": "Telefonnummer ist erforderlich",
        "identity.error.phoneInvalid": "Ungültige Telefonnummer",
        "identity.error.codeRequired": "Bestätigungscode ist erforderlich",
        "identity.error.codeInvalid": "Bestätigungscode ungültig oder abgelaufen",
        "identity.error.credentialsInvalid": "E-Mail oder Passwort ist falsch",
        "identity.error.accountSuspended": "Dieses Konto ist gesperrt. Bitte wenden Sie sich an eine Administration.",
        "identity.error.network": "Netzwerkfehler. Prüfen Sie Ihre Verbindung und versuchen Sie es erneut.",
        "identity.error.unknown": "Ein unbekannter Fehler ist aufgetreten",
        "identity.hint.emailRequired": "Wir müssen Ihre E-Mail-Adresse verifizieren",
        "identity.hint.emailRequiredDescription":
            "Ihre E-Mail-Adresse wird für Bestätigungsmails und zur Wiederherstellung des Passworts genutzt. Einige Anmeldearten (etwa WeChat) liefern keine E-Mail-Adresse — dann müssen Sie sie manuell ergänzen.",
        "identity.hint.codeSent": "Bestätigungscode an {email} gesendet",
        "identity.hint.agreeToTerms": "Mit der Registrierung stimmen Sie den Nutzungsbedingungen und der Datenschutzerklärung zu",
    },
    "es-ES": {
        "identity.title.signIn": "Iniciar sesión",
        "identity.title.signUp": "Registrarse",
        "identity.subtitle.signIn": "Inicia sesión para seguir usando tu espacio académico",
        "identity.subtitle.signUp": "Crea una cuenta para empezar tu viaje académico",
        "identity.tab.signIn": "Iniciar sesión",
        "identity.tab.signUp": "Registrarse",
        "identity.field.email": "Correo electrónico",
        "identity.field.emailPlaceholder": "name@example.com",
        "identity.field.password": "Contraseña",
        "identity.field.passwordPlaceholder": "Al menos 10 caracteres, con un número y una letra",
        "identity.field.phone": "Número de teléfono",
        "identity.field.phonePlaceholder": "13800138000",
        "identity.field.code": "Código de verificación",
        "identity.field.codePlaceholder": "6 dígitos",
        "identity.field.displayName": "Nombre visible",
        "identity.field.displayNamePlaceholder": "Opcional",
        "identity.action.signIn": "Iniciar sesión",
        "identity.action.signUp": "Registrarse",
        "identity.action.sendCode": "Enviar código",
        "identity.action.resendCode": "Reenviar en {seconds} s",
        "identity.action.wechat": "Iniciar sesión con WeChat",
        "identity.action.google": "Iniciar sesión con Google",
        "identity.action.github": "Iniciar sesión con GitHub",
        "identity.action.switchToSignUp": "¿Sin cuenta? Regístrate",
        "identity.action.switchToSignIn": "¿Ya tienes cuenta? Inicia sesión",
        "identity.action.back": "Atrás",
        "identity.divider.or": "o",
        "identity.state.sending": "Enviando…",
        "identity.state.verifying": "Verificando…",
        "identity.state.redirecting": "Redirigiendo…",
        "identity.error.emailRequired": "El correo electrónico es obligatorio",
        "identity.error.emailInvalid": "Correo electrónico no válido",
        "identity.error.emailTaken": "Este correo electrónico ya está registrado",
        "identity.error.passwordRequired": "La contraseña es obligatoria",
        "identity.error.passwordTooShort": "La contraseña debe tener al menos 10 caracteres",
        "identity.error.passwordNeedsNumber": "La contraseña debe contener un número",
        "identity.error.passwordNeedsLetter": "La contraseña debe contener una letra",
        "identity.error.phoneRequired": "El número de teléfono es obligatorio",
        "identity.error.phoneInvalid": "Número de teléfono no válido",
        "identity.error.codeRequired": "El código de verificación es obligatorio",
        "identity.error.codeInvalid": "Código de verificación no válido o caducado",
        "identity.error.credentialsInvalid": "Correo electrónico o contraseña incorrectos",
        "identity.error.accountSuspended": "Esta cuenta está suspendida. Contacta con un administrador.",
        "identity.error.network": "Error de red. Comprueba tu conexión e inténtalo de nuevo.",
        "identity.error.unknown": "Se ha producido un error desconocido",
        "identity.hint.emailRequired": "Necesitamos verificar tu correo electrónico",
        "identity.hint.emailRequiredDescription":
            "Tu correo electrónico se usa para recibir la verificación y recuperar la contraseña. Algunos métodos de acceso (como WeChat) no proporcionan correo electrónico, así que tendrás que añadirlo manualmente.",
        "identity.hint.codeSent": "Código de verificación enviado a {email}",
        "identity.hint.agreeToTerms": "Al registrarte aceptas los Términos del Servicio y la Política de Privacidad",
    },
    "pt-BR": {
        "identity.title.signIn": "Entrar",
        "identity.title.signUp": "Cadastrar-se",
        "identity.subtitle.signIn": "Entre para continuar usando seu espaço acadêmico",
        "identity.subtitle.signUp": "Crie uma conta para começar sua jornada acadêmica",
        "identity.tab.signIn": "Entrar",
        "identity.tab.signUp": "Cadastrar-se",
        "identity.field.email": "E-mail",
        "identity.field.emailPlaceholder": "name@example.com",
        "identity.field.password": "Senha",
        "identity.field.passwordPlaceholder": "Pelo menos 10 caracteres, com número e letra",
        "identity.field.phone": "Número de telefone",
        "identity.field.phonePlaceholder": "13800138000",
        "identity.field.code": "Código de verificação",
        "identity.field.codePlaceholder": "6 dígitos",
        "identity.field.displayName": "Nome de exibição",
        "identity.field.displayNamePlaceholder": "Opcional",
        "identity.action.signIn": "Entrar",
        "identity.action.signUp": "Cadastrar-se",
        "identity.action.sendCode": "Enviar código",
        "identity.action.resendCode": "Reenviar em {seconds}s",
        "identity.action.wechat": "Entrar com WeChat",
        "identity.action.google": "Entrar com Google",
        "identity.action.github": "Entrar com GitHub",
        "identity.action.switchToSignUp": "Sem conta? Cadastre-se",
        "identity.action.switchToSignIn": "Já tem conta? Entre",
        "identity.action.back": "Voltar",
        "identity.divider.or": "ou",
        "identity.state.sending": "Enviando…",
        "identity.state.verifying": "Verificando…",
        "identity.state.redirecting": "Redirecionando…",
        "identity.error.emailRequired": "O e-mail é obrigatório",
        "identity.error.emailInvalid": "Endereço de e-mail inválido",
        "identity.error.emailTaken": "Este e-mail já está registrado",
        "identity.error.passwordRequired": "A senha é obrigatória",
        "identity.error.passwordTooShort": "A senha deve ter pelo menos 10 caracteres",
        "identity.error.passwordNeedsNumber": "A senha deve conter um número",
        "identity.error.passwordNeedsLetter": "A senha deve conter uma letra",
        "identity.error.phoneRequired": "O número de telefone é obrigatório",
        "identity.error.phoneInvalid": "Número de telefone inválido",
        "identity.error.codeRequired": "O código de verificação é obrigatório",
        "identity.error.codeInvalid": "Código de verificação inválido ou expirado",
        "identity.error.credentialsInvalid": "E-mail ou senha incorretos",
        "identity.error.accountSuspended": "Esta conta está suspensa. Contate um administrador.",
        "identity.error.network": "Erro de rede. Verifique sua conexão e tente novamente.",
        "identity.error.unknown": "Ocorreu um erro desconhecido",
        "identity.hint.emailRequired": "Precisamos verificar seu e-mail",
        "identity.hint.emailRequiredDescription":
            "Seu e-mail é usado para receber a verificação e recuperar a senha. Alguns métodos de login (como WeChat) não fornecem e-mail — você precisará adicioná-lo manualmente.",
        "identity.hint.codeSent": "Código de verificação enviado para {email}",
        "identity.hint.agreeToTerms": "Ao se cadastrar, você concorda com os Termos de Serviço e a Política de Privacidade",
    },
    "ru-RU": {
        "identity.title.signIn": "Войти",
        "identity.title.signUp": "Регистрация",
        "identity.subtitle.signIn": "Войдите, чтобы продолжить работу в академическом пространстве",
        "identity.subtitle.signUp": "Создайте аккаунт и начните свой академический путь",
        "identity.tab.signIn": "Войти",
        "identity.tab.signUp": "Регистрация",
        "identity.field.email": "Электронная почта",
        "identity.field.emailPlaceholder": "name@example.com",
        "identity.field.password": "Пароль",
        "identity.field.passwordPlaceholder": "Не менее 10 символов, с цифрой и буквой",
        "identity.field.phone": "Номер телефона",
        "identity.field.phonePlaceholder": "13800138000",
        "identity.field.code": "Код подтверждения",
        "identity.field.codePlaceholder": "6 цифр",
        "identity.field.displayName": "Отображаемое имя",
        "identity.field.displayNamePlaceholder": "Необязательно",
        "identity.action.signIn": "Войти",
        "identity.action.signUp": "Зарегистрироваться",
        "identity.action.sendCode": "Отправить код",
        "identity.action.resendCode": "Повторить через {seconds} с",
        "identity.action.wechat": "Войти через WeChat",
        "identity.action.google": "Войти через Google",
        "identity.action.github": "Войти через GitHub",
        "identity.action.switchToSignUp": "Нет аккаунта? Зарегистрируйтесь",
        "identity.action.switchToSignIn": "Уже есть аккаунт? Войдите",
        "identity.action.back": "Назад",
        "identity.divider.or": "или",
        "identity.state.sending": "Отправка…",
        "identity.state.verifying": "Проверка…",
        "identity.state.redirecting": "Перенаправление…",
        "identity.error.emailRequired": "Укажите электронную почту",
        "identity.error.emailInvalid": "Некорректный адрес электронной почты",
        "identity.error.emailTaken": "Этот адрес уже зарегистрирован",
        "identity.error.passwordRequired": "Укажите пароль",
        "identity.error.passwordTooShort": "Пароль должен содержать не менее 10 символов",
        "identity.error.passwordNeedsNumber": "Пароль должен содержать цифру",
        "identity.error.passwordNeedsLetter": "Пароль должен содержать букву",
        "identity.error.phoneRequired": "Укажите номер телефона",
        "identity.error.phoneInvalid": "Некорректный номер телефона",
        "identity.error.codeRequired": "Укажите код подтверждения",
        "identity.error.codeInvalid": "Код подтверждения недействителен или истёк",
        "identity.error.credentialsInvalid": "Неверная почта или пароль",
        "identity.error.accountSuspended": "Аккаунт заблокирован. Обратитесь к администратору.",
        "identity.error.network": "Ошибка сети. Проверьте подключение и повторите попытку.",
        "identity.error.unknown": "Произошла неизвестная ошибка",
        "identity.hint.emailRequired": "Нам нужно подтвердить вашу электронную почту",
        "identity.hint.emailRequiredDescription":
            "Почта используется для подтверждения и восстановления пароля. Некоторые способы входа (например, WeChat) не дают адрес почты — его нужно будет указать вручную.",
        "identity.hint.codeSent": "Код подтверждения отправлен на {email}",
        "identity.hint.agreeToTerms": "Регистрируясь, вы соглашаетесь с Условиями использования и Политикой конфиденциальности",
    },
    "ar-EG": {
        "identity.title.signIn": "تسجيل الدخول",
        "identity.title.signUp": "إنشاء حساب",
        "identity.subtitle.signIn": "سجّل الدخول لمتابعة استخدام مساحتك الأكاديمية",
        "identity.subtitle.signUp": "أنشئ حسابًا وابدأ رحلتك الأكاديمية",
        "identity.tab.signIn": "تسجيل الدخول",
        "identity.tab.signUp": "إنشاء حساب",
        "identity.field.email": "البريد الإلكتروني",
        "identity.field.emailPlaceholder": "name@example.com",
        "identity.field.password": "كلمة المرور",
        "identity.field.passwordPlaceholder": "10 أحرف على الأقل، مع رقم وحرف",
        "identity.field.phone": "رقم الهاتف",
        "identity.field.phonePlaceholder": "13800138000",
        "identity.field.code": "رمز التحقق",
        "identity.field.codePlaceholder": "6 أرقام",
        "identity.field.displayName": "الاسم الظاهر",
        "identity.field.displayNamePlaceholder": "اختياري",
        "identity.action.signIn": "تسجيل الدخول",
        "identity.action.signUp": "إنشاء حساب",
        "identity.action.sendCode": "إرسال الرمز",
        "identity.action.resendCode": "إعادة الإرسال خلال {seconds} ثانية",
        "identity.action.wechat": "تسجيل الدخول عبر WeChat",
        "identity.action.google": "تسجيل الدخول عبر Google",
        "identity.action.github": "تسجيل الدخول عبر GitHub",
        "identity.action.switchToSignUp": "ليس لديك حساب؟ أنشئ حسابًا",
        "identity.action.switchToSignIn": "لديك حساب بالفعل؟ سجّل الدخول",
        "identity.action.back": "رجوع",
        "identity.divider.or": "أو",
        "identity.state.sending": "جارٍ الإرسال…",
        "identity.state.verifying": "جارٍ التحقق…",
        "identity.state.redirecting": "جارٍ التحويل…",
        "identity.error.emailRequired": "البريد الإلكتروني مطلوب",
        "identity.error.emailInvalid": "صيغة البريد الإلكتروني غير صحيحة",
        "identity.error.emailTaken": "هذا البريد الإلكتروني مسجل بالفعل",
        "identity.error.passwordRequired": "كلمة المرور مطلوبة",
        "identity.error.passwordTooShort": "يجب أن تتكون كلمة المرور من 10 أحرف على الأقل",
        "identity.error.passwordNeedsNumber": "يجب أن تحتوي كلمة المرور على رقم",
        "identity.error.passwordNeedsLetter": "يجب أن تحتوي كلمة المرور على حرف",
        "identity.error.phoneRequired": "رقم الهاتف مطلوب",
        "identity.error.phoneInvalid": "صيغة رقم الهاتف غير صحيحة",
        "identity.error.codeRequired": "رمز التحقق مطلوب",
        "identity.error.codeInvalid": "رمز التحقق غير صالح أو منتهي الصلاحية",
        "identity.error.credentialsInvalid": "البريد الإلكتروني أو كلمة المرور غير صحيحة",
        "identity.error.accountSuspended": "هذا الحساب موقوف. يرجى التواصل مع المسؤول.",
        "identity.error.network": "خطأ في الشبكة. تحقق من اتصالك وحاول مرة أخرى.",
        "identity.error.unknown": "حدث خطأ غير معروف",
        "identity.hint.emailRequired": "نحتاج إلى التحقق من بريدك الإلكتروني",
        "identity.hint.emailRequiredDescription":
            "يُستخدم بريدك الإلكتروني لاستلام رسائل التحقق واستعادة كلمة المرور. بعض طرق الدخول (مثل WeChat) لا توفر بريدًا إلكترونيًا، لذا ستحتاج إلى إضافته يدويًا.",
        "identity.hint.codeSent": "تم إرسال رمز التحقق إلى {email}",
        "identity.hint.agreeToTerms": "بإنشاء حساب فأنت توافق على شروط الخدمة وسياسة الخصوصية",
    },
}

# 各语言的导出变量名与显示名
LOCALES = {
    "zh-TW": ("zhTW", "繁體中文"),
    "zh-HK": ("zhHK", "繁體中文（香港）"),
    "ja-JP": ("jaJP", "日本語"),
    "ko-KR": ("koKR", "한국어"),
    "fr-FR": ("frFR", "Français"),
    "de-DE": ("deDE", "Deutsch"),
    "es-ES": ("esES", "Español"),
    "pt-BR": ("ptBR", "Português (Brasil)"),
    "ru-RU": ("ruRU", "Русский"),
    "ar-EG": ("arEG", "العربية"),
}

# 从 en-US 提取 key 顺序（保证所有语言 key 顺序一致）
BASE_FILE = MESSAGES / "en-US.ts"
base_text = BASE_FILE.read_text(encoding="utf-8")

import re

# ⚠️ 缩进不敏感 —— Biome 可能把缩排成 tab 或空格。
#    用 `[ \t]*` 而不是固定的 `\t`，否则格式一变就匹配不到（静默生成空表）。
KEY_PATTERN = re.compile(r"^[ \t]*'([^']+)':\s*'((?:[^'\\]|\\.)*)'", re.MULTILINE)

base_entries = KEY_PATTERN.findall(base_text)
keys = [key for key, _ in base_entries]
base_values = dict(base_entries)
print(f"base keys: {len(keys)}")

if not keys:
    raise SystemExit("ERROR: no keys extracted from en-US.ts -- check the file format")

# ⚠️ 静默失败防护 —— 上一版因为正则写死 `\t`（Biome 改成空格后），
#    匹配不到任何 key，**生成了 10 个空表**而且不报错。
#    这类「跑成功了但结果是空的」必须在这里挡住。
if len(keys) < 40:
    raise SystemExit(
        f"ERROR: only {len(keys)} keys extracted from en-US.ts "
        f"(expected >= 40) -- the file format probably changed"
    )

if len(set(keys)) != len(keys):
    raise SystemExit("ERROR: duplicate keys found in en-US.ts")

# ⚠️ 每种语言都必须是 100% 覆盖 —— 少一条就报错，不留到测试才发现
for locale, (var_name, _label) in LOCALES.items():
    missing = [key for key in keys if key not in TRANSLATIONS[locale]]
    if missing:
        raise SystemExit(
            f"ERROR: {locale} is missing {len(missing)} keys: {missing[:5]}"
        )

for locale, (var_name, label) in LOCALES.items():
    table = TRANSLATIONS[locale]

    # ⚠️ 检查占位符一致性 —— 与 en-US 比对
    for key in keys:
        base_placeholders = set(re.findall(r"\{(\w+)\}", base_values.get(key, "")))
        target = table.get(key, "")
        target_placeholders = set(re.findall(r"\{(\w+)\}", target))
        if base_placeholders != target_placeholders:
            print(
                f"  [WARN] {locale} {key}: placeholders "
                f"{base_placeholders} != {target_placeholders}"
            )

    lines = [
        "/**",
        f" * 登录注册文案 —— {label}（L2）。",
        " *",
        " * ⚠️ key 集合与 en-US **完全一致**（由 generate.py 保证）。",
        " *    占位符也必须一致 —— `packages/ui` 的 findPlaceholderMismatches() 会校验。",
        " */",
        "",
        f"export const {var_name} = {{",
    ]

    for key in keys:
        value = table.get(key)
        if value is None:
            # ⚠️ 缺失 → 留空由回退链兜底（en-US）
            continue
        # 转义引号 —— 按 Biome 的偏好选引号风格
        quoted = quote(value)
        # ⚠️ 缩进必须与 conventions 一致（space × 2）——
        #    Biome 的 lint 规则用 space，formatter 默认用 tab；
        #    生成器写 tab 会让 lint 一直报格式错。
        #    详见 packages/conventions/typescript/biome.json 的 indentStyle/indentWidth。
        line = f"  '{key}': {quoted},"

        # ⚠️ 长行换行 —— Biome 的 formatter 会在超过 lineWidth 时把值挪到下一行。
        #    生成器不照做的话，每次跑完都要手动 biome check --write，
        #    「生成即干净」这个属性就没了。
        #    ⚠️ 用显示宽度算（CJK 占 2 列），不是 len()。
        if display_width(line) > MAX_LINE_WIDTH:
            # 值单独一行，缩进比 key 多一级（4 空格）
            lines.append(f"  '{key}':")
            lines.append(f"    {quoted},")
        else:
            lines.append(line)

    lines.append("} as const;")
    lines.append("")

    target_file = MESSAGES / f"{locale}.ts"
    # ⚠️ 必须显式 newline="\n" —— Windows 上 Python 默认写 CRLF，
    #    而 conventions 要求 LF。写 CRLF 会让 Biome 的 formatter 一直报差异。
    #    （这正是「生成器跑完还得手动 biome check --write」的根本原因。）
    with target_file.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines))
    print(f"  wrote {locale}.ts ({len(table)} entries)")

print("done")
