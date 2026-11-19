/**
 * 登录注册文案 —— 日本語（L2）。
 *
 * ⚠️ key 集合与 en-US **完全一致**（由 generate.py 保证）。
 *    占位符也必须一致 —— `packages/ui` 的 findPlaceholderMismatches() 会校验。
 */

export const jaJP = {
  'identity.title.signIn': 'ログイン',
  'identity.title.signUp': '新規登録',
  'identity.subtitle.signIn': 'ログインして学術ワークスペースを使い続けましょう',
  'identity.subtitle.signUp': 'アカウントを作成して学術の旅を始めましょう',
  'identity.tab.signIn': 'ログイン',
  'identity.tab.signUp': '新規登録',
  'identity.field.email': 'メールアドレス',
  'identity.field.emailPlaceholder': 'name@example.com',
  'identity.field.password': 'パスワード',
  'identity.field.passwordPlaceholder': '10 文字以上、数字と英字を含めてください',
  'identity.field.phone': '電話番号',
  'identity.field.phonePlaceholder': '13800138000',
  'identity.field.code': '確認コード',
  'identity.field.codePlaceholder': '6 桁の数字',
  'identity.field.displayName': '表示名',
  'identity.field.displayNamePlaceholder': '任意',
  'identity.action.signIn': 'ログイン',
  'identity.action.signUp': '登録',
  'identity.action.sendCode': '確認コードを送信',
  'identity.action.resendCode': '再送信（{seconds} 秒）',
  'identity.action.wechat': 'WeChat でログイン',
  'identity.action.google': 'Google でログイン',
  'identity.action.github': 'GitHub でログイン',
  'identity.action.switchToSignUp': 'アカウントがありませんか？新規登録',
  'identity.action.switchToSignIn': 'すでにアカウントをお持ちですか？ログイン',
  'identity.action.back': '戻る',
  'identity.divider.or': 'または',
  'identity.state.sending': '送信中…',
  'identity.state.verifying': '確認中…',
  'identity.state.redirecting': '転送中…',
  'identity.error.emailRequired': 'メールアドレスを入力してください',
  'identity.error.emailInvalid': 'メールアドレスの形式が正しくありません',
  'identity.error.emailTaken': 'このメールアドレスは既に登録されています',
  'identity.error.passwordRequired': 'パスワードを入力してください',
  'identity.error.passwordTooShort': 'パスワードは 10 文字以上必要です',
  'identity.error.passwordNeedsNumber': 'パスワードには数字が必要です',
  'identity.error.passwordNeedsLetter': 'パスワードには英字が必要です',
  'identity.error.phoneRequired': '電話番号を入力してください',
  'identity.error.phoneInvalid': '電話番号の形式が正しくありません',
  'identity.error.codeRequired': '確認コードを入力してください',
  'identity.error.codeInvalid': '確認コードが無効か、有効期限が切れています',
  'identity.error.credentialsInvalid': 'メールアドレスまたはパスワードが正しくありません',
  'identity.error.accountSuspended':
    'このアカウントは停止されています。管理者にお問い合わせください。',
  'identity.error.network': 'ネットワークエラーです。接続を確認して再試行してください。',
  'identity.error.unknown': '不明なエラーが発生しました',
  'identity.hint.emailRequired': 'メールアドレスの確認が必要です',
  'identity.hint.emailRequiredDescription':
    'メールアドレスは確認メールの送信とパスワード復旧に使用されます。WeChat など一部のログイン方法はメールアドレスを提供しないため、手動で追加する必要があります。',
  'identity.hint.codeSent': '確認コードを {email} に送信しました',
  'identity.hint.agreeToTerms':
    '登録により利用規約とプライバシーポリシーに同意したものとみなされます',
} as const;
