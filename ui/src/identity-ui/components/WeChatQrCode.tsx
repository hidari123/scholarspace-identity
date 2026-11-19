/**
 * 微信扫码登录 —— 二维码容器。
 *
 * ⚠️ 设计：**不自己生成二维码**。
 *
 *   微信开放平台要求用官方的 `WxLogin` JS SDK 渲染二维码 ——
 *   自己生成二维码会丢掉微信的会话绑定，扫码后回调拿不到 code。
 *
 *   所以本组件只负责：
 *     ① 向后端要授权 URL 与 state
 *     ② 加载微信官方 SDK
 *     ③ 在容器 div 上初始化
 *     ④ 轮询/接收回调
 *
 *   宿主负责注入 SDK 加载与回调处理 —— 这样本包不绑死微信 SDK 的加载方式。
 */

import { Alert, Spin, useTranslate } from '@scholarspace/ui';
import { useCallback, useEffect, useRef, useState } from 'react';

export interface WeChatQrCodeProps {
  /**
   * 获取微信授权信息。
   *
   * ⚠️ 返回的 `authorizeUrl` 与 `state` 来自**后端** ——
   * state 必须由服务端生成并签名（防 CSRF），前端不能自己造。
   */
  onFetchAuthorize: () => Promise<{ authorizeUrl: string; state: string }>;
  /**
   * 加载微信官方 SDK。
   *
   * ⚠️ 由宿主注入 —— 不同环境（主站 / 独立站 / 移动端）加载方式不同。
   */
  loadSdk: () => Promise<void>;
  /**
   * 扫码成功回调。
   *
   * ⚠️ 微信会把浏览器重定向到 redirect_uri ——
   *    所以这里通常是「页面跳转」，而不是函数内直接 resolve。
   */
  onSuccess?: (code: string, state: string) => void;
  /** 加载中。 */
  loading?: boolean;
}

/** 微信 SDK 初始化所需的全局对象。 */
interface WxLoginConstructor {
  new (config: {
    appid: string;
    scope: string;
    redirect_uri: string;
    state: string;
    href: string;
    onload?: () => void;
    onerror?: (error: unknown) => void;
  }): {
    destroy: () => void;
  };
}

declare global {
  interface Window {
    WxLogin?: WxLoginConstructor;
  }
}

export function WeChatQrCode({
  onFetchAuthorize,
  loadSdk,
  onSuccess,
  loading = false,
}: WeChatQrCodeProps) {
  const t = useTranslate();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const instanceRef = useRef<{ destroy: () => void } | null>(null);
  const [errorKey, setErrorKey] = useState<string | undefined>(undefined);
  const [ready, setReady] = useState(false);

  const initQrCode = useCallback(async () => {
    setErrorKey(undefined);

    try {
      // ① 先拿授权信息 —— state 必须服务端生成
      const { authorizeUrl, state } = await onFetchAuthorize();

      // ② 加载微信官方 SDK
      await loadSdk();

      if (!window.WxLogin) {
        setErrorKey('identity.error.unknown');
        return;
      }

      // ③ 解析出 SDK 需要的参数
      const params = new URLSearchParams(authorizeUrl.split('?')[1] ?? '');
      const appid = params.get('appid') ?? '';
      const redirectUri = params.get('redirect_uri') ?? '';
      const scope = params.get('scope') ?? 'snsapi_login';

      // ④ 在容器上初始化
      if (!containerRef.current) return;

      instanceRef.current?.destroy();
      instanceRef.current = new window.WxLogin({
        appid,
        scope,
        redirect_uri: redirectUri,
        state,
        href: '',
        onload: () => setReady(true),
        onerror: () => setErrorKey('identity.error.unknown'),
      });

      // ⚠️ 微信 SDK 没有提供 code 回调 ——
      //    扫码成功后浏览器会跳到 redirect_uri，由那边解析 code + state。
      //    所以这里只把 state 留在 context 里供宿主使用。
      onSuccess?.('', state);
    } catch {
      setErrorKey('identity.error.network');
    }
  }, [onFetchAuthorize, loadSdk, onSuccess]);

  useEffect(() => {
    void initQrCode();

    return () => {
      instanceRef.current?.destroy();
      instanceRef.current = null;
    };
  }, [initQrCode]);

  return (
    <div style={{ position: 'relative', minHeight: 200, textAlign: 'center' }}>
      {errorKey ? <Alert type="error" message={t(errorKey)} showIcon /> : null}

      {!ready && !errorKey ? (
        <div style={{ padding: 80 }}>
          <Spin size="large" />
        </div>
      ) : null}

      {/* ⚠️ 微信 SDK 会往这个 div 里塞 iframe —— 不能用 React 接管它的子节点 */}
      <div ref={containerRef} />

      {loading ? (
        <div style={{ position: 'absolute', inset: 0, background: 'rgba(255,255,255,0.7)' }}>
          <Spin style={{ marginTop: 80 }} />
        </div>
      ) : null}
    </div>
  );
}
