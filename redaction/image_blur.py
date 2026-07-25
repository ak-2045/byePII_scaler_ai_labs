import logging
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np

logger = logging.getLogger("byepii")
_cv2 = None

def _get_cv2():
    global _cv2
    if _cv2 is None:
        try:
            import cv2
            _cv2 = cv2
        except ImportError:
            logger.warning("opencv-python-headless not installed; image blurring disabled.")
    return _cv2

IMAGE_REDACT_DIR = Path(__file__).parent.parent / "image_redact"
MATCH_THRESHOLD = 0.45
DIRECT_MATCH_THRESHOLD = 0.38
SCALES = [0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0]
MAX_TMPL_DIM = 400
BLUR_KERNEL = (51, 51)
COMPARE_SIZE = (128, 128)

def _resize_to_max(img: np.ndarray, max_dim: int):
    cv2 = _get_cv2()
    h, w = img.shape[:2]
    if max(h, w) <= max_dim:
        return img
    scale = max_dim / max(h, w)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    return cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

def _load_templates() -> List[Tuple[str, np.ndarray]]:
    cv2 = _get_cv2()
    if cv2 is None:
        return []
    templates = []
    if not IMAGE_REDACT_DIR.exists():
        logger.warning(f"image_redact dir not found: {IMAGE_REDACT_DIR}")
        return templates
    for img_path in sorted(IMAGE_REDACT_DIR.iterdir()):
        if img_path.suffix.lower() not in (".png", ".jpg", ".jpeg", ".bmp"):
            continue
        tmpl = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
        if tmpl is None:
            logger.warning(f"Could not load template: {img_path}")
            continue
        tmpl = _resize_to_max(tmpl, MAX_TMPL_DIM)
        templates.append((img_path.name, tmpl))
        logger.info(f"Loaded template: {img_path.name} ({tmpl.shape[1]}×{tmpl.shape[0]}px after resize)")
    logger.info(f"Loaded {len(templates)} templates for visual matching.")
    return templates

_TEMPLATES: Optional[List[Tuple[str, np.ndarray]]] = None

def _get_templates() -> List[Tuple[str, np.ndarray]]:
    global _TEMPLATES
    if _TEMPLATES is None:
        _TEMPLATES = _load_templates()
    return _TEMPLATES

