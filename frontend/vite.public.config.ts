import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({plugins:[react()],publicDir:false,
 build:{outDir:'dist-public',manifest:true,rollupOptions:{input:{dashboard:'dashboard/index.html',preparedness:'preparedness/index.html',operator:'operator/index.html'}}}});
