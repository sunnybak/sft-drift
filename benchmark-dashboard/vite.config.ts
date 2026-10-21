import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath } from 'node:url';
import { loadReports } from './server/report-loader.ts';
const directories = [
  fileURLToPath(new URL('./reports/', import.meta.url)),
  fileURLToPath(new URL('../belief-transfer/data/results/ethical_pilot/ethics_gpu_benchmark_dashboard_v1/reports/', import.meta.url)),
];
export default defineConfig({
  plugins: [react(), {
    name: 'local-benchmark-reports',
    configureServer(server) {
      server.middlewares.use((req,res,next)=>{
        if(req.url?.split('?')[0]!=='/reports.json')return next();
        if(req.method!=='GET'){res.statusCode=405;res.end('Method not allowed');return;}
        res.setHeader('Content-Type','application/json');res.setHeader('Cache-Control','no-store');
        res.end(JSON.stringify(loadReports(directories)));
      });
    },
    generateBundle(){this.emitFile({type:'asset',fileName:'reports.json',source:JSON.stringify(loadReports(directories))});},
  }],
  server:{port:5174,strictPort:true},
});
