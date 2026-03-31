"""
VietstockBCTCService — Lấy BCTC đầy đủ từ finance.vietstock.vn
với authenticated session. Cookie hết hạn sau ~30 ngày.

Cần cập nhật .env với cookies mới khi hết hạn.
"""
import os, re, json, time, requests
from pathlib import Path

_ENV = {}
_ENV_PATH = Path(__file__).parent.parent.parent / '.env'
try:
    with open(_ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                k, v = line.split('=', 1)
                _ENV[k.strip()] = v.strip()
except Exception:
    pass

_BASE = 'https://finance.vietstock.vn'
_CACHE: dict = {}
_TTL = 6 * 3600  # 6 tiếng

# ── Vietstock-specific NormId mapping (verified từ data dump DXG 2025) ────
# Balance Sheet (CDKT)
BS_NORMS = {
    3000: 'tai_san_ngan_han',              # A. Tài sản ngắn hạn
    3003: 'tien_mat',                       # I. Tiền & tương đương tiền
    3018: 'tien_mat_thuc',                  # 1. Tiền (cash only)
    3005: 'phai_thu_ngan_han',              # III. Phải thu ngắn hạn
    3022: 'phai_thu_khach_hang',            # 1. Phải thu KH
    3023: 'tra_truoc_nha_cung_cap',         # 2. Trả trước cho người bán NH
    3006: 'hang_ton_kho',                   # IV. Hàng tồn kho ← ĐÚNG (15,658 tỷ)
    3027: 'hang_ton_kho_chi_tiet',          # Hàng tồn kho (detail)
    3001: 'tai_san_dai_han',               # B. Tài sản dài hạn
    2996: 'tong_tai_san',                   # TỔNG TÀI SẢN ← ĐÚNG (38,102 tỷ)
    2997: 'no_ngan_han',                    # I. Nợ ngắn hạn
    3014: 'vay_no_ngan_han',               # Vay nợ ngắn hạn ← (14,480 tỷ)
    3049: 'nguoi_mua_tra_truoc',           # Người mua trả trước ← ĐÚNG (6,219 tỷ)
    2998: 'no_dai_han',                     # II. Nợ dài hạn
    3063: 'vay_no_dai_han',                # Vay nợ dài hạn ← (11,141 tỷ)
    5320: 'vcsh',                           # Vốn chủ sở hữu (6,635 tỷ)
    2999: 'tong_nguon_von',                 # Tổng nguồn vốn (= Total Assets)
}

# Income Statement (KQKD) — need to verify IDs
IS_NORMS = {
    7000: 'doanh_thu',                      # Doanh thu bán hàng
    7020: 'doanh_thu_thuan',                # Doanh thu thuần
    7030: 'gia_von',                        # Giá vốn hàng bán
    7040: 'loi_nhuan_gop',                  # Lợi nhuận gộp
    7070: 'chi_phi_tai_chinh',              # Chi phí tài chính
    7080: 'lai_vay',                        # Lãi vay
    7160: 'loi_nhuan_truoc_thue',           # LN trước thuế
    7180: 'loi_nhuan_sau_thue',             # LN sau thuế
    7200: 'lnst_cty_me',                   # LN của CP cty mẹ
}

# Cash Flow (LCTT)
CF_NORMS = {
    6000: 'ocf',                            # LCTT từ HĐKD (Operating CF)
    6050: 'ocf_net',                        # Lưu chuyển thuần từ HĐKD
    6100: 'icf',                            # LCTT từ ĐT (Investing CF)
    6200: 'fcf',                            # LCTT từ TC (Financing CF)
    6300: 'net_cf',                         # LCTT thuần
}


def _build_headers() -> dict:
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Cookie': _ENV.get('VIETSTOCK_COOKIES', ''),
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer': f'{_BASE}/tai-chinh.htm',
        'Origin': _BASE,
    }


def _form_token() -> str:
    t = _ENV.get('VIETSTOCK_FORM_TOKEN', '')
    if not t:
        m = re.search(r'__RequestVerificationToken=([^;]+)', _ENV.get('VIETSTOCK_COOKIES', ''))
        t = m.group(1) if m else ''
    return t


def _post(endpoint: str, payload: dict) -> any:
    try:
        r = requests.post(f'{_BASE}/data/{endpoint}', headers=_build_headers(),
                          data=payload, timeout=20)
        ct = r.headers.get('Content-Type', '')
        if 'json' in ct or r.text.strip().startswith(('{', '[')):
            return r.json()
        print(f'[VS] {endpoint} returned HTML — session may be expired')
        return None
    except Exception as e:
        print(f'[VS] {endpoint} error: {e}')
        return None


