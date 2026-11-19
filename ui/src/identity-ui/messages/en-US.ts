/**
 * 登录注册文案 —— 英文（L1，100% 覆盖）。
 *
 * ⚠️ key 集合与占位符必须与 zh-CN **完全一致**。
 */

export const enUS = {
  // ── Entry ──────────────────────────────────────────
  'identity.title.signIn': 'Sign in',
  'identity.title.signUp': 'Sign up',
  'identity.subtitle.signIn': 'Sign in to continue with your academic workspace',
  'identity.subtitle.signUp': 'Create an account to start your academic journey',
  'identity.tab.signIn': 'Sign in',
  'identity.tab.signUp': 'Sign up',

  // ── Fields ─────────────────────────────────────────
  'identity.field.email': 'Email',
  'identity.field.emailPlaceholder': 'name@example.com',
  'identity.field.password': 'Password',
  'identity.field.passwordPlaceholder': 'At least 10 characters, with a number and a letter',
  'identity.field.phone': 'Phone number',
  'identity.field.phonePlaceholder': '13800138000',
  'identity.field.code': 'Verification code',
  'identity.field.codePlaceholder': '6 digits',
  'identity.field.displayName': 'Display name',
  'identity.field.displayNamePlaceholder': 'Optional',

  // ── Actions ────────────────────────────────────────
  'identity.action.signIn': 'Sign in',
  'identity.action.signUp': 'Sign up',
  'identity.action.sendCode': 'Send code',
  'identity.action.resendCode': 'Resend in {seconds}s',
  'identity.action.wechat': 'Sign in with WeChat',
  'identity.action.google': 'Sign in with Google',
  'identity.action.github': 'Sign in with GitHub',
  'identity.action.switchToSignUp': 'No account? Sign up',
  'identity.action.switchToSignIn': 'Have an account? Sign in',
  'identity.action.back': 'Back',

  // ── Divider ────────────────────────────────────────
  'identity.divider.or': 'or',

  // ── States ─────────────────────────────────────────
  'identity.state.sending': 'Sending…',
  'identity.state.verifying': 'Verifying…',
  'identity.state.redirecting': 'Redirecting…',

  // ── Errors ─────────────────────────────────────────
  'identity.error.emailRequired': 'Email is required',
  'identity.error.emailInvalid': 'Invalid email address',
  'identity.error.emailTaken': 'This email is already registered',
  'identity.error.passwordRequired': 'Password is required',
  'identity.error.passwordTooShort': 'Password must be at least 10 characters',
  'identity.error.passwordNeedsNumber': 'Password must contain a number',
  'identity.error.passwordNeedsLetter': 'Password must contain a letter',
  'identity.error.phoneRequired': 'Phone number is required',
  'identity.error.phoneInvalid': 'Invalid phone number',
  'identity.error.codeRequired': 'Verification code is required',
  'identity.error.codeInvalid': 'Invalid or expired verification code',
  'identity.error.credentialsInvalid': 'Incorrect email or password',
  'identity.error.accountSuspended': 'This account is suspended. Please contact an administrator.',
  'identity.error.network': 'Network error. Check your connection and try again.',
  'identity.error.unknown': 'Something went wrong',

  // ── Hints ──────────────────────────────────────────
  'identity.hint.emailRequired': 'We need to verify your email',
  'identity.hint.emailRequiredDescription':
    'Your email is used for verification and password recovery. Some sign-in methods (such as WeChat) do not provide an email, so you will need to add one manually.',
  'identity.hint.codeSent': 'Verification code sent to {email}',
  'identity.hint.agreeToTerms':
    'By signing up you agree to the Terms of Service and Privacy Policy',
} as const;
