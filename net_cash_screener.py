"""
日本株 ネットキャッシュ比率スクリーナー

ネットキャッシュ = 現金及び現金同等物 + 短期投資 - 有利子負債（短期+長期）
ネットキャッシュ比率 = ネットキャッシュ / 時価総額
"""

import yfinance as yf
import pandas as pd
import time

# 小型株銘柄コード（時価総額300億円以下が中心）
SMALL_CAP_TICKERS = [
    # ゲーム・エンタメ
    "3765.T",  # ガンホー・オンライン
    "3632.T",  # グリー
    "3659.T",  # ネクソン（中型だが参考）
    "7832.T",  # バンダイナムコ
    "3668.T",  # コロプラ
    "3664.T",  # モバイルファクトリー
    "3907.T",  # シリコンスタジオ
    "4265.T",  # enish
    # IT・SaaS
    "4443.T",  # Sansan
    "4477.T",  # BASE
    "3697.T",  # SHIFT
    "4776.T",  # サイボウズ
    "3923.T",  # rakumo
    "4169.T",  # ENECHANGE
    "4441.T",  # トビラシステムズ
    "4485.T",  # JTOWER
    "4493.T",  # サイバーセキュリティクラウド
    "6200.T",  # インソース
    "6196.T",  # ストライク（M&A仲介）
    "7069.T",  # サイバー・バズ
    "4499.T",  # Speee
    "3834.T",  # 朝日ネット
    # 医療・ヘルスケア
    "6095.T",  # メドピア
    "7776.T",  # セルシード
    "4565.T",  # そーせいグループ
    "4596.T",  # 窪田製薬ホールディングス
    "2158.T",  # FRONTEO
    "7157.T",  # ライフネット生命保険
    # 小売・消費
    "3179.T",  # シュッピン
    "3196.T",  # ホットランド
    "3563.T",  # FOOD & LIFE COMPANIES（スシロー）
    "6069.T",  # トレジャー・ファクトリー
    "9262.T",  # シルバーライフ
    "9627.T",  # アインホールディングス
    "3560.T",  # ほぼ日
    # 金融・フィンテック
    "7342.T",  # ウェルスナビ
    "8771.T",  # イー・ギャランティ
    "7148.T",  # FPG
    "3482.T",  # ロードスターキャピタル
    "3328.T",  # BEENOS
    # 製造・素材
    "6323.T",  # ローツェ
    "6336.T",  # 石井表記
    "6254.T",  # 野村マイクロ・サイエンス
    "6356.T",  # 日本ギア工業
    "6464.T",  # ツバキ・ナカシマ
    # 人材・コンサル
    "2170.T",  # リンクアンドモチベーション
    "7033.T",  # マネジメントソリューションズ
    "7085.T",  # カーブスホールディングス
    "6556.T",  # ウェルビー
    # メディア・出版
    "9418.T",  # U-NEXT Holdings
    "9468.T",  # KADOKAWA
    "3680.T",  # ホットリンク
    # その他
    "9424.T",  # 日本通信
    "6072.T",  # 地盤ネットホールディングス
    "7047.T",  # ポート
    "9603.T",  # H.I.S.
    "2375.T",  # ギグワークス
    "4507.T",  # 塩野義製薬（参考）
]

# 主要な日本株銘柄コード（東証プライム・スタンダード上場の代表的な銘柄）
JAPAN_TICKERS = [
    # テクノロジー
    "6758.T",  # ソニーグループ
    "6861.T",  # キーエンス
    "9984.T",  # ソフトバンクグループ
    "4689.T",  # LINEヤフー
    "3659.T",  # ネクソン
    "9697.T",  # カプコン
    "7974.T",  # 任天堂
    "9613.T",  # NTTデータ
    "4307.T",  # 野村総合研究所
    "9433.T",  # KDDI
    "9432.T",  # 日本電信電話
    "9984.T",  # ソフトバンク
    "6954.T",  # ファナック
    "6902.T",  # デンソー
    "6723.T",  # ルネサスエレクトロニクス
    "8035.T",  # 東京エレクトロン
    "6857.T",  # アドバンテスト
    "4063.T",  # 信越化学工業
    # 金融
    "8306.T",  # 三菱UFJフィナンシャル
    "8316.T",  # 三井住友フィナンシャル
    "8411.T",  # みずほフィナンシャル
    "8591.T",  # オリックス
    "8766.T",  # 東京海上ホールディングス
    # 自動車
    "7203.T",  # トヨタ自動車
    "7267.T",  # 本田技研工業
    "7269.T",  # スズキ
    "7270.T",  # SUBARU
    "7201.T",  # 日産自動車
    # 小売・消費財
    "2914.T",  # JT
    "4452.T",  # 花王
    "4911.T",  # 資生堂
    "8267.T",  # イオン
    "3382.T",  # セブン&アイ・ホールディングス
    "9983.T",  # ファーストリテイリング
    # 製造業
    "6367.T",  # ダイキン工業
    "6301.T",  # 小松製作所
    "6326.T",  # クボタ
    "5108.T",  # ブリヂストン
    "4901.T",  # 富士フイルム
    # 医薬品・ヘルスケア
    "4502.T",  # 武田薬品工業
    "4503.T",  # アステラス製薬
    "4519.T",  # 中外製薬
    "4523.T",  # エーザイ
    "4568.T",  # 第一三共
    # 不動産
    "8801.T",  # 三井不動産
    "8802.T",  # 三菱地所
    "3289.T",  # 東急不動産ホールディングス
    # 素材・化学
    "4183.T",  # 三井化学
    "4005.T",  # 住友化学
    "3402.T",  # 東レ
    "5401.T",  # 日本製鉄
    "5713.T",  # 住友金属鉱山
    # ゲーム・エンタメ
    "3765.T",  # ガンホー・オンライン・エンターテイメント
    "2432.T",  # DeNA
    "3632.T",  # グリー
    "4755.T",  # 楽天グループ
    # その他
    "9020.T",  # 東日本旅客鉄道
    "9022.T",  # 東海旅客鉄道
    "9201.T",  # 日本航空
    "9202.T",  # ANAホールディングス
    "2503.T",  # キリンホールディングス
    "2802.T",  # 味の素
    "2871.T",  # ニチレイ
]