def _get_report_ids(report_type: str, symbol: str) -> list:
    """Lấy list ReportDataID mới nhất (tối đa 3 năm)."""
    ep_map = {'CDKT': 'CDKT_GetListReportData', 'KQKD': 'KQKD_GetListReportData', 'LCTT': 'LCTT_GetListReportData'}
    payload = {
        'StockCode': symbol, 'Unit': '1000000000', 'PeriodType': 'NAM',
        'SortTimeType': 'Time_DESC', 'UnitedId': '-1', 'AuditedStatusId': '-1',
        'IsNamDuongLich': 'false', '__RequestVerificationToken': _form_token(),
    }
    result = _post(ep_map[report_type], payload)
    if not result:
        return []
    data = result.get('data', result) if isinstance(result, dict) else result
    permitted = [r for r in data if r.get('IsShowData_Permission')]
    return permitted[:3]


def _fetch_values(symbol: str, report_ids: list) -> dict:
    """
    Gọi GetReportDataDetailValueByReportDataIds để lấy actual values.
    Trả về dict: {norm_id: value_year1} (lấy Value1 = năm mới nhất).
    """
    if not report_ids:
        return {}
    payload = {
        'StockCode': symbol, 'Unit': '1000000000', 'TypeCompare': '1',
        '__RequestVerificationToken': _form_token(),
    }
    for i, row in enumerate(report_ids[:3]):
        payload[f'listReportDataIds[{i}][Index]'] = str(i)
        payload[f'listReportDataIds[{i}][ReportDataId]'] = str(row['ReportDataID'])
        payload[f'listReportDataIds[{i}][YearPeriod]'] = str(row['YearPeriod'])

    result = _post('GetReportDataDetailValueByReportDataIds', payload)
    if not result:
        return {}
    rows = result.get('data', result) if isinstance(result, dict) else result
    # Build {norm_id: [v1, v2, v3]} — Value1=newest year, Value2=prev year
    values = {}
    for row in rows:
        nid = row.get('ReportNormId')
        if nid is not None:
            values[nid] = {
                'y0': row.get('Value1'),
                'y1': row.get('Value2'),
                'y2': row.get('Value3'),
            }
    return values


def _extract_key_metrics(bs_vals: dict, is_vals: dict, cf_vals: dict, years: list) -> dict:
    """
    Lấy ra các chỉ tiêu quan trọng nhất từ values dict.
    units: tỷ đồng (vì Unit=1000000000 = 1 tỷ).
    """
    def get(vals, norm_id, key='y0'):
        for nid in (norm_id if isinstance(norm_id, list) else [norm_id]):
            v = vals.get(nid, {}).get(key)
            if v is not None:
                return round(v, 1)
        return None

    y0_label = str(years[0]) if years else 'N/A'
    y1_label = str(years[1]) if len(years) > 1 else 'N/A'

    return {
        'report_years': [y0_label, y1_label],
        # Balance Sheet — assets (verified NormIds from Vietstock)
        'cash_bn':              get(bs_vals, 3003),          # Tiền & tương đương
        'inventory_bn':         get(bs_vals, [3006, 3027]),  # Hàng tồn kho ← ĐÚNG
        'current_assets_bn':    get(bs_vals, 3000),          # Tài sản ngắn hạn
        'total_assets_bn':      get(bs_vals, [2996, 2999]),  # Tổng tài sản ← ĐÚNG
        # Balance Sheet — liabilities (verified NormIds)
        'advance_from_customers_bn': get(bs_vals, 3049),    # Người mua trả trước ← ĐÚNG
        'st_debt_bn':           get(bs_vals, 3014),          # Vay nợ ngắn hạn
        'lt_debt_bn':           get(bs_vals, [3063, 2998]),  # Vay nợ dài hạn
        'total_liabilities_bn': get(bs_vals, [2997, 2998]), # Tổng nợ
        'equity_bn':            get(bs_vals, 5320),          # VCSH
        # YoY comparison — prev year
        'inventory_prev_bn':    get(bs_vals, [3006, 3027], 'y1'),
        'advance_prev_bn':      get(bs_vals, 3049, 'y1'),
        # Income Statement
        'revenue_bn':           get(is_vals, [7000, 7020]),
        'gross_profit_bn':      get(is_vals, 7040),
        'interest_expense_bn':  get(is_vals, [7080, 7070]),
        'net_profit_bn':        get(is_vals, [7200, 7180]),
        # Cash Flow
        'ocf_bn':               get(cf_vals, [6000, 6050]),
        'icf_bn':               get(cf_vals, 6100),
        'fcf_bn':               get(cf_vals, 6200),
    }


