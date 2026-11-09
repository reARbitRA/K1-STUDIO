import { expect, test } from '@playwright/test';
async function test_ac_9_desktop_layout({ page }: {page: import('@playwright/test').Page}) {
  await page.goto('/'); await page.getByLabel('Demo session').click();
  await expect(page.getByLabel('Track arrangement').getByText('TEXTURE 04',{exact:true})).toBeVisible();
  for (const size of [{width:1440,height:900},{width:1920,height:1080}]) {
    await page.setViewportSize(size); await page.goto('/');
    await expect(page.getByRole('heading',{name:'Surgical regions'})).toBeVisible();
    await expect(page.getByRole('heading',{name:'Analog mastering'})).toBeVisible();
    expect(await page.evaluate(()=>document.documentElement.scrollHeight<=innerHeight)).toBeTruthy();
    await expect(page.getByRole('button',{name:'Export WAV',exact:true})).toBeVisible();
    await expect(page.getByLabel('Track arrangement').getByText('TEXTURE 04',{exact:true})).toBeVisible();
    expect(await page.locator('.track-row').last().evaluate(e=>e.getBoundingClientRect().bottom<=e.parentElement!.getBoundingClientRect().bottom)).toBeTruthy();
    await page.waitForFunction(()=>[...document.querySelectorAll('.wave')].every(e=>e.querySelector('div')?.shadowRoot?.querySelector('canvas')));
    await page.screenshot({path:`../../.verification/studio-${size.width}.png`});
  }
}
async function test_ac_10_transport_regions({page}:{page:import('@playwright/test').Page}) {
  await page.goto('/'); await page.getByLabel('Demo session').click();
  await expect(page.getByLabel('Track arrangement').getByText('SYNTH 01',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Play',exact:true}).click();
  await expect(page.getByRole('button',{name:'Pause',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Pause',exact:true}).click();
  await page.getByRole('button',{name:'Hard mute',exact:true}).click();
  await expect(page.getByText('HARD_MUTE',{exact:true}).first()).toBeVisible();
  await page.getByRole('button',{name:'Undo',exact:true}).click();
  await page.getByRole('button',{name:'Redo',exact:true}).click();
}
async function test_ac_11_accessibility_errors({page}:{page:import('@playwright/test').Page}) {
  await page.goto('/'); await page.keyboard.press('Tab');
  expect(await page.evaluate(()=>document.activeElement?.tagName)).not.toBe('BODY');
  await page.getByLabel('Demo session').click();
  await page.route('**/api/v1/project/render',route=>route.fulfill({status:503,
    contentType:'application/json',body:JSON.stringify({error:{code:'processing_failed',message:'Try again',field:null}})}));
  await page.getByRole('button',{name:'Export WAV',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('Try again');
  await expect(page.getByLabel('Track arrangement').getByText('SYNTH 01',{exact:true})).toBeVisible();
}
test('test_ac_9_desktop_layout',test_ac_9_desktop_layout);
test('test_ac_10_transport_regions',test_ac_10_transport_regions);
test('test_ac_11_accessibility_errors',test_ac_11_accessibility_errors);
