// SPEC-004: repository-wide frontend tooling, not runtime code.
import tseslint from 'typescript-eslint';
export default tseslint.config({ignores:['**/dist/**','**/node_modules/**']},...tseslint.configs.recommended);
