/**
 * 注册表单 —— 支持邮箱密码、短信、第三方三种方式。
 *
 * ⚠️ **关键场景：微信注册没有邮箱**。
 *
 *   微信开放平台的 `sns/userinfo` 不返回邮箱 ——
 *   所以微信注册的用户必须**补一个邮箱并验证**。
 *
 *   本组件用一个 `requiresEmail` 状态表达这个流程：
 *     ① 第三方注册 → 后端返回 pending（要求补邮箱）
 *     ② 前端切到「补邮箱」步骤
 *     ③ 用户填邮箱 → 收验证码 → 验证 → 完成
 *
 *   这正是「邮箱必绑」Policy 在前端的表现。
 */

import {
  Alert,
  Button,
  Form,
  Input,
  Space,
  Steps,
  Typography,
  useTranslate,
} from '@scholarspace/ui';
import { useCallback, useState } from 'react';

import {
  type SignInFormValues,
  type SignInMethod,
  validateEmail,
  validateSignUpForm,
} from '../validation';

export interface SignUpFormProps {
  /**
   * 提交回调。
   *
   * ⚠️ 返回值语义：
   *   · `undefined` —— 成功
   *   · `{ code: string }` —— 失败（code 是 i18n key）
   *   · `{ pendingEmail: true }` —— 需要补邮箱（第三方注册场景）
   */
  onSubmit?: (
    method: SignInMethod,
    values: SignInFormValues,
  ) => Promise<{ code?: string; pendingEmail?: boolean } | undefined>;
  /** 切换到登录。 */
  onSwitchToSignIn?: () => void;
  /** 第三方注册回调。 */
  onThirdParty?: (method: 'wechat' | 'google' | 'github') => void;
  /** 发送邮箱验证码。 */
  onSendEmailCode?: (email: string) => Promise<void>;
  /** 初始方式。 */
  defaultMethod?: SignInMethod;
  /** 加载中。 */
  loading?: boolean;
}

/** 注册步骤。 */
type Step = 'credentials' | 'bind-email';

