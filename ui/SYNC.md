# 规范同步说明

本目录的 `tsconfig.base.json` / `biome.base.json` 是从主仓 **复制**而来。

⚠️ 子仓 CI 独立 checkout，没有主仓在场，相对路径 extends 会**静默失效**（biome 尤其危险）。

本仓的 `tsconfig.json` 应指向本地副本：

```json
{
  "extends": "./tsconfig.base.json"
}
```

```json
{
  "extends": ["./biome.base.json"]
}
```

更新方式：

```bash
npx @scholarspace/cli sync --kind typescript
```

⚠️ 复制后请勿手改 —— 下次同步会覆盖。
