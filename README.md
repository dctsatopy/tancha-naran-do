# たんちゃーならんど (Tancha-Naran-Do)

感情のセルフモニタリングを習慣化するための Web アプリケーションです。
平日に1日3回のチェックインを通じて、怒り・ストレス・マインドフルネスなどの感情状態を記録・可視化します。

---

## 機能

- **感情チェックイン**: 検証済み心理尺度をベースにした設問（200問）からランダムに10問を出題
- **スコアリング**: 回答をもとに5カテゴリ（怒り・感情調節・マインドフルネス・ストレス・総合）をスコア化
- **ダッシュボード**: 直近7日/30日の感情スコア推移グラフ（折れ線・レーダーチャート）
- **通知**: チェックイン時刻になるとブラウザ通知を表示（Notifications API）
- **週末振り返り**: 土日はホーム画面から振り返りチェックインを作成可能

---

## 技術スタック

| レイヤー | 採用技術 |
|---|---|
| バックエンド | Python 3.11 + FastAPI |
| テンプレートエンジン | Jinja2 |
| データベース | SQLite + SQLAlchemy 2.x |
| スケジューラ | APScheduler 3.x |
| フロントエンド CSS | Bootstrap 5 |
| グラフ | Chart.js 4.x |
| コンテナ | Docker + Docker Compose |
| CI/CD | GitHub Actions |

---

## 起動方法

### Docker Compose（推奨）

```bash
docker compose up -d
```

ブラウザで http://localhost:8080 を開いてください。

### ローカル実行

```bash
pip install -r requirements.txt
DATABASE_URL=sqlite:///./data/tancha.db uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 環境変数

| 変数名 | デフォルト | 説明 |
|---|---|---|
| `DATABASE_URL` | `sqlite:////data/tancha.db` | SQLite DB のパス |
| `TZ` | `Asia/Tokyo` | タイムゾーン |
| `LOG_LEVEL` | `INFO` | ログレベル |
| `LOG_DIR` | `/data/logs` | ログ出力ディレクトリ |
| `ENABLE_DOCS` | `false` | `true` にすると `/docs` `/redoc` を公開 |

---

## API エンドポイント

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/` | ホーム画面 |
| GET | `/check-in` | チェックイン画面 |
| POST | `/check-in/submit` | 回答送信 |
| GET | `/check-in/result/{session_id}` | 結果画面 |
| GET | `/dashboard` | グラフ・履歴画面 |
| GET | `/api/status` | チェックイン待ち確認（ポーリング用） |
| GET | `/api/history` | グラフ用スコア履歴取得 |
| GET | `/api/sessions` | セッション一覧取得 |
| POST | `/api/sessions/weekend` | 週末振り返りセッション生成 |

---

## テスト

```bash
# 依存パッケージのインストール
pip install -r requirements.txt -r requirements-dev.txt

# テスト実行
python -m pytest tests/ -v

# カバレッジレポート付き
python -m pytest tests/ --cov=app --cov-report=term-missing
```

### テスト構成

| ファイル | 内容 |
|---|---|
| `test_scoring.py` | スコア計算ロジック |
| `test_questions_data.py` | 設問データの整合性 |
| `test_messages_data.py` | メッセージデータ |
| `test_api.py` | HTTP エンドポイント統合テスト |
| `test_security.py` | セキュリティヘッダー・入力検証 |
| `test_scheduler.py` | スケジューラ |

---

## ディレクトリ構成

```
tancha-naran-do/
├── app/
│   ├── main.py              FastAPI アプリ本体
│   ├── database.py          DB 接続・セッション管理
│   ├── models.py            SQLAlchemy モデル
│   ├── scheduler.py         APScheduler ジョブ定義
│   ├── questions_data.py    200問の設問データ
│   ├── messages_data.py     リラクセーションメッセージ
│   ├── scoring.py           スコア計算ロジック
│   ├── static/              CSS / JS
│   └── templates/           Jinja2 テンプレート
├── tests/                   pytest テストスイート
├── data/                    SQLite DB・ログ（Docker volume）
├── .github/workflows/ci.yml GitHub Actions CI
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## 出典・免責事項

### 参考心理尺度

設問は下記の検証済み心理尺度を参考に、個人的なセルフモニタリング用として再編集したものです。

| カテゴリ | 参考尺度 | 日本語版出典 |
|---|---|---|
| 怒り感情 | STAXI-2 (State-Trait Anger Expression Inventory-2) | PAR 社が著作権を保有する商業尺度。日本語版は著者許諾のもと研究・臨床目的に使用される。公開文献での邦訳確認不可。 |
| 感情調節困難 | DERS (Difficulties in Emotion Regulation Scale) | 山田圭介・杉江征 (2013). 「感情調節困難尺度日本語版の作成」. *感情心理学研究*, 20(3), 86–95. [DOI: 10.4092/jsre.20.86](https://doi.org/10.4092/jsre.20.86) |
| 認知的感情調節 | CERQ (Cognitive Emotion Regulation Questionnaire) | 榊原良太 (2015). 「認知的感情調節方略尺度（CERQ-J）の開発」. *感情心理学研究*, 23(1), 46–58. |
| マインドフルネス | FFMQ (Five Facet Mindfulness Questionnaire) | Sugiura, Y., Sato, A., Ito, Y., & Murakami, H. (2012). Development and validation of the Japanese version of the Five Facet Mindfulness Questionnaire. *Mindfulness*, 3(2), 85–94. [DOI: 10.1007/s12671-011-0082-1](https://doi.org/10.1007/s12671-011-0082-1) |
| ストレス | PSS (Perceived Stress Scale) | 鷲見克典 (2006). 「知覚されたストレス尺度（PSS）日本語版の信頼性・妥当性の検討」. *健康心理学研究*, 19(2), 44–53. [DOI: 10.11560/jahp.19.2_44](https://doi.org/10.11560/jahp.19.2_44); Mimura, C., & Griffiths, P. (2008). A Japanese version of the Perceived Stress Scale. *BMC Psychiatry*, 8, 85. |

### 免責事項

- 本アプリケーションは**個人的な感情セルフモニタリング**を目的としており、医療診断・治療を目的としたものではありません。
- 上記尺度の設問は参考として再編集したものであり、原著尺度の正式な実施・採点手順とは異なります。
- 精神的な健康について専門的なサポートが必要な場合は、医師・臨床心理士等の専門家にご相談ください。

---

## ライセンス

個人利用目的のプロジェクトです。医療診断を目的としたものではありません。
