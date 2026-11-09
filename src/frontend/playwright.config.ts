// # SPEC-004
import { defineConfig } from '@playwright/test';
import chromium from '@sparticuz/chromium';
import { mkdirSync, readFileSync } from 'node:fs';
import { brotliDecompressSync } from 'node:zlib';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
// Test-only native libraries bundled by the pinned npm package; no network download.
const libs=resolve('../../.verification/browser-libs');mkdirSync(libs,{recursive:true});
execFileSync('tar',['-xf','-','-C',libs],{input:brotliDecompressSync(readFileSync(new URL('../../bin/al2023.tar.br',import.meta.resolve('@sparticuz/chromium'))))});
export default defineConfig({testDir:'../../tests/frontend/e2e',timeout:60000,workers:1,
  use:{baseURL:'http://localhost:5173',headless:true,launchOptions:{
    executablePath:await chromium.executablePath(),
    env:{...process.env,LD_LIBRARY_PATH:resolve(libs,'lib')},
    args:chromium.args.filter(arg=>!['--single-process','--disable-web-security','--allow-running-insecure-content'].includes(arg))}},
  webServer:[{command:'PYTHONPATH=src K1_WORKSPACE=.verification/e2e-workspace .venv/bin/uvicorn k1_studio.app.main:app --host 0.0.0.0 --port 8000',cwd:resolve('../..'),url:'http://127.0.0.1:8000/openapi.json',reuseExistingServer:!process.env.CI},{command:'npm --prefix src/frontend run dev -- --port 5173',cwd:resolve('../..'),url:'http://localhost:5173',reuseExistingServer:!process.env.CI}],
  reporter:'list'});
