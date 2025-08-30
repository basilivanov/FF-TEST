const { chromium } = require('playwright');

async function testUI() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  // Авторизация
  await page.setExtraHTTPHeaders({
    'Authorization': 'Basic ' + Buffer.from('ops:ops123').toString('base64')
  });
  
  console.log('Тестирую Dashboard...');
  await page.goto('https://etl-tst.chococraft.ru/admin/');
  await page.waitForSelector('.space-y-6', { timeout: 5000 });
  console.log('✅ Dashboard загружается');
  
  console.log('Тестирую Agents...');
  await page.goto('https://etl-tst.chococraft.ru/admin/agents');
  await page.waitForSelector('.space-y-6', { timeout: 5000 });
  console.log('✅ Agents загружается');
  
  console.log('Тестирую Budget...');
  await page.goto('https://etl-tst.chococraft.ru/admin/budget');
  await page.waitForSelector('.space-y-6', { timeout: 5000 });
  console.log('✅ Budget загружается');
  
  console.log('Тестирую Logs...');
  await page.goto('https://etl-tst.chococraft.ru/admin/logs');
  await page.waitForSelector('.space-y-6', { timeout: 5000 });
  console.log('✅ Logs загружается');
  
  await browser.close();
  console.log('🎉 Все страницы работают быстро!');
}

testUI().catch(console.error);