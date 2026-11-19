/**
 * 12 种语言的文案一致性测试。
 *
 * ⚠️ 这组测试是**多语言体系的护栏** ——
 *    漏翻译、占位符不一致、key 拼错，都会在这里被抓住。
 */

import { findPlaceholderMismatches, measureCoverage } from '@scholarspace/ui';
import { describe, expect, it } from 'vitest';

import { IDENTITY_LOCALES, IDENTITY_MESSAGES } from '../src/identity-ui/messages';

describe('语言表结构', () => {
  it('有 12 种语言', () => {
    expect(IDENTITY_LOCALES.length).toBe(12);
  });

  it('包含约定的 12 种语言', () => {
    const expected = [
      'zh-CN',
      'en-US',
      'zh-TW',
      'zh-HK',
      'ja-JP',
      'ko-KR',
      'fr-FR',
      'de-DE',
      'es-ES',
      'pt-BR',
      'ru-RU',
      'ar-EG',
    ];

    for (const locale of expected) {
      expect(IDENTITY_LOCALES).toContain(locale);
    }
  });

  it('每种语言都有文案表', () => {
    for (const locale of IDENTITY_LOCALES) {
      const table = IDENTITY_MESSAGES[locale];
      expect(table, `缺少 ${locale}`).toBeDefined();
      expect(Object.keys(table ?? {}).length).toBeGreaterThan(0);
    }
  });

  it('包含 RTL 语言（ar-EG）', () => {
    // ⚠️ RTL 是架构预留的验证实现 —— 必须有
    expect(IDENTITY_LOCALES).toContain('ar-EG');
  });
});

describe('key 集合一致性', () => {
  it('⚠️ 所有语言的 key 集合与 en-US 完全一致', () => {
    const baseKeys = Object.keys(IDENTITY_MESSAGES['en-US'] ?? {}).sort();

    for (const locale of IDENTITY_LOCALES) {
      const keys = Object.keys(IDENTITY_MESSAGES[locale] ?? {}).sort();
      expect(keys, `${locale} 的 key 集合与 en-US 不一致`).toEqual(baseKeys);
    }
  });

  it('en-US 是基准（有足够多的 key）', () => {
    const count = Object.keys(IDENTITY_MESSAGES['en-US'] ?? {}).length;
    expect(count).toBeGreaterThanOrEqual(40);
  });

  it('每种语言的覆盖率都是 100%', () => {
    // ⚠️ 本包要求所有语言 100% 覆盖 ——
    //    生成器保证了 key 集合一致，翻译由 generate.py 维护。
    for (const locale of IDENTITY_LOCALES) {
      const coverage = measureCoverage(locale, IDENTITY_MESSAGES);
      expect(coverage.ratio, `${locale} 覆盖率不足`).toBe(1);
    }
  });
});

describe('占位符一致性', () => {
  it('⚠️ 跨语言占位符完全一致', () => {
    const mismatches = findPlaceholderMismatches(IDENTITY_MESSAGES);
    expect(mismatches).toEqual([]);
  });

  it('重发倒计时有 seconds 占位符', () => {
    const value = IDENTITY_MESSAGES['en-US']?.['identity.action.resendCode'];
    expect(value).toContain('{seconds}');
  });

  it('验证码提示有 email 占位符', () => {
    const value = IDENTITY_MESSAGES['en-US']?.['identity.hint.codeSent'];
    expect(value).toContain('{email}');
  });
});

describe('key 命名规范', () => {
  it('全部 key 以 identity. 开头', () => {
    // ⚠️ 规范：<domain>.<section>.<element>[.<state>]
    for (const locale of IDENTITY_LOCALES) {
      for (const key of Object.keys(IDENTITY_MESSAGES[locale] ?? {})) {
        expect(key, `${locale} 的 key "${key}" 不合规`).toMatch(
          /^identity\.[a-z][a-zA-Z]*\.[a-z][a-zA-Z]*(\.[a-z][a-zA-Z]*)?$/,
        );
      }
    }
  });

  it('错误 key 都在 identity.error. 命名空间下', () => {
    for (const key of Object.keys(IDENTITY_MESSAGES['en-US'] ?? {})) {
      if (key.includes('.error.')) {
        expect(key.startsWith('identity.error.')).toBe(true);
      }
    }
  });
});

describe('文案质量', () => {
  it('没有空文案', () => {
    for (const locale of IDENTITY_LOCALES) {
      for (const [key, value] of Object.entries(IDENTITY_MESSAGES[locale] ?? {})) {
        expect(value?.trim(), `${locale} 的 "${key}" 是空的`).not.toBe('');
      }
    }
  });

  it('中文文案不含英文占位符残留', () => {
    // ⚠️ 中文里不该出现 "{count} 条" 这种没翻译的片段
    for (const key of Object.keys(IDENTITY_MESSAGES['zh-CN'] ?? {})) {
      const value = IDENTITY_MESSAGES['zh-CN']?.[key] ?? '';
      // 占位符本身允许，但不该有 "{xxx}" 之外的英文句子
      expect(value.replace(/\{[a-zA-Z]+\}/g, ''), `zh-CN 的 "${key}" 有未翻译内容`).not.toMatch(
        /\b(the|and|with|your|Please)\b/i,
      );
    }
  });
});
