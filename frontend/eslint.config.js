/**
 * ESLint 9 Flat Config
 * 创建时间: 2025-06-20
 * 作者: hongchuwudi
 * 描述: 前端 ESLint 配置 — TypeScript + React + React Hooks + Vite
 *
 * 注意: ESLint 不原生支持 .ts 配置文件，因此使用 .js 并通过 JSDoc 获得类型检查。
 */

import js from "@eslint/js";
import tseslint from "typescript-eslint";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import globals from "globals";

export default tseslint.config(
  // ----- 全局忽略 -----
  {
    ignores: [
      "dist",
      "node_modules",
      "scripts",
    ],
  },

  // ----- 基础规则（所有文件） -----
  js.configs.recommended,

  // ----- TypeScript 规则（TS/TSX 文件） -----
  ...tseslint.configs.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      parserOptions: {
        project: "./tsconfig.json",
      },
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    rules: {
      // TypeScript 严格度调整
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/no-unused-vars": ["warn", {
        argsIgnorePattern: "^_",
        varsIgnorePattern: "^_",
      }],
      "@typescript-eslint/consistent-type-imports": ["error", {
        prefer: "type-imports",
      }],
    },
  },

  // ----- React 规则（组件文件） -----
  {
    files: ["**/*.{ts,tsx}"],
    plugins: {
      "react-hooks": reactHooks,
      "react-refresh": reactRefresh,
    },
    rules: {
      // React Hooks 推荐规则
      ...reactHooks.configs.recommended.rules,

      // setState 在 useEffect 中调用 — 项目中这是标准数据获取模式，
      // 所有页面/组件都这样用，实际运行无问题，禁用此规则
      "react-hooks/set-state-in-effect": "off",

      // React Refresh — 只允许文件导出组件
      "react-refresh/only-export-components": ["warn", {
        allowConstantExport: true,
      }],
    },
  },

  // ----- Context 文件豁免：Provider + Hook 必须同文件导出 -----
  {
    files: ["**/context/*.tsx"],
    rules: {
      "react-refresh/only-export-components": "off",
    },
  },

  // ----- 声明文件豁免 -----
  {
    files: ["**/*.d.ts"],
    rules: {
      "react-refresh/only-export-components": "off",
    },
  },
);
