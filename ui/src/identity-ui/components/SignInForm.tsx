/**
 * 登录表单 —— 邮箱密码 / 短信 / 第三方三种方式。
 *
 * ⚠️ 设计原则：
 *   · **组件不含业务逻辑** —— 校验规则在 `validation.ts`（纯函数，可测）
 *   · **API 调用由宿主注入** —— 本包是「可复用组件」，不该绑死后端
 *   · **文案从 i18n 来** —— 用 `useTranslate()`，不硬编码
 */

import { Alert, Button, Divider, Form, Input, Space, Tabs, useTranslate } from '@scholarspace/ui';
import { useCallback, useState } from 'react';

import { type SignInFormValues, type SignInMethod, validateSignInForm } from '../validation';

export interface SignInFormProps {
  /**
   * 提交回调。
   *
   * ⚠️ 由宿主注入 —— 本包不绑死后端地址与协议。
   * 返回值：成功返回 undefined，失败返回错误码（i18n key）。
   */
  onSubmit?: (method: SignInMethod, values: SignInFormValues) => Promise<string | undefined>;
  /** 切换到注册。 */
  onSwitchToSignUp?: () => void;
  /** 第三方登录回调（method → 跳转或弹窗）。 */
  onThirdParty?: (method: 'wechat' | 'google' | 'github') => void;
  /** 初始方式。 */
  defaultMethod?: SignInMethod;
  /** 加载中。 */
  loading?: boolean;
}

export function SignInForm({
  onSubmit,
  onSwitchToSignUp,
  onThirdParty,
  defaultMethod = 'email',
  loading = false,
}: SignInFormProps) {
  const t = useTranslate();
  const [method, setMethod] = useState<SignInMethod>(defaultMethod);
  const [errorKey, setErrorKey] = useState<string | undefined>(undefined);
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm<SignInFormValues>();

  const handleSubmit = useCallback(
    async (values: SignInFormValues) => {
      // ① 前端校验 —— 即时反馈
      const validation = validateSignInForm(method, values);
      if (!validation.valid) {
        setErrorKey(validation.errorKey);
        return;
      }

      setErrorKey(undefined);
      setSubmitting(true);

      try {
        // ② 交给宿主 —— 本包不关心后端细节
        const failure = await onSubmit?.(method, values);
        if (failure) setErrorKey(failure);
      } catch {
        // ⚠️ 不记 error —— 生产环境不该把原始异常挂到用户界面上，
        //    统一给一个可操作的提示，具体原因交给日志/监控。
        setErrorKey('identity.error.network');
      } finally {
        setSubmitting(false);
      }
    },
    [method, onSubmit],
  );

  const busy = loading || submitting;

  return (
    <Form<SignInFormValues>
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
      requiredMark={false}
    >
      <Tabs
        activeKey={method === 'email' ? 'email' : 'sms'}
        onChange={(key) => {
          setMethod(key as SignInMethod);
          setErrorKey(undefined);
        }}
        items={[
          { key: 'email', label: t('identity.tab.signIn') },
          { key: 'sms', label: t('identity.field.phone') },
        ]}
      />

      {errorKey ? <Alert type="error" message={t(errorKey)} showIcon /> : null}

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
              autoComplete="current-password"
            />
          </Form.Item>
        </>
      ) : (
        <>
          <Form.Item
            name="phone"
            label={t('identity.field.phone')}
            rules={[{ required: true, message: t('identity.error.phoneRequired') }]}
          >
            <Input placeholder={t('identity.field.phonePlaceholder')} autoComplete="tel" />
          </Form.Item>

          <Form.Item name="code" label={t('identity.field.code')}>
            <Space.Compact style={{ width: '100%' }}>
              <Input placeholder={t('identity.field.codePlaceholder')} />
              <Button>{t('identity.action.sendCode')}</Button>
            </Space.Compact>
          </Form.Item>
        </>
      )}

      <Form.Item>
        <Button type="primary" htmlType="submit" block loading={busy}>
          {t('identity.action.signIn')}
        </Button>
      </Form.Item>

      <Divider plain>{t('identity.divider.or')}</Divider>

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

      {onSwitchToSignUp ? (
        <Button type="link" block onClick={onSwitchToSignUp} style={{ marginTop: 16 }}>
          {t('identity.action.switchToSignUp')}
        </Button>
      ) : null}
    </Form>
  );
}
