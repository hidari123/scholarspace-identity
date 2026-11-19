/**
 * 表单校验 —— 纯函数，无 React 依赖。
 *
 * ⚠️ **为什么单独抽出来**：
 *   校验规则是业务逻辑，放进组件里就没法单独测。
 *   纯函数 + 独立测试 = 规则可验证。
 *
 * ⚠️ **规则与后端一致**：
 *   `identity-core` 的 `EmailAddress` / `PhoneNumber` 值对象与
 *   `identity-providers` 的密码强度检查是同一套规则。
 *   前端校验只是为了**即时反馈**，不能替代后端校验。
 */

/** 校验结果。 */
export interface ValidationResult {
  /** 是否通过。 */
  valid: boolean;
  /** 失败时的 i18n key（`identity.error.*`）。 */
  errorKey?: string;
}

/** 邮箱格式正则 —— 与后端 `identity_core.entities` 的规则一致。 */
const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

/** 中国大陆手机号 —— 与后端一致。 */
const PHONE_PATTERN = /^1[3-9]\d{9}$/;

/** 密码最小长度 —— 与后端 `identity-providers` 一致。 */
export const MIN_PASSWORD_LENGTH = 10;

/** 校验邮箱。 */
export function validateEmail(email: string): ValidationResult {
  const trimmed = email.trim();
  if (!trimmed) return { valid: false, errorKey: 'identity.error.emailRequired' };
  if (!EMAIL_PATTERN.test(trimmed)) {
    return { valid: false, errorKey: 'identity.error.emailInvalid' };
  }
  return { valid: true };
}

/** 校验手机号。 */
export function validatePhone(phone: string): ValidationResult {
  const trimmed = phone.trim();
  if (!trimmed) return { valid: false, errorKey: 'identity.error.phoneRequired' };
  if (!PHONE_PATTERN.test(trimmed)) {
    return { valid: false, errorKey: 'identity.error.phoneInvalid' };
  }
  return { valid: true };
}

/**
 * 校验密码强度。
 *
 * ⚠️ 规则与后端 `EmailPasswordProvider._validate_strength` 一致：
 *   ≥10 位 + 至少一个数字 + 至少一个字母
 *
 * ⚠️ **按优先级只报一个错** —— 同时报「太短」和「缺数字」会让用户不知道先改哪个。
 */
export function validatePassword(password: string): ValidationResult {
  if (!password) return { valid: false, errorKey: 'identity.error.passwordRequired' };
  if (password.length < MIN_PASSWORD_LENGTH) {
    return { valid: false, errorKey: 'identity.error.passwordTooShort' };
  }
  if (!/\d/.test(password)) {
    return { valid: false, errorKey: 'identity.error.passwordNeedsNumber' };
  }
  if (!/[a-zA-Z]/.test(password)) {
    return { valid: false, errorKey: 'identity.error.passwordNeedsLetter' };
  }
  return { valid: true };
}

/** 校验验证码。 */
export function validateCode(code: string): ValidationResult {
  const trimmed = code.trim();
  if (!trimmed) return { valid: false, errorKey: 'identity.error.codeRequired' };
  return { valid: true };
}

/** 登录方式。 */
export type SignInMethod = 'email' | 'wechat' | 'google' | 'github' | 'sms';

/** 表单值。 */
export interface SignInFormValues {
  email?: string;
  password?: string;
  phone?: string;
  code?: string;
  displayName?: string;
}

/**
 * 校验整个登录表单。
 *
 * ⚠️ **按方式分别校验** —— 邮箱登录要邮箱+密码，
 *   短信登录要手机号+验证码，第三方登录什么都不用填。
 *
 * @param method 登录方式
 * @param values 表单值
 */
export function validateSignInForm(
  method: SignInMethod,
  values: SignInFormValues,
): ValidationResult {
  if (method === 'email') {
    const email = validateEmail(values.email ?? '');
    if (!email.valid) return email;

    return validatePassword(values.password ?? '');
  }

  if (method === 'sms') {
    const phone = validatePhone(values.phone ?? '');
    if (!phone.valid) return phone;

    return validateCode(values.code ?? '');
  }

  // 第三方登录 —— 前端不校验，交给 provider
  return { valid: true };
}

/**
 * 校验注册表单。
 *
 * ⚠️ 注册比登录多一项：确认密码。
 */
export function validateSignUpForm(
  method: SignInMethod,
  values: SignInFormValues & { confirmPassword?: string },
): ValidationResult {
  const base = validateSignInForm(method, values);
  if (!base.valid) return base;

  if (method === 'email') {
    if (values.confirmPassword !== values.password) {
      // ⚠️ 没有专门的 key —— 复用密码错误 key 避免文案膨胀
      return { valid: false, errorKey: 'identity.error.credentialsInvalid' };
    }
  }

  return { valid: true };
}
