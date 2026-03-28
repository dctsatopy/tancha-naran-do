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

## ライセンス

個人利用目的のプロジェクトです。医療診断を目的としたものではありません。