def get_net_cash_ratio(ticker_symbol: str):
    """指定銘柄のネットキャッシュ比率を計算する"""
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info

        # 時価総額
        market_cap = info.get("marketCap")
        if not market_cap or market_cap <= 0:
            return None

        # 現金・短期投資
        cash = info.get("totalCash", 0) or 0

        # 有利子負債（短期借入金 + 長期借入金）
        total_debt = info.get("totalDebt", 0) or 0

        # ネットキャッシュ
        net_cash = cash - total_debt
        net_cash_ratio = net_cash / market_cap

        return {
            "ticker": ticker_symbol,
            "name": info.get("longName", ticker_symbol),
            "market_cap_B": round(market_cap / 1e8, 1),   # 億円
            "cash_B": round(cash / 1e8, 1),                # 億円
            "total_debt_B": round(total_debt / 1e8, 1),    # 億円
            "net_cash_B": round(net_cash / 1e8, 1),        # 億円
            "net_cash_ratio": round(net_cash_ratio * 100, 1),  # %
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "sector": info.get("sector", "不明"),
        }

    except Exception as e:
        print(f"  [{ticker_symbol}] エラー: {e}")
        return None


def run_screener(tickers, label, output_filename):
    total = len(tickers)
    print(f"\n対象銘柄数: {total}")
    print("データ取得中...\n")

    # 重複除去
    unique_tickers = list(dict.fromkeys(tickers))

    results = []
    for i, ticker in enumerate(unique_tickers, 1):
        print(f"[{i:2d}/{len(unique_tickers)}] {ticker} を取得中...", end=" ")
        data = get_net_cash_ratio(ticker)
        if data:
            results.append(data)
            print(f"完了 (ネットキャッシュ比率: {data['net_cash_ratio']}%)")
        else:
            print("スキップ")
        time.sleep(0.3)

    if not results:
        print("データを取得できませんでした。")
        return

    df = pd.DataFrame(results)
    df = df.sort_values("net_cash_ratio", ascending=False)

    print("\n" + "=" * 70)
    print(f"【結果】{label} ネットキャッシュ比率ランキング（上位20銘柄）")
    print("=" * 70)
    print("※ ネットキャッシュ比率 = (現金 - 有利子負債) / 時価総額 × 100")
    print()

    top20 = df.head(20)
    print(f"{'順位':<4} {'銘柄コード':<10} {'企業名':<35} {'比率':>8} {'時価総額(億)':>12} {'現金(億)':>10} {'負債(億)':>10}")
    print("-" * 95)
    for rank, (_, row) in enumerate(top20.iterrows(), 1):
        name = row['name'][:30] if row['name'] else row['ticker']
        print(
            f"{rank:<4} {row['ticker']:<10} {name:<35} "
            f"{row['net_cash_ratio']:>7.1f}% "
            f"{row['market_cap_B']:>11.1f} "
            f"{row['cash_B']:>9.1f} "
            f"{row['total_debt_B']:>9.1f}"
        )

    positive = df[df["net_cash_ratio"] > 0]
    print(f"\nネットキャッシュプラス銘柄: {len(positive)} / {len(df)} 銘柄")

    output_path = f"/Volumes/SanDisk SSD/private/90.work/10.claude/10.work/02.トレーダー/{output_filename}"
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"CSVに保存しました: {output_filename}")

    return df


def main():
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    print("=" * 70)
    print("日本株 ネットキャッシュ比率スクリーナー")
    print("=" * 70)
    print("使い方: python net_cash_screener.py [small|large|all]")
    print(f"実行モード: {mode}")

    if mode == "small":
        run_screener(SMALL_CAP_TICKERS, "小型株", "net_cash_small_cap.csv")
    elif mode == "large":
        run_screener(JAPAN_TICKERS, "大型株", "net_cash_large_cap.csv")
    else:
        all_tickers = list(dict.fromkeys(SMALL_CAP_TICKERS + JAPAN_TICKERS))
        run_screener(all_tickers, "全銘柄（小型＋大型）", "net_cash_result.csv")


if __name__ == "__main__":
    main()