def _image_matches_any_template(gray_img: np.ndarray) -> bool:
    cv2 = _get_cv2()
    templates = _get_templates()
    if cv2 is None or not templates:
        return False
        
    thumb = cv2.resize(gray_img, COMPARE_SIZE, interpolation=cv2.INTER_AREA).astype(np.float32)
    thumb -= thumb.mean()
    norm = np.linalg.norm(thumb)
    if norm > 0:
        thumb /= norm
        for tmpl_name, tmpl_gray in templates:
            tmpl_thumb = cv2.resize(tmpl_gray, COMPARE_SIZE, interpolation=cv2.INTER_AREA).astype(np.float32)
            tmpl_thumb -= tmpl_thumb.mean()
            tmpl_norm = np.linalg.norm(tmpl_thumb)
            if tmpl_norm > 0:
                tmpl_thumb /= tmpl_norm
                score = float(np.dot(thumb.ravel(), tmpl_thumb.ravel()))
                
                thresh = DIRECT_MATCH_THRESHOLD
                if "aadhar" in tmpl_name.lower() or "nuvama" in tmpl_name.lower():
                    thresh = 0.25
                    
                if score >= thresh:
                    logger.info(f"Direct match: embedded image matches template '{tmpl_name}' (score={score:.3f}, threshold={thresh})")
                    return True
                    
    h_img, w_img = gray_img.shape[:2]
    for tmpl_name, tmpl_gray in templates:
        th, tw = tmpl_gray.shape
        thresh = MATCH_THRESHOLD
        if "aadhar" in tmpl_name.lower() or "nuvama" in tmpl_name.lower():
            thresh = 0.30
            
        for scale in SCALES:
            scaled_tw = int(tw * scale)
            scaled_th = int(th * scale)
            if scaled_tw < 12 or scaled_th < 12 or scaled_tw > w_img or scaled_th > h_img:
                continue
            scaled_tmpl = cv2.resize(tmpl_gray, (scaled_tw, scaled_th), interpolation=cv2.INTER_AREA)
            result = cv2.matchTemplate(gray_img, scaled_tmpl, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            if max_val >= thresh:
                logger.info(f"Template fallback match: '{tmpl_name}' matched at scale {scale:.2f} (score={max_val:.3f}, threshold={thresh})")
                return True
    return False

def blur_logos_in_image(img_array: np.ndarray) -> Tuple[np.ndarray, int]:
    cv2 = _get_cv2()
    if cv2 is None:
        return img_array, 0
    templates = _get_templates()
    if not templates:
        return img_array, 0
    total_matches = 0
    h_img, w_img = img_array.shape[:2]
    if img_array.ndim == 2:
        gray_img = img_array
        output = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
    elif img_array.shape[2] == 4:
        output = cv2.cvtColor(img_array, cv2.RGBA2BGR)
        gray_img = cv2.cvtColor(output, cv2.COLOR_BGR2GRAY)
    else:
        output = img_array.copy()
        gray_img = cv2.cvtColor(output, cv2.COLOR_BGR2GRAY)
    for tmpl_name, tmpl_gray in templates:
        th, tw = tmpl_gray.shape
        thresh = MATCH_THRESHOLD
        if "aadhar" in tmpl_name.lower() or "nuvama" in tmpl_name.lower():
            thresh = 0.30
            
        for scale in SCALES:
            scaled_tw = max(1, int(tw * scale))
            scaled_th = max(1, int(th * scale))
            if scaled_tw < 8 or scaled_th < 8 or scaled_tw > w_img or scaled_th > h_img:
                continue
            scaled_tmpl = cv2.resize(tmpl_gray, (scaled_tw, scaled_th), interpolation=cv2.INTER_AREA)
            result = cv2.matchTemplate(gray_img, scaled_tmpl, cv2.TM_CCOEFF_NORMED)
            locs = np.where(result >= thresh)
            seen = set()
            for pt_y, pt_x in zip(*locs):
                bucket = (pt_x // 15, pt_y // 15)
                if bucket in seen:
                    continue
                seen.add(bucket)
                pad = 4
                x1p = max(0, pt_x - pad)
                y1p = max(0, pt_y - pad)
                x2p = min(w_img, pt_x + scaled_tw + pad)
                y2p = min(h_img, pt_y + scaled_th + pad)
                roi = output[y1p:y2p, x1p:x2p]
                output[y1p:y2p, x1p:x2p] = cv2.GaussianBlur(roi, BLUR_KERNEL, 0)
                total_matches += 1
                logger.debug(f"Blurred '{tmpl_name}' @({pt_x},{pt_y}) scale={scale:.2f}")
    return output, total_matches

def blur_logos_in_pil(pil_image):
    cv2 = _get_cv2()
    if cv2 is None:
        return pil_image
    from PIL import Image, ImageFilter
    img_array = np.array(pil_image.convert("RGB"))
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    if not _image_matches_any_template(gray):
        return pil_image
    return pil_image.filter(ImageFilter.GaussianBlur(radius=20))

def blur_logos_in_pdf_page(page) -> int:
    cv2 = _get_cv2()
    if cv2 is None or not _get_templates():
        return 0
    import fitz
    mat = fitz.Matrix(1.5, 1.5)
    pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
    img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
    gray_img = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    total_matches = 0
    h_img, w_img = img_array.shape[:2]
    scale_factor = 1.5
    for tmpl_name, tmpl_gray in _get_templates():
        th, tw = tmpl_gray.shape
        thresh = MATCH_THRESHOLD
        if "aadhar" in tmpl_name.lower() or "nuvama" in tmpl_name.lower():
            thresh = 0.30
            
        for scale in SCALES:
            scaled_tw = max(1, int(tw * scale))
            scaled_th = max(1, int(th * scale))
            if scaled_tw < 8 or scaled_th < 8 or scaled_tw > w_img or scaled_th > h_img:
                continue
            scaled_tmpl = cv2.resize(tmpl_gray, (scaled_tw, scaled_th), interpolation=cv2.INTER_AREA)
            result = cv2.matchTemplate(gray_img, scaled_tmpl, cv2.TM_CCOEFF_NORMED)
            locs = np.where(result >= thresh)
            seen = set()
            for pt_y, pt_x in zip(*locs):
                bucket = (pt_x // 15, pt_y // 15)
                if bucket in seen:
                    continue
                seen.add(bucket)
                x1 = pt_x / scale_factor
                y1 = pt_y / scale_factor
                x2 = (pt_x + scaled_tw) / scale_factor
                y2 = (pt_y + scaled_th) / scale_factor
                rect = fitz.Rect(x1, y1, x2, y2)
                page.draw_rect(rect, color=(0.4, 0.4, 0.4), fill=(0.75, 0.75, 0.75), width=0)
                total_matches += 1
                logger.info(f"PDF: blurred logo '{tmpl_name}' @{rect} scale={scale:.2f}")
    return total_matches
