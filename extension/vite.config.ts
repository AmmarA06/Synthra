import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';
import zipPack from 'vite-plugin-zip-pack';
import { copyFileSync } from 'fs';

export default defineConfig({
  plugins: [
    react(),
    zipPack({
      outDir: 'dist-zip',
      outFileName: 'synthra-extension.zip'
    }),
    // Custom plugin to copy manifest.json
    {
      name: 'copy-manifest',
      writeBundle() {
        copyFileSync('manifest.json', 'dist/manifest.json');
      }
    }
  ],
  root: '.',
  build: {
    outDir: 'dist',
    rollupOptions: {
      input: {
        sidebar: resolve(__dirname, 'sidebar.html'),
        background: resolve(__dirname, 'background.js'),
        content: resolve(__dirname, 'content.js')
      },
      output: {
        entryFileNames: (chunkInfo) => {
          if (chunkInfo.name === 'background' || chunkInfo.name === 'content') {
            return '[name].js';
          }
          return 'assets/[name]-[hash].js';
        },
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name!.split('.');
          const ext = info[info.length - 1];
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
            return `icons/[name].[ext]`;
          }
          return `assets/[name]-[hash].[ext]`;
        }
      }
    },
    copyPublicDir: true
  },
  publicDir: 'public'
});
