const { chromium } = require('playwright');
const { pathToFileURL } = require('url');
const path = require('path');
const assert = require('assert/strict');
(async () => {
  const browser = await chromium.launch({ channel: 'msedge', headless: true });
  try {
    const page = await browser.newPage();
    await page.route(/^https?:/, route => route.abort());
    await page.goto(pathToFileURL(path.resolve('index.html')).href);
    for (const width of [320,390,768,1024,1150,1160,1280,1366,1440,1920]) {
      await page.setViewportSize({ width, height: 900 });
      const layout = await page.evaluate(() => {
        const nav = document.querySelector('.nav');
        const links = document.querySelector('.nav-links');
        const actions = document.querySelector('.header-actions').getBoundingClientRect();
        const bounds = links.getBoundingClientRect();
        return {
          overflow: nav.scrollWidth > nav.clientWidth + 1,
          overlap: innerWidth > 1150 && bounds.right > actions.left,
          wrapped: [...links.querySelectorAll('a')].some(a => {
            const range = document.createRange(); range.selectNodeContents(a);
            return range.getClientRects().length > 1;
          })
        };
      });
      assert.deepEqual(layout, {overflow:false,overlap:false,wrapped:false}, String(width));
      await page.locator('.contact-toggle').click();
      assert.equal(await page.locator('#header-contact-panel').isVisible(), true);
      assert.equal(await page.locator('#header-contact-panel .js-phone').getAttribute('href'), 'tel:+380630607088');
      await page.keyboard.press('Escape');
      assert.equal(await page.locator('#header-contact-panel').isVisible(), false);
      if (width <= 1150) {
        await page.locator('.menu-toggle').click();
        assert.equal(await page.locator('.menu-toggle').getAttribute('aria-expanded'), 'true');
        await page.locator('.menu-toggle').click();
      }
      console.log(`PASS header ${width}px`);
    }
    await page.setViewportSize({width:1366,height:900});
    await page.mouse.move(0,400);
    await page.locator('.contact-toggle').hover();
    assert.equal(await page.locator('#header-contact-panel').isVisible(),true);
    console.log('PASS hover and contact links');
    const touch = await browser.newPage({viewport:{width:390,height:844},hasTouch:true,isMobile:true});
    await touch.route(/^https?:/, route=>route.abort());
    await touch.goto(pathToFileURL(path.resolve('index.html')).href);
    await touch.locator('.contact-toggle').tap();
    assert.equal(await touch.locator('#header-contact-panel').isVisible(),true);
    await touch.locator('.contact-toggle').tap();
    assert.equal(await touch.locator('#header-contact-panel').isVisible(),false);
    console.log('PASS touch open/close');
  } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});
