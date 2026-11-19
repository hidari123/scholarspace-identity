/**
 * 校验规则测试。
 *
 * ⚠️ 这些规则**必须与后端一致** ——
 *    `identity-core` 的 EmailAddress / PhoneNumber 值对象，
 *    `identity-providers` 的密码强度检查。
 *    前端只是即时反馈，后端才是权威。
 */

import { describe, expect, it } from 'vitest';

import {
  MIN_PASSWORD_LENGTH,
  validateCode,
  validateEmail,
  validatePassword,
  validatePhone,
  validateSignInForm,
  validateSignUpForm,
} from '../src/identity-ui/validation';

describe('validateEmail', () => {
  it('接受合法邮箱', () => {
    expect(validateEmail('user@example.com').valid).toBe(true);
  });

  it('接受 + 标签邮箱', () => {
    // ⚠️ 过严的正则会误杀 —— 后端也接受
    expect(validateEmail('user+tag@example.com').valid).toBe(true);
  });

  it('接受国际化域名', () => {
    expect(validateEmail('用户@例子.中国').valid).toBe(true);
  });

  it('拒绝空邮箱', () => {
    const result = validateEmail('');
    expect(result.valid).toBe(false);
    expect(result.errorKey).toBe('identity.error.emailRequired');
  });

  it('拒绝纯空白', () => {
    expect(validateEmail('   ').valid).toBe(false);
  });

  it('拒绝缺 @ 的', () => {
    expect(validateEmail('userexample.com').valid).toBe(false);
  });

  it('拒绝缺域名的', () => {
    expect(validateEmail('user@').valid).toBe(false);
  });

  it('拒绝含空格的', () => {
    expect(validateEmail('user name@example.com').valid).toBe(false);
  });
});

describe('validatePhone', () => {
  it('接受合法手机号', () => {
    expect(validatePhone('13800138000').valid).toBe(true);
  });

  it('接受 199 开头的号', () => {
    expect(validatePhone('19912345678').valid).toBe(true);
  });

  it('拒绝空', () => {
    expect(validatePhone('').errorKey).toBe('identity.error.phoneRequired');
  });

  it('拒绝 12 位', () => {
    expect(validatePhone('138001380001').valid).toBe(false);
  });

  it('拒绝 10 位', () => {
    expect(validatePhone('1380013800').valid).toBe(false);
  });

  it('拒绝不以 1 开头的', () => {
    expect(validatePhone('23800138000').valid).toBe(false);
  });

  it('拒绝第二位为 0 的', () => {
    expect(validatePhone('10800138000').valid).toBe(false);
  });
});

describe('validatePassword', () => {
  it('接受强密码', () => {
    expect(validatePassword('Str0ngPassword!').valid).toBe(true);
  });

  it('拒绝空', () => {
    expect(validatePassword('').errorKey).toBe('identity.error.passwordRequired');
  });

  it('拒绝太短', () => {
    const result = validatePassword('Ab1');
    expect(result.valid).toBe(false);
    expect(result.errorKey).toBe('identity.error.passwordTooShort');
  });

  it('拒绝无数字', () => {
    expect(validatePassword('OnlyLettersHere').errorKey).toBe('identity.error.passwordNeedsNumber');
  });

  it('拒绝无字母', () => {
    expect(validatePassword('1234567890').errorKey).toBe('identity.error.passwordNeedsLetter');
  });

  it('⚠️ 只报第一个错（按优先级）', () => {
    // 同时太短 + 无数字 → 只报「太短」
    const result = validatePassword('abc');
    expect(result.errorKey).toBe('identity.error.passwordTooShort');
  });

  it('最小长度常量与后端一致', () => {
    expect(MIN_PASSWORD_LENGTH).toBe(10);
  });
});

describe('validateCode', () => {
  it('接受非空验证码', () => {
    expect(validateCode('123456').valid).toBe(true);
  });

  it('拒绝空', () => {
    expect(validateCode('').errorKey).toBe('identity.error.codeRequired');
  });
});

describe('validateSignInForm', () => {
  it('邮箱登录要邮箱与密码都合法', () => {
    expect(
      validateSignInForm('email', { email: 'a@b.com', password: 'Str0ngPassword!' }).valid,
    ).toBe(true);
  });

  it('邮箱缺失时报邮箱错', () => {
    expect(validateSignInForm('email', { password: 'Str0ngPassword!' }).errorKey).toBe(
      'identity.error.emailRequired',
    );
  });

  it('密码缺失时报密码错', () => {
    expect(validateSignInForm('email', { email: 'a@b.com' }).errorKey).toBe(
      'identity.error.passwordRequired',
    );
  });

  it('短信登录要手机号与验证码', () => {
    expect(validateSignInForm('sms', { phone: '13800138000', code: '123456' }).valid).toBe(true);
  });

  it('短信登录手机号非法', () => {
    expect(validateSignInForm('sms', { phone: '123', code: '123456' }).valid).toBe(false);
  });

  it('⚠️ 第三方登录不校验表单', () => {
    // 微信/Google/GitHub 由 provider 处理 —— 前端不拦
    expect(validateSignInForm('wechat', {}).valid).toBe(true);
    expect(validateSignInForm('google', {}).valid).toBe(true);
    expect(validateSignInForm('github', {}).valid).toBe(true);
  });
});

describe('validateSignUpForm', () => {
  it('确认密码一致才通过', () => {
    expect(
      validateSignUpForm('email', {
        email: 'a@b.com',
        password: 'Str0ngPassword!',
        confirmPassword: 'Str0ngPassword!',
      }).valid,
    ).toBe(true);
  });

  it('确认密码不一致时报错', () => {
    const result = validateSignUpForm('email', {
      email: 'a@b.com',
      password: 'Str0ngPassword!',
      confirmPassword: 'Different123',
    });

    expect(result.valid).toBe(false);
    expect(result.errorKey).toBe('identity.error.credentialsInvalid');
  });

  it('基础校验失败时优先报基础错', () => {
    const result = validateSignUpForm('email', {
      email: 'bad',
      password: 'Str0ngPassword!',
      confirmPassword: 'Str0ngPassword!',
    });

    expect(result.errorKey).toBe('identity.error.emailInvalid');
  });

  it('第三方注册不校验确认密码', () => {
    expect(validateSignUpForm('wechat', {}).valid).toBe(true);
  });
});
