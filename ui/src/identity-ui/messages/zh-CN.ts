/**
 * 登录注册文案 —— 简体中文（L1，100% 覆盖）。
 *
 * key 规范：<domain>.<section>.<element>[.<state>]
 * 规范来源：packages/conventions/i18n/key-patterns.json
 *
 * ⚠️ 所有语言的 key 集合必须**完全一致** ——
 *    占位符也要一致（`{count}` 在每种语言都要有）。
 *    `packages/ui` 的 `findPlaceholderMismatches()` 会校验。
 */

export const zhCN = {
  // ── 入口 ────────────────────────────────────────────
  'identity.title.signIn': '登录',
  'identity.title.signUp': '注册',
  'identity.subtitle.signIn': '登录以继续使用学术工作空间',
  'identity.subtitle.signUp': '创建账号，开始你的学术旅程',
  'identity.tab.signIn': '登录',
  'identity.tab.signUp': '注册',

  // ── 表单 ────────────────────────────────────────────
  'identity.field.email': '邮箱',
  'identity.field.emailPlaceholder': 'name@example.com',
  'identity.field.password': '密码',
  'identity.field.passwordPlaceholder': '至少 10 位，含数字与字母',
  'identity.field.phone': '手机号',
  'identity.field.phonePlaceholder': '13800138000',
  'identity.field.code': '验证码',
  'identity.field.codePlaceholder': '6 位数字',
  'identity.field.displayName': '昵称',
  'identity.field.displayNamePlaceholder': '选填',

  // ── 动作 ────────────────────────────────────────────
  'identity.action.signIn': '登录',
  'identity.action.signUp': '注册',
  'identity.action.sendCode': '发送验证码',
  'identity.action.resendCode': '重新发送（{seconds} 秒）',
  'identity.action.wechat': '微信扫码登录',
  'identity.action.google': '使用 Google 登录',
  'identity.action.github': '使用 GitHub 登录',
  'identity.action.switchToSignUp': '没有账号？去注册',
  'identity.action.switchToSignIn': '已有账号？去登录',
  'identity.action.back': '返回',

  // ── 第三方登录分隔 ──────────────────────────────────
  'identity.divider.or': '或',

  // ── 状态 ────────────────────────────────────────────
  'identity.state.sending': '发送中…',
  'identity.state.verifying': '验证中…',
  'identity.state.redirecting': '正在跳转…',

  // ── 错误 ────────────────────────────────────────────
  'identity.error.emailRequired': '请输入邮箱',
  'identity.error.emailInvalid': '邮箱格式不正确',
  'identity.error.emailTaken': '该邮箱已被注册',
  'identity.error.passwordRequired': '请输入密码',
  'identity.error.passwordTooShort': '密码至少 10 位',
  'identity.error.passwordNeedsNumber': '密码需包含数字',
  'identity.error.passwordNeedsLetter': '密码需包含字母',
  'identity.error.phoneRequired': '请输入手机号',
  'identity.error.phoneInvalid': '手机号格式不正确',
  'identity.error.codeRequired': '请输入验证码',
  'identity.error.codeInvalid': '验证码无效或已过期',
  'identity.error.credentialsInvalid': '邮箱或密码错误',
  'identity.error.accountSuspended': '账号已被停用，请联系管理员',
  'identity.error.network': '网络异常，请检查连接后重试',
  'identity.error.unknown': '发生未知错误',

  // ── 提示 ────────────────────────────────────────────
  'identity.hint.emailRequired': '我们需要验证邮箱',
  'identity.hint.emailRequiredDescription':
    '邮箱用于接收验证邮件与找回密码。部分登录方式（如微信）不提供邮箱，需要手动补充。',
  'identity.hint.codeSent': '验证码已发送至 {email}',
  'identity.hint.agreeToTerms': '注册即表示同意服务条款与隐私政策',
} as const;
