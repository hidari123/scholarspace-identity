# @scholarspace/identity-ui

scholarspace 登录注册前端组件 —— 邮箱 / 短信 / 微信 / Google / GitHub。

> **可复用组件包**：不绑死后端地址与协议，不绑定微信 SDK 的加载方式。
> 两者都由宿主注入。

---

## 特点

| 能力               | 说明                                                                                               |
| ------------------ | -------------------------------------------------------------------------------------------------- |
| 12 种界面语言      | zh-CN / en-US / zh-TW / zh-HK / ja-JP / ko-KR / fr-FR / de-DE / es-ES / pt-BR / ru-RU / ar-EG(RTL) |
| 100% 覆盖          | 所有语言 key 集合完全一致 —— 由 `generate.py` 保证，测试校验                                       |
| 邮箱必绑           | 微信注册没邮箱 → 强制补邮箱并验证（`pendingEmail` 流程）                                           |
| 校验规则与后端一致 | 密码强度、邮箱、手机号规则与 `identity-core` 对齐                                                  |

---

## 用法

### 1. 合并文案

```tsx
import { ScholarSpaceProvider } from '@scholarspace/ui';
import { IDENTITY_MESSAGES } from '@scholarspace/identity-ui';

<ScholarSpaceProvider locale="zh-CN" namespaces={{ identity: IDENTITY_MESSAGES }}>
  <App />
</ScholarSpaceProvider>;
```

### 2. 登录表单

```tsx
import { SignInForm } from '@scholarspace/identity-ui';

<SignInForm
  onSubmit={async (method, values) => {
    const res = await api.signIn(method, values);
    return res.ok ? undefined : 'identity.error.credentialsInvalid';
  }}
  onThirdParty={(method) => redirectToOAuth(method)}
  onSwitchToSignUp={() => navigate('/signup')}
/>;
```

### 3. 注册表单（含补邮箱流程）

```tsx
<SignUpForm
  onSubmit={async (method, values) => {
    const res = await api.signUp(method, values);
    // ⚠️ pendingEmail —— 第三方注册没邮箱时后端会返回这个
    //    组件会自动切到「补邮箱」步骤
    if (res.pendingEmail) return { pendingEmail: true };
    return res.ok ? undefined : { code: 'identity.error.emailTaken' };
  }}
  onSendEmailCode={async (email) => {
    await api.sendEmailCode(email);
  }}
/>;
```

### 4. 微信扫码

```tsx
import { WeChatQrCode } from '@scholarspace/identity-ui';

<WeChatQrCode
  onFetchAuthorize={async () => {
    // ⚠️ state 必须服务端生成并签名 —— 前端不能自己造
    const res = await api.getWeChatAuthorize();
    return { authorizeUrl: res.url, state: res.state };
  }}
  loadSdk={loadWeChatSdk}
  onSuccess={(code, state) => saveStateForCallback(state)}
/>;
```

---

## 设计约束

### 只从 `@scholarspace/ui` 导入组件

```ts
// ✅ 正确
import { Button, Form, Input } from '@scholarspace/ui';

// ❌ 禁止 —— G7 护栏会拦
import { Button } from 'antd';
```

`packages/ui` 再导出了常用 AntD 组件，所以业务代码**不需要**直接依赖 antd。

### 校验逻辑是纯函数

放在 `validation.ts` 而不是组件里 —— 组件难测，纯函数好测。
规则必须与后端一致，前端只是**即时反馈**，不能替代后端校验。

---

## 命令

```bash
pnpm run verify      # typecheck + lint + test + build
pnpm run test        # 48 个测试
```

---

## 与后端的对应关系

| 前端                 | 后端                                                |
| -------------------- | --------------------------------------------------- |
| `validateEmail`      | `identity_core.entities.EmailAddress`               |
| `validatePhone`      | `identity_core.entities.PhoneNumber`                |
| `validatePassword`   | `identity_providers.password.EmailPasswordProvider` |
| `pendingEmail` 流程  | `identity_core.policy.EmailRequiredPolicy`          |
| `state` 由服务端签发 | `identity_providers.oauth2.state.OAuth2StateCodec`  |

---

## 维护文案

文案有 12 份，语言多容易漏。**用生成器维护**：

```bash
python src/identity-ui/messages/generate.py
```

生成器做两件事：

1. 复制 en-US 的 key 集合与占位符 → 保证结构一致
2. 把每条文案替换成对应语言的译文

翻译表在 `generate.py` 的 `TRANSLATIONS` 里。**改文案时改那里，不要手改生成出来的文件** —— 下次生成会被覆盖。

---

## 已知限制

- **微信扫码依赖官方 JS SDK** —— 本包只做容器，实际二维码由 SDK 渲染（自己生成会丢会话绑定）
- **短信验证码的倒计时**目前是静态显示，未接真实倒计时逻辑