def fetch_bctc(symbol: str) -> dict:
    """
    Fetch đầy đủ BCTC: Balance Sheet, Income Statement, Cash Flow.
    Returns {} nếu session hết hạn hoặc không có cookies trong .env.
    """
    if not _ENV.get('VIETSTOCK_COOKIES'):
        print('[VS] VIETSTOCK_COOKIES not set in .env')
        return {}

    cached = _CACHE.get(symbol)
    if cached and time.time() - cached.get('_ts', 0) < _TTL:
        return cached

    print(f'[VS] Fetching BCTC for {symbol}...')

    bs_ids = _get_report_ids('CDKT', symbol)
    is_ids = _get_report_ids('KQKD', symbol)
    cf_ids = _get_report_ids('LCTT', symbol)

    if not bs_ids and not is_ids:
        print('[VS] No data — session may be expired')
        return {}

    bs_vals = _fetch_values(symbol, bs_ids)
    is_vals = _fetch_values(symbol, is_ids)
    cf_vals = _fetch_values(symbol, cf_ids)

    years = [r['YearPeriod'] for r in bs_ids]
    km = _extract_key_metrics(bs_vals, is_vals, cf_vals, years)

    result = {
        '_ts': time.time(),
        'symbol': symbol,
        'key_metrics': km,
        'bs_ids': bs_ids,
    }
    _CACHE[symbol] = result
    print(f'[VS] {symbol} BCTC done. Cash={km.get("cash_bn")} tỷ, Inventory={km.get("inventory_bn")} tỷ')
    return result


def get_bctc_for_ai(symbol: str) -> str:
    """
    Format BCTC metrics thành string để inject vào Gemini prompt.
    """
    data = fetch_bctc(symbol)
    if not data:
        return ''
    km = data.get('key_metrics', {})
    years = km.get('report_years', ['N/A'])
    y0 = years[0]

    lines = [f'=== BCTC {symbol} ({y0}) từ Vietstock Finance ===']

    def add(label, val, unit='tỷ đồng', prev_val=None, prev_label=None):
        if val is not None:
            s = f'  {label}: {val:,.1f} {unit}'
            if prev_val is not None and prev_label:
                s += f' (năm trước {prev_label}: {prev_val:,.1f})'
            lines.append(s)

    lines.append('--- TÀI SẢN ---')
    add('Tiền mặt & tương đương', km.get('cash_bn'))
    add('Hàng tồn kho', km.get('inventory_bn'), prev_val=km.get('inventory_prev_bn'), prev_label=years[1] if len(years) > 1 else '')
    add('Tài sản ngắn hạn', km.get('current_assets_bn'))
    add('Tổng tài sản', km.get('total_assets_bn'))

    lines.append('--- NỢ ---')
    add('Người mua trả trước', km.get('advance_from_customers_bn'), prev_val=km.get('advance_prev_bn'), prev_label=years[1] if len(years) > 1 else '')
    add('Vay nợ ngắn hạn', km.get('st_debt_bn'))
    add('Vay nợ dài hạn', km.get('lt_debt_bn'))
    add('Tổng nợ phải trả', km.get('total_liabilities_bn'))
    add('Vốn chủ sở hữu', km.get('equity_bn'))

    lines.append('--- KẾT QUẢ KINH DOANH ---')
    add('Doanh thu', km.get('revenue_bn'))
    add('Lợi nhuận gộp', km.get('gross_profit_bn'))
    add('Chi phí lãi vay', km.get('interest_expense_bn'))
    add('LNST', km.get('net_profit_bn'))

    lines.append('--- DÒNG TIỀN ---')
    add('OCF (HĐKD)', km.get('ocf_bn'))
    add('ICF (Đầu tư)', km.get('icf_bn'))
    add('FCF (Tài chính)', km.get('fcf_bn'))

    return '\n'.join(lines) if len(lines) > 5 else ''


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    result = fetch_bctc('DXG')
    if result:
        print('SUCCESS!')
        km = result.get('key_metrics', {})
        print(json.dumps(km, ensure_ascii=False, indent=2))
        print('\n=== AI Summary ===')
        print(get_bctc_for_ai('DXG'))
    else:
        print('FAILED — check session cookies in .env')
