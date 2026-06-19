# 09 工程化

**状态：★ 刚配置完成**

## 知识点

- [ ] TypeScript 严格模式（`noUnusedLocals`、`noUnusedParameters`）
- [ ] ESLint 9 Flat Config — 代码规范检查
- [ ] Prettier — 代码格式化（你还没配）
- [ ] Playwright — E2E 测试
- [ ] GitHub Actions — CI 流水线
- [ ] Vite — 构建工具
- [ ] 环境变量管理
- [ ] pre-commit hooks（husky + lint-staged）

## 项目中的配置

- `eslint.config.js` — 刚配的，零报错
- `playwright.config.ts` — 刚写的，14 个测试全部通过
- `.github/workflows/ci.yml` — 后端 pytest + 前端 lint/tsc
- `vite.config.ts` — Tailwind v4 插件 + API 代理
- `tsconfig.json` — `noUnusedLocals: true`、`noUnusedParameters: true`

## 还缺什么

- [ ] Prettier — 格式化统一
- [ ] husky — 提交前自动 lint
- [ ] 前端单元测试（Vitest）
- [ ] 后端集成测试

## 常见面试题

- CI/CD 流水线每步做什么？
- ESLint 和 Prettier 的分工？
- 如何保证团队所有人的代码风格一致？
