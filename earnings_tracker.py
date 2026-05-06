"""
決算情報トラッカー

モード:
  summary  : 全銘柄の直近決算サマリーと次回決算日を表示（デフォルト）
  notify   : 過去7日以内に決算が出た銘柄のみ出力（スケジュール通知用）
"""

import warnings
warnings.filterwarnings("ignore")

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta, timezone, date

WATCH_LIST = {
    # 米国株
    "NVDA":   "エヌビディア",
    "KO":     "コカ・コーラ",
    "DVN":    "デボンエナジー（Devon Energy）",
    # 日本株
    "8053.T": "住友商事",
    "2702.T": "日本マクドナルド",
    "7832.T": "バンダイナムコ",
}


def get_earnings_summary(symbol: str, display_name: str) -> dict:
    result = {
        "symbol": symbol,
        "name": display_name,
        "last_earnings_date": None,
        "next_earnings_date": None,
        "revenue_latest": None,
        "revenue_prev": None,
        "revenue_qoq": None,
        "eps_latest": None,
        "eps_reported": None,
        "eps_estimate": None,
        "eps_surprise": None,
        "currency": "USD",
        "error": None,
    }

    try:
        t = yf.Ticker(symbol)

        # 通貨判定
        try:
            result["currency"] = t.fast_info.currency or "USD"
        except Exception:
            result["currency"] = "JPY" if symbol.endswith(".T") else "USD"

        # カレンダーから次回決算日を取得
        try:
            cal = t.calendar
            if isinstance(cal, dict) and "Earnings Date" in cal:
                today = date.today()
                dates = cal["Earnings Date"]
                if not isinstance(dates, list):
                    dates = [dates]
                future = [d for d in dates if d > today]
                past   = [d for d in dates if d <= today]
                if future:
                    result["next_earnings_date"] = str(future[0])
                if past:
                    result["last_earnings_date"] = str(past[-1])
        except Exception:
            pass

        # earnings_dates から過去の決算実績（EPS）を取得
        try:
            ed = t.earnings_dates
            if ed is not None and not ed.empty:
                now = datetime.now(timezone.utc)
                ed.index = pd.to_datetime(ed.index, utc=True)
                past_rows   = ed[ed.index <= now].sort_index(ascending=False)
                future_rows = ed[ed.index >  now].sort_index(ascending=True)

                if not past_rows.empty:
                    if result["last_earnings_date"] is None:
                        result["last_earnings_date"] = str(past_rows.index[0].date())
                    row = past_rows.iloc[0]
                    result["eps_reported"] = row.get("Reported EPS")
                    result["eps_estimate"] = row.get("EPS Estimate")
                    result["eps_surprise"] = row.get("Surprise(%)")

                if not future_rows.empty and result["next_earnings_date"] is None:
                    result["next_earnings_date"] = str(future_rows.index[0].date())
        except Exception:
            pass

        # 四半期損益計算書から売上・EPS を取得
        try:
            inc = t.quarterly_income_stmt
            if inc is not None and not inc.empty:
                if "Total Revenue" in inc.index and inc.shape[1] >= 1:
                    vals = inc.loc["Total Revenue"].dropna()
                    if len(vals) >= 1:
                        result["revenue_latest"] = float(vals.iloc[0])
                    if len(vals) >= 2:
                        result["revenue_prev"] = float(vals.iloc[1])
                        if result["revenue_prev"] != 0:
                            result["revenue_qoq"] = (result["revenue_latest"] / result["revenue_prev"] - 1) * 100

                if "Diluted EPS" in inc.index and result["eps_latest"] is None:
                    vals = inc.loc["Diluted EPS"].dropna()
                    if len(vals) >= 1:
                        result["eps_latest"] = float(vals.iloc[0])
        except Exception:
            pass

    except Exception as e:
        result["error"] = str(e)

    return result


def fmt_money(val, currency="USD"):
    """金額をわかりやすい単位に変換"""
    if val is None:
        return "N/A"
    if currency == "JPY" or (currency != "USD" and val > 1e9):
        return f"{val/1e8:.0f}億円"
    # USD
    if abs(val) >= 1e9:
        return f"${val/1e9:.2f}B"
    if abs(val) >= 1e6:
        return f"${val/1e6:.1f}M"
    return f"${val:.2f}"


def fmt_pct(val):
    if val is None:
        return "N/A"
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.1f}%"


def print_summary(results: list):
    now_str = datetime.now().strftime("%Y年%m月%d日")
    print("=" * 65)
    print(f"決算情報サマリー　{now_str}")
    print("=" * 65)

    for r in results:
        print(f"\n▶ {r['name']}  ({r['symbol']})")
        if r["error"]:
            print(f"   エラー: {r['error']}")
            continue

        print(f"   直近決算日    : {r['last_earnings_date'] or 'N/A'}")
        print(f"   次回決算日    : {r['next_earnings_date'] or 'N/A'}")

        # 売上
        rev = fmt_money(r["revenue_latest"], r["currency"])
        qoq = fmt_pct(r["revenue_qoq"])
        print(f"   売上（直近Q）  : {rev}  前四半期比 {qoq}")

        # EPS（決算発表値を優先）
        if r["eps_reported"] is not None:
            surp = fmt_pct(r["eps_surprise"])
            est  = f"{r['eps_estimate']:.2f}" if r["eps_estimate"] is not None else "N/A"
            print(f"   EPS（実績）   : {r['eps_reported']:.2f}  予想 {est}  サプライズ {surp}")
        elif r["eps_latest"] is not None:
            print(f"   EPS（直近Q）  : {r['eps_latest']:.2f}")
        else:
            print(f"   EPS           : N/A")


def notify_mode(results: list, days: int = 7):
    """過去N日以内に決算が出た銘柄のみ通知形式で出力する"""
    threshold = date.today() - timedelta(days=days)
    triggered = []

    for r in results:
        if r["last_earnings_date"]:
            try:
                d = date.fromisoformat(r["last_earnings_date"])
                if d >= threshold:
                    triggered.append(r)
            except Exception:
                pass

    if not triggered:
        print(f"✓ 過去{days}日以内に決算発表した監視銘柄はありません。")
        return

    now_str = datetime.now().strftime("%Y年%m月%d日")
    print("=" * 65)
    print(f"【決算通知】{now_str}  過去{days}日以内に決算発表あり")
    print("=" * 65)

    for r in triggered:
        print(f"\n▶ {r['name']}  ({r['symbol']})")
        print(f"   決算日        : {r['last_earnings_date']}")

        rev = fmt_money(r["revenue_latest"], r["currency"])
        qoq = fmt_pct(r["revenue_qoq"])
        print(f"   売上（直近Q）  : {rev}  前四半期比 {qoq}")

        if r["eps_reported"] is not None:
            surp = fmt_pct(r["eps_surprise"])
            est  = f"{r['eps_estimate']:.2f}" if r["eps_estimate"] is not None else "N/A"
            print(f"   EPS（実績）   : {r['eps_reported']:.2f}  予想 {est}  サプライズ {surp}")
        elif r["eps_latest"] is not None:
            print(f"   EPS（直近Q）  : {r['eps_latest']:.2f}")

        print(f"   次回決算日    : {r['next_earnings_date'] or 'N/A'}")


def main():
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "summary"

    print(f"データ取得中...  (モード: {mode})\n")
    results = []
    for symbol, name in WATCH_LIST.items():
        print(f"  {symbol} ({name}) を取得中...")
        results.append(get_earnings_summary(symbol, name))

    print()
    if mode == "notify":
        notify_mode(results, days=7)
    else:
        print_summary(results)


if __name__ == "__main__":
    main()
