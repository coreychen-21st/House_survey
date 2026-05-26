from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # Open houseprice.tw
    page.goto("https://www.houseprice.tw/", timeout=30000, wait_until="networkidle")
    page.wait_for_timeout(3000)
    
    title = page.title()
    print(f"Title: {title}")
    
    # Get all links
    links = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a[href]')).map(a => ({
            text: a.innerText.trim().substring(0, 40),
            href: a.href
        })).filter(l => l.href && !l.href.startsWith('javascript'));
    }""")
    print(f"\nTotal links: {len(links)}")
    for l in links[:30]:
        print(f"  {l['text'][:30]:30s} -> {l['href'][:80]}")
    
    # Try clicking "買屋"
    buy_link = page.query_selector("a:has-text('買屋'), a:has-text('買房')")
    if buy_link:
        print(f"\nFound buy link: {buy_link.inner_text()}")
        buy_link.click()
        page.wait_for_timeout(3000)
        print(f"After click URL: {page.url}")
    else:
        print("\nNo buy link found, trying direct navigation")
    
    # Try the buy list page
    page.goto("https://www.houseprice.tw/buy.html", timeout=15000)
    page.wait_for_timeout(3000)
    print(f"Buy page URL: {page.url}")
    print(f"Buy page title: {page.title()}")
    
    # Get all possible URLs  
    buy_links = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a[href]')).map(a => a.href).filter(h => h.includes('buy') || h.includes('list') || h.includes('search')).slice(0, 30);
    }""")
    print(f"\nBuy/list links: {buy_links}")
    
    # Try search API
    search_inputs = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('input, select, form')).map(el => ({
            tag: el.tagName,
            name: el.name,
            id: el.id,
            placeholder: el.placeholder,
            action: el.action
        }));
    }""")
    print(f"\nForms/inputs: {search_inputs}")
    
    browser.close()
