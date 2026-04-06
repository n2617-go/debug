def get_defcon_repair_v2():
    """
    針對 DEFCON 消失問題：實施雙重模式掃描
    """
    # ... (前面的截圖流程維持 350, 15, 1100, 100)
    
    img_org = Image.open(io.BytesIO(screenshot_bytes)).convert('L')
    
    # --- 策略 A：原始高對比模式 (針對 紅底白字) ---
    img_a = ImageEnhance.Contrast(img_org).enhance(4.0)
    img_a = img_a.point(lambda x: 255 if x > 128 else 0, mode='1')
    raw_a = pytesseract.image_to_string(img_a, config='--psm 6')
    
    # --- 策略 B：極限反轉模式 (針對 您之前遇到的白底黑字) ---
    img_b = ImageOps.invert(img_org)
    img_b = ImageEnhance.Contrast(img_b).enhance(5.0)
    img_b = img_b.point(lambda x: 255 if x > 200 else 0, mode='1')
    raw_b = pytesseract.image_to_string(img_b, config='--psm 6')
    
    # 儲存策略 B 的影像供您檢查是否又變白底
    buf = io.BytesIO()
    img_b.convert("RGB").save(buf, format="PNG")
    debug_defcon_img = buf.getvalue()
    
    # 優先從 A 找，找不到再從 B 找
    raw_combined = raw_a + " " + raw_b
    lvl_match = re.search(r'(?:defcon|d\w+n|et)\s*[:|l|!|i]?\s*([1-5])', raw_combined, re.IGNORECASE)
    
    # ... (後續百分比 8x 放大流程維持不變)
