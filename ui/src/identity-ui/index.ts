/**
 * @scholarspace/identity-ui —— 登录注册前端组件。
 *
 * ⚠️ 本包是**可复用组件包**：
 *   · 不绑死后端地址与协议（API 由宿主注入）
 *   · 不绑定微信 SDK 的加载方式（由宿主注入）
 *   · 12 种界面语言，与 `@scholarspace/ui` 的 i18n 机制一致
 */

export { SignInForm, type SignInFormProps } from './components/SignInForm';
export { SignUpForm, type SignUpFormProps } from './components/SignUpForm';
export { WeChatQrCode, type WeChatQrCodeProps } from './components/WeChatQrCode';
export {
  IDENTITY_LOCALES,
  IDENTITY_MESSAGES,
} from './messages/index';
export {
  MIN_PASSWORD_LENGTH,
  type SignInFormValues,
  type SignInMethod,
  type ValidationResult,
  validateCode,
  validateEmail,
  validatePassword,
  validatePhone,
  validateSignInForm,
  validateSignUpForm,
} from './validation';
