import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir:'./distribution-tests', workers:1, fullyParallel:false, timeout:90000,
  expect:{timeout:15000}, reporter:[['list'],['json',{outputFile:'test-results-distribution/report.json'}]],
  outputDir:'./test-results-distribution',
  use:{baseURL:'http://127.0.0.1:18188',channel:process.env.CI ? undefined : 'chrome',
    viewport:{width:1280,height:900},screenshot:'only-on-failure',trace:'retain-on-failure'},
});
