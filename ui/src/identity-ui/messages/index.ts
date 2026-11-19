/**
 * 文案表 —— 12 种界面语言。
 *
 * ⚠️ 与 `packages/ui` 的 `BUILTIN_MESSAGES` 结构一致：
 *   locale → (key → 文案)
 *
 * 宿主用法（合并进 ScholarSpaceProvider 的 namespaces）：
 *   <ScholarSpaceProvider namespaces={{ identity: IDENTITY_MESSAGES }}>
 *     <LoginForm />
 *   </ScholarSpaceProvider>
 */

import type { LocaleTable } from '@scholarspace/ui';

import { arEG } from './ar-EG';
import { deDE } from './de-DE';
import { enUS } from './en-US';
import { esES } from './es-ES';
import { frFR } from './fr-FR';
import { jaJP } from './ja-JP';
import { koKR } from './ko-KR';
import { ptBR } from './pt-BR';
import { ruRU } from './ru-RU';
import { zhCN } from './zh-CN';
import { zhHK } from './zh-HK';
import { zhTW } from './zh-TW';

/** 登录注册的 12 种语言文案表。 */
export const IDENTITY_MESSAGES: LocaleTable = {
  'zh-CN': zhCN,
  'en-US': enUS,
  'zh-TW': zhTW,
  'zh-HK': zhHK,
  'ja-JP': jaJP,
  'ko-KR': koKR,
  'fr-FR': frFR,
  'de-DE': deDE,
  'es-ES': esES,
  'pt-BR': ptBR,
  'ru-RU': ruRU,
  'ar-EG': arEG,
};

/** 本包提供的语言代码。 */
export const IDENTITY_LOCALES = Object.keys(IDENTITY_MESSAGES);
