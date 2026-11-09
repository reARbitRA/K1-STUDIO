// # SPEC-004
import { defineConfig } from 'vite';
export default defineConfig({server:{host:'0.0.0.0',allowedHosts:['.e2b.app','localhost'],
  proxy:{'/api':{target:'http://127.0.0.1:8000'},'/ws':{target:'ws://127.0.0.1:8000',ws:true}}}});
