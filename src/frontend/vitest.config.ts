// # SPEC-004
import { defineConfig } from 'vitest/config';
export default defineConfig({test:{root:'../..',environment:'jsdom',include:['tests/frontend/*.test.ts']}});
