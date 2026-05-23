import { test, expect } from '@playwright/test';

test.describe('TechSpar 登录功能测试', () => {
  
  test('完整登录流程测试', async ({ page }) => {
    const screenshots = [];
    
    // 步骤 1: 打开首页
    console.log('步骤 1: 打开首页...');
    await page.goto('http://localhost');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'test-results/01-homepage.png' });
    console.log('首页已截图');

    // 步骤 2: 查找并点击登录按钮
    console.log('步骤 2: 查找登录按钮...');
    
    // 尝试多种选择器来找到登录按钮
    const loginButton = page.getByText('登录').first();
    await expect(loginButton).toBeVisible({ timeout: 5000 });
    await page.screenshot({ path: 'test-results/02-before-login-click.png' });
    await loginButton.click();
    console.log('已点击登录按钮');

    // 步骤 3: 等待登录页面加载
    console.log('步骤 3: 等待登录页面...');
    await page.waitForURL('**/login**', { timeout: 5000 }).catch(() => {
      console.log('URL 未变化，可能已在登录页面');
    });
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'test-results/03-login-page.png' });
    console.log('登录页面已截图');

    // 步骤 4: 填写表单
    console.log('步骤 4: 填写登录表单...');
    await page.fill('input[type="email"]', 'admin@techspar.local');
    await page.fill('input[type="password"]', 'admin123');
    await page.screenshot({ path: 'test-results/04-form-filled.png' });
    console.log('表单已填写');

    // 步骤 5: 点击登录按钮
    console.log('步骤 5: 点击登录...');
    await page.click('button[type="submit"]');
    
    // 步骤 6: 等待响应
    console.log('步骤 6: 等待登录响应...');
    await page.waitForTimeout(3000);
    await page.screenshot({ path: 'test-results/05-after-login.png' });

    // 步骤 7: 检查结果
    console.log('步骤 7: 检查登录结果...');
    
    const currentUrl = page.url();
    console.log('当前 URL:', currentUrl);
    
    // 检查是否有错误提示
    const errorElement = page.locator('div').filter({ hasText: /操作失败|Invalid|错误/ }).first();
    const hasError = await errorElement.isVisible().catch(() => false);
    
    if (hasError) {
      const errorText = await errorElement.textContent();
      console.log('登录失败，错误信息:', errorText);
      await page.screenshot({ path: 'test-results/06-error-state.png' });
    } else if (currentUrl.includes('login')) {
      console.log('仍在登录页面，可能需要更多时间');
      await page.screenshot({ path: 'test-results/06-still-on-login.png' });
    } else {
      console.log('登录成功! 当前 URL:', currentUrl);
      await page.screenshot({ path: 'test-results/06-success-state.png' });
    }

    // 步骤 8: 收集网络请求信息
    console.log('\n=== 网络请求日志 ===');
    console.log('最终 URL:', page.url());
    
    // 检查 localStorage 中的 token
    const token = await page.evaluate(() => localStorage.getItem('token'));
    console.log('Token 存在:', !!token);
    if (token) {
      console.log('Token 前 50 字符:', token.substring(0, 50) + '...');
    }

    // 最终截图
    await page.screenshot({ path: 'test-results/07-final-state.png' });
    console.log('\n测试完成，截图已保存到 test-results/ 目录');
  });

  test('直接访问登录页面测试', async ({ page }) => {
    console.log('\n=== 直接访问登录页面测试 ===');
    
    await page.goto('http://localhost/login');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'test-results/direct-login-page.png' });
    
    // 填写表单
    await page.fill('input[type="email"]', 'admin@techspar.local');
    await page.fill('input[type="password"]', 'admin123');
    
    // 监听网络请求
    const [response] = await Promise.all([
      page.waitForResponse(response => response.url().includes('/api/auth/login')),
      page.click('button[type="submit"]')
    ]);
    
    console.log('API 响应状态:', response.status());
    console.log('API 响应内容:', await response.text());
    
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'test-results/direct-login-result.png' });
  });

});