export function SignUpForm({
  onSubmit,
  onSwitchToSignIn,
  onThirdParty,
  onSendEmailCode,
  defaultMethod = 'email',
  loading = false,
}: SignUpFormProps) {
  const t = useTranslate();
  // ⚠️ 注册页不做「方式切换」—— 注册方式由入口决定（邮箱注册页 / 微信注册页）。
  //    所以 method 只读，不提供 setter。
  const [method] = useState<SignInMethod>(defaultMethod);
  const [step, setStep] = useState<Step>('credentials');
  const [errorKey, setErrorKey] = useState<string | undefined>(undefined);
  const [codeSent, setCodeSent] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm<SignInFormValues & { confirmPassword?: string }>();

  const handleSubmit = useCallback(
    async (values: SignInFormValues & { confirmPassword?: string }) => {
      const validation = validateSignUpForm(method, values);
      if (!validation.valid) {
        setErrorKey(validation.errorKey);
        return;
      }

      setErrorKey(undefined);
      setSubmitting(true);

      try {
        const result = await onSubmit?.(method, values);

        if (result?.code) {
          setErrorKey(result.code);
          return;
        }

        // ⚠️ 后端说「需要补邮箱」→ 切到补邮箱步骤
        if (result?.pendingEmail) {
          setStep('bind-email');
        }
      } catch {
        setErrorKey('identity.error.network');
      } finally {
        setSubmitting(false);
      }
    },
    [method, onSubmit],
  );

  const handleSendCode = useCallback(async () => {
    const email = form.getFieldValue('email');
    const validation = validateEmail(email ?? '');
    if (!validation.valid) {
      setErrorKey(validation.errorKey);
      return;
    }

    try {
      await onSendEmailCode?.(email);
      setCodeSent(true);
    } catch {
      setErrorKey('identity.error.network');
    }
  }, [form, onSendEmailCode]);

  const busy = loading || submitting;

  return (
    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
      {step === 'bind-email' ? (
        <Steps
          current={1}
          size="small"
          items={[{ title: t('identity.tab.signUp') }, { title: t('identity.hint.emailRequired') }]}
        />
      ) : null}

      <Alert
        type="info"
        showIcon
        message={t('identity.hint.emailRequired')}
        description={t('identity.hint.emailRequiredDescription')}
      />

      {errorKey ? <Alert type="error" message={t(errorKey)} showIcon /> : null}

      <Form<SignInFormValues & { confirmPassword?: string }>
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        requiredMark={false}
      >
        {step === 'bind-email' ? (
          <>
            <Form.Item
              name="email"
              label={t('identity.field.email')}
              rules={[{ required: true, message: t('identity.error.emailRequired') }]}
            >
              <Input placeholder={t('identity.field.emailPlaceholder')} />
            </Form.Item>

            <Form.Item name="code" label={t('identity.field.code')}>
              <Space.Compact style={{ width: '100%' }}>
                <Input placeholder={t('identity.field.codePlaceholder')} />
                <Button onClick={handleSendCode} disabled={codeSent}>
                  {codeSent
                    ? t('identity.action.resendCode', { seconds: 60 })
                    : t('identity.action.sendCode')}
                </Button>
              </Space.Compact>
            </Form.Item>
          </>
        ) : (
          <>
            {method === 'email' ? (
              <>
                <Form.Item
                  name="email"
                  label={t('identity.field.email')}
                  rules={[{ required: true, message: t('identity.error.emailRequired') }]}
                >
                  <Input placeholder={t('identity.field.emailPlaceholder')} autoComplete="email" />
                </Form.Item>

                <Form.Item
                  name="password"
                  label={t('identity.field.password')}
                  rules={[{ required: true, message: t('identity.error.passwordRequired') }]}
                >
                  <Input.Password
                    placeholder={t('identity.field.passwordPlaceholder')}
                    autoComplete="new-password"
                  />
                </Form.Item>

                <Form.Item
                  name="confirmPassword"
                  label={t('identity.field.password')}
                  dependencies={['password']}
                  rules={[
                    ({ getFieldValue }) => ({
                      validator(_rule: unknown, value: string | undefined) {
                        if (!value || getFieldValue('password') === value) return Promise.resolve();
                        return Promise.reject(new Error(t('identity.error.credentialsInvalid')));
                      },
                    }),
                  ]}
                >
                  <Input.Password autoComplete="new-password" />
                </Form.Item>
              </>
            ) : null}

            <Form.Item
              name="displayName"
              label={t('identity.field.displayName')}
              rules={[{ required: false }]}
            >
              <Input placeholder={t('identity.field.displayNamePlaceholder')} />
            </Form.Item>
          </>
        )}

        <Form.Item>
          <Button type="primary" htmlType="submit" block loading={busy}>
            {step === 'bind-email' ? t('identity.action.sendCode') : t('identity.action.signUp')}
          </Button>
        </Form.Item>
      </Form>

      {step === 'credentials' ? (
        <Space direction="vertical" style={{ width: '100%' }}>
          <Button block onClick={() => onThirdParty?.('wechat')}>
            {t('identity.action.wechat')}
          </Button>
          <Button block onClick={() => onThirdParty?.('google')}>
            {t('identity.action.google')}
          </Button>
          <Button block onClick={() => onThirdParty?.('github')}>
            {t('identity.action.github')}
          </Button>
        </Space>
      ) : null}

      {onSwitchToSignIn ? (
        <Button type="link" block onClick={onSwitchToSignIn}>
          {t('identity.action.switchToSignIn')}
        </Button>
      ) : null}

      <Typography.Text type="secondary" style={{ fontSize: 12 }}>
        {t('identity.hint.agreeToTerms')}
      </Typography.Text>
    </Space>
  );
}
