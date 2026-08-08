# たんちゃーならんど (Tancha-Naran-Do) — 開発経緯・仕様書

> 作成日: 2026-03-27
> ステータス: 実装中

---

## 1. 経緯・背景

感情（特に怒り）のセルフコントロールを習慣的に改善したいという動機から開発を開始した。
習慣的なセルフチェックと気づきによって、感情の傾向を把握し克服することを目指す。

---

## 2. 目的

- 感情（特に怒り）のセルフコントロール能力を高める。
- 日々の感情状態を可視化し、自己の傾向を把握する。
- 気づき・受容・認知的再評価などの心理的スキルを身につける。

---

## 3. 機能要件

### 3.1 感情チェック（メイン機能）

| 項目 | 仕様 |
|---|---|
| 実施タイミング | 曜日問わず（平日・休祝日共通）9:00〜22:00 の間にランダムで 1日2回 |
| 設問数/セッション | 1セッションあたり 8〜10問（約5分で回答可能） |
| 設問総数 | 120問（6カテゴリ） |
| 出題方式 | 120問からランダムに選出 |
| 回答形式 | 4段階リッカート尺度（1〜4） |

- 同一セッションのチェックイン画面は再アクセス時も同じ問題セットを表示する（セッションIDをシードにした固定サンプリング）

### 3.2 感情グラフ画面

- 日々の感情スコア推移グラフ（折れ線グラフ）
- カテゴリ別スコアのレーダーチャート
- 直近7日間・30日間の切り替え表示

### 3.3 リラクセーションメッセージ

- チェックイン画面・結果画面にリラックス・心落ち着かせる言葉を表示
- 名言・心理学的な知見に基づいたメッセージ（50件以上）

### 3.5 週末振り返りチェックイン

| 項目 | 仕様 |
|---|---|
| 対象曜日 | 土・日のみ |
| トリガー | ホーム画面を開いた際、当日のセッションが0件のとき |
| UI | モーダルダイアログで「振り返りチェックインを作成しますか？」を表示 |
| OK 操作 | `POST /api/sessions/weekend` を呼び出し、セッション1件を作成して画面リロード |
| 「後で」操作 | モーダルを閉じるだけ（その後の同じ日の再アクセスでもセッションが0件ならまた表示） |
| チェックイン時刻 | 18:00〜21:00 の間でランダムに1件生成 |
| 目的 | その日に平穏な心の状態を維持できたかを振り返るため |

### 3.4 通知機能

- スケジューラが毎朝0時に当日の2回分のチェックイン時刻を生成・保存
- フロントエンドが30秒ごとにポーリングし、チェックイン時刻になったらブラウザ通知を表示
- ブラウザ Notifications API を使用

---

## 4. 設問の出典・根拠

以下の検証済み心理尺度・認知行動療法（CBT）の理論を参考に、日常的な状態チェック用に編集した設問を使用する。

| カテゴリ | 参考尺度・理論 | 主要出典 | 問数 |
|---|---|---|---|
| 怒りの状態 (anger_state) | STAXI-2 State Anger, DAR-5, CAS | Spielberger (1999); Forbes et al. (2014); Snell et al. (1995) | 25問 |
| 認知パターン (cognitive_pattern) | Beck の認知的歪み, Novaco Cognitive | Beck (1976); Novaco (1994); Burns (1980) | 25問 |
| 身体反応 (physiological) | Novaco Arousal, InAn Factor 1 | Novaco (1994); Ferretti et al. (2025, BMC Psychiatry) | 15問 |
| 行動傾向 (behavioral) | Novaco Behavioral, STAXI-2 Expression | Novaco (1994); Spielberger (1999) | 20問 |
| 感情調節 (emotion_regulation) | DERS, InAn Factor 2, CERQ | Gratz & Roemer (2004); Garnefski et al. (2001) | 20問 |
| 心理的状態 (psychological_state) | K6, PANAS | Kessler et al. (2003); Watson et al. (1988) | 15問 |
| **合計** | | | **120問** |

> **注記**: 設問は上記尺度・理論を参考に日常の状態チェック用として再編集したものです。
> 医療診断目的ではなく、個人的な感情セルフモニタリングを目的としています。
> 特に認知パターンカテゴリは CBT（認知行動療法）の枠組みに基づき、怒りに関連する
> 認知的歪み（べき思考・読心術・破局化・反芻・敵意帰属・ラベリング・白黒思考）を
> 状態レベルで評価できるよう設計しています。

---

## 5. 技術スタック

| レイヤー | 採用技術 | 選定理由 |
|---|---|---|
| バックエンド | Python 3.14（最新安定版）+ FastAPI | 非同期対応・型安全・軽量 |
| テンプレートエンジン | Jinja2 | サーバーサイドレンダリングで簡素な構成 |
| データベース | SQLite + SQLAlchemy 2.x | Docker 内で完結・外部依存なし |
| スケジューラ | APScheduler 3.x | プロセス内スケジューリング |
| フロントエンド CSS | Bootstrap 5 | レスポンシブ・カスタマイズ容易 |
| グラフ | Chart.js 4.x | 軽量・日本語対応 |
| コンテナ | Docker + Docker Compose | ポータブルな実行環境 |
| CI/CD | GitHub Actions | pytest 実行 + Docker イメージビルド確認（push なし） |

### 5.1 バージョンポリシー

- **Python は常に最新の安定版（stable）メジャーリリースを利用する**（2026-07-09 時点: 3.14 系）。
- Python バージョンは以下の 4 箇所で一致させること。不整合は `tests/test_environment.py` で検出する。
  1. `Dockerfile` のベースイメージ（`python:3.14-slim`）
  2. `.github/workflows/ci.yml` の `python-version`
  3. `README.md` の技術スタック表
  4. 本仕様書 §5 の技術スタック表
- 依存パッケージ（`requirements.txt` / `requirements-dev.txt`）は最新安定版にピン留めし、Dependabot の週次更新と `pip-audit` による脆弱性チェックで維持する。

---

## 6. アーキテクチャ

```
[ブラウザ]
    │  HTTP (port 8080)
    ▼
[Docker コンテナ]
    ├─ FastAPI (uvicorn)
    │    ├─ GET  /                  ホーム画面
    │    ├─ GET  /check-in          チェックイン画面
    │    ├─ POST /check-in/submit   回答送信・結果表示
    │    ├─ GET  /dashboard         グラフ・履歴画面
    │    ├─ GET  /api/status        チェックイン待ち確認 (polling)
    │    ├─ GET  /api/history       グラフ用データ取得
    │    └─ POST /api/sessions/weekend  土日の振り返りセッション生成
    ├─ APScheduler
    │    └─ 毎朝0時に当日チェックイン時刻を生成
    └─ SQLite (./data/tancha.db)
         ├─ check_in_sessions  チェックイン予定・実績
         ├─ check_in_answers   各設問への回答
         └─ emotional_scores   セッションごとのスコア集計
```

---

## 7. データベース設計

### check_in_sessions

| カラム | 型 | 説明 |
|---|---|---|
| id | INTEGER PK | |
| access_token | VARCHAR(36) UNIQUE | UUID v4。結果ページURL に使用し、連番IDによる推測を防止する |
| scheduled_at | DATETIME | 予定時刻 |
| started_at | DATETIME | 開始時刻 |
| completed_at | DATETIME | 完了時刻 |
| status | VARCHAR | pending / in_progress / completed / skipped |

### check_in_answers

| カラム | 型 | 説明 |
|---|---|---|
| id | INTEGER PK | |
| session_id | INTEGER FK | |
| question_id | INTEGER | 設問ID (1〜200) |
| answer_value | INTEGER | 回答値 (1〜4) |
| answered_at | DATETIME | |

### emotional_scores

| カラム | 型 | 説明 |
|---|---|---|
| id | INTEGER PK | |
| session_id | INTEGER FK | |
| date | DATE | |
| anger_state_score | FLOAT | 怒りの状態スコア (0〜100、低いほど良好) |
| cognitive_pattern_score | FLOAT | 認知パターンスコア (0〜100、低いほど良好)。認知的歪みの強さを反映 |
| physiological_score | FLOAT | 身体反応スコア (0〜100、低いほど良好)。身体的覚醒の強さを反映 |
| behavioral_score | FLOAT | 行動傾向スコア (0〜100、低いほど良好)。攻撃的行動傾向の強さを反映 |
| emotion_regulation_score | FLOAT | 感情調節スコア (0〜100、低いほど良好)。調節困難度を反映 |
| psychological_state_score | FLOAT | 心理的状態スコア (0〜100、低いほど良好)。心理的苦痛の強さを反映 |
| overall_score | FLOAT | 総合スコア (0〜100、高いほど良好)。文献に基づく重み付け計算式（§4.1 参照） |

#### 4.1 スコアリング方式

各カテゴリスコアは 0〜100 に正規化（低い = 良好）。overall は以下の重み付けで算出:

```
overall = (100 - anger_state)       × 0.25
        + (100 - cognitive_pattern)  × 0.20
        + (100 - physiological)      × 0.15
        + (100 - behavioral)         × 0.15
        + (100 - emotion_regulation) × 0.15
        + (100 - psychological_state)× 0.10
```

重み付けの根拠:
- anger_state (0.25): 本アプリの主目的である怒り状態の直接測定（STAXI-2 State Anger を最重要視）
- cognitive_pattern (0.20): CBT の中核概念。Novaco モデルにおいて認知は慢性的怒りと長期的攻撃リスクの最良予測因子
- physiological (0.15): InAn (2025) の因子分析で覚醒管理困難が分散の 58.8% を占める重要因子
- behavioral (0.15): Novaco モデルの行動成分。対人関係への直接的影響度
- emotion_regulation (0.15): DERS に基づく感情調節能力。全カテゴリを媒介する保護因子
- psychological_state (0.10): K6/PANAS に基づく文脈情報。怒りの背景にある全般的な心理状態

重症度ラベル（overall に基づく、CAS・K6・DASS-21 の閾値を統合）:
- ≥ 70: 良好（CAS minimal ≈ 79%、K6 low ≈ 79%、DASS-21 normal ≈ 67% の収束点）
- ≥ 45: 普通（K6 moderate ≈ 46%、DASS-21 moderate ≈ 41% の中間域）
- ≥ 25: 注意（DASS-21 severe ≈ 21% 付近）
- < 25: 要ケア（複数尺度で臨床的に有意な水準）

---

## 8. ディレクトリ構成

```
tancha-naran-do/
├── app/
│   ├── __init__.py
│   ├── main.py              FastAPI アプリ本体
│   ├── database.py          DB 接続・セッション管理
│   ├── models.py            SQLAlchemy モデル
│   ├── scheduler.py         APScheduler ジョブ定義
│   ├── questions_data.py    200問の設問データ
│   ├── messages_data.py     リラクセーションメッセージ
│   ├── scoring.py           スコア計算ロジック
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/
│   │       ├── notifications.js
│   │       └── dashboard.js
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── check_in.html
│       ├── result.html
│       └── dashboard.html
├── alembic/                 Alembic マイグレーションスクリプト
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_add_access_token_to_sessions.py
├── data/                    SQLite DB (Docker volume)
├── .github/
│   ├── workflows/
│   │   └── ci.yml           GitHub Actions CI
│   └── dependabot.yml       依存ライブラリ自動更新設定
├── alembic.ini              Alembic 設定ファイル
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
└── .gitignore
```

---

## 9. 画面設計

### 9.1 ホーム画面 (`/`)
- 今日のチェックイン状況（完了数/3回）
- 次回チェックイン予定時刻
- 最新のスコアサマリ
- リラクセーションメッセージ

### 9.2 チェックイン画面 (`/check-in`)
- ランダムに選出された10〜12問を表示
- プログレスバーで進捗表示
- 回答フォーム（ラジオボタン、1〜4段階）
- 画面上部にリラクセーションメッセージ

### 9.3 結果画面 (`/check-in/result`)
- セッションのスコア（カテゴリ別）
- 高スコア設問への解説とアドバイス
- 次のチェックイン予定時刻
- リラクセーションメッセージ

### 9.4 ダッシュボード画面 (`/dashboard`)
- 直近7日/30日の感情スコア折れ線グラフ
- カテゴリ別スコアのレーダーチャート
- チェックイン履歴一覧

---

## 10. 非機能要件

| 項目 | 仕様 |
|---|---|
| 実行環境 | Docker コンテナ（シングルコンテナ） |
| 外部依存 | なし（SQLite のみ使用） |
| データ永続化 | Docker volume (./data) |
| ポート | 8080 |
| ログ | stdout + `/data/logs/access.log`, `/data/logs/app.log`（RotatingFileHandler） |
| 認証 | Basic 認証（オプトイン）。環境変数 `BASIC_AUTH_USER` / `BASIC_AUTH_PASSWORD` を設定した場合のみ有効化。未設定時はローカル利用想定で無認証（起動時に警告ログを出力） |
| ヘルスチェック | `GET /health` → `{"status": "ok"}`（コンテナオーケストレーター向け） |

---

## 11. セキュリティ要件

### 11.1 HTTP セキュリティヘッダー（全レスポンス）

| ヘッダー | 値 |
|---|---|
| `Content-Security-Policy` | `default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; style-src 'self' https://cdn.jsdelivr.net; font-src https://cdn.jsdelivr.net data:; img-src 'self' data:; connect-src 'self'; form-action 'self'; base-uri 'self'; frame-ancestors 'none'` |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` |

> **注記**: `X-XSS-Protection` は現代のブラウザでは非推奨のため削除。CSP ヘッダーで代替する。
> **注記**: `Strict-Transport-Security` は HTTPS 終端をリバースプロキシに委ねる構成を見据えて付与している。HTTP レスポンスに含めてもブラウザは無視するため平文運用時の副作用はない。
> **注記**: `script-src` / `style-src` は `'unsafe-inline'` を含まない。テンプレート内のインライン `<script>` は `app/static/js/check-in.js`・`weekend-modal.js`・`progress-bars.js` へ外部化し、動的な幅指定を伴うインライン `style` 属性は `data-progress-width` 属性 + `progress-bars.js` による JS 適用に置き換えた（固定値の高さは `.progress-thin` / `.progress-mid` / `.progress-thick` の CSS クラス化）。`dashboard.html` の `onclick` 属性も `data-days` 属性 + `addEventListener` に置き換えている。

### 11.2 入力バリデーション

| 項目 | 検証内容 |
|---|---|
| `session_id` | 正の整数のみ受付（非数値・0・負値 → 400） |
| `question_id` | 1〜120 の既存 ID のみ受付（範囲外・未定義 → 400） |
| `answer_value` | 1〜4 のみ受付（範囲外・非整数 → 400） |
| `days` パラメータ | 1〜365 の範囲（範囲外 → 422） |
| `limit` パラメータ | 1〜200 の範囲（範囲外 → 422） |
| 完了済みセッションへの再送信 | `status == "completed"` のセッションへの POST → 409 |

### 11.3 セッション識別子

- 各 `CheckInSession` は UUID v4 形式の `access_token` を持つ
- 結果ページ URL は `/check-in/result/{access_token}` の形式とし、連番整数による推測を防止する
- 既存セッション（DB 移行前）に対してはアプリ起動時に自動で UUID を付与する（`_migrate_access_tokens()`）
- Alembic マイグレーション `0001_add_access_token_to_sessions.py` でも対応可能
- 万一 `access_token` が未設定のままリダイレクトが必要になった場合も、連番の `session.id` を代替トークンとして使わず、その場で UUID v4 をオンデマンド発行する（`_ensure_access_token()`）
- アクセスログに出力する `/check-in/result/{access_token}` はトークン部分を `***` にマスクする（ログ閲覧者による結果ページなりすまし閲覧を防止。§12.2）

### 11.4 CSRF 保護

- `CsrfMiddleware` により POST リクエストの `Origin` / `Referer` ヘッダーを検証する
- `Origin` ヘッダーが存在し、リクエストホストと不一致 → 403 を返す
- `Origin` 不在で `Referer` ヘッダーが存在し、`urlparse(referer).netloc` がリクエストホストと不一致 → 403 を返す（`host in referer` のような部分文字列一致は `https://attacker.example/<host>/evil` のような Referer でバイパスされるため使用しない）
- `Origin` / `Referer` のいずれも存在しない場合も 403 を返す（本アプリはブラウザからのフォーム送信のみを想定しており curl 等の直接呼び出しはサポート対象外のため）

### 11.5 レート制限

- `slowapi` ライブラリによる IP アドレス単位のレート制限
- `/check-in/submit`: 60回/分
- `/api/sessions/weekend`: 10回/分
- 制限超過時は 429 Too Many Requests を返す
- 環境変数 `DISABLE_RATE_LIMIT=true` で無効化（テスト時に使用）

### 11.6 その他

- API ドキュメント（`/docs`, `/redoc`, `/openapi.json`）はデフォルト非公開（`ENABLE_DOCS=true` で有効化）
- Docker コンテナは非 root ユーザー（`appuser`, UID=1000）で実行
- Basic 認証（オプトイン）: `BASIC_AUTH_USER` / `BASIC_AUTH_PASSWORD` を両方設定した場合のみ `BasicAuthMiddleware` が全エンドポイント（`/health`, `/static/*` を除く）に認証を要求する。パスワード比較は `secrets.compare_digest` によるタイミング攻撃対策を行う。未設定時は起動時に警告ログを出力する

---

## 12. ロギング仕様

### 12.1 出力先

| ログ種別 | stdout | ファイル |
|---|---|---|
| アクセスログ | ✓ | `/data/logs/access.log` |
| 業務操作ログ | ✓ | `/data/logs/app.log` |

### 12.2 ログフォーマット

```
YYYY-MM-DD HH:MM:SS LEVEL    logger_name          message
```

アクセスログには UUID v4 形式のリクエスト ID が含まれる：

```
2026-03-29 10:00:00 INFO     access               req_id=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx 127.0.0.1 GET / 200 12.3ms
```

リクエスト ID は `request.state.request_id` に格納されており、下流のハンドラーからも参照可能。

### 12.3 業務操作ログの出力タイミング

| イベント | レベル | 内容 |
|---|---|---|
| チェックイン開始 | INFO | `[CHECK-IN] session_id=N started` |
| 回答送信完了 | INFO | `[SUBMIT] session_id=N completed answers=10 overall_score=72.3` |
| 不正 session_id | WARNING | `[SUBMIT] Invalid session_id received: 'abc'` |
| 不正 question_id | WARNING | `[SUBMIT] Unknown question_id=999 session_id=N` |
| 範囲外 answer_value | WARNING | `[SUBMIT] Out-of-range answer_value=9 question_id=1 session_id=N` |
| 完了済みセッションへの再送信 | WARNING | `[SUBMIT] Already completed session_id=N` |
| CSRF 保護による拒否 | WARNING | `[CSRF] Rejected POST from Origin=... (expected host=...) path=...` |
| DB 操作エラー（スケジューラ） | ERROR | `Database error while generating daily sessions: ...` |

### 12.4 ローテーション設定

- 最大ファイルサイズ: 10 MB
- 保持世代数: 5（計最大 50 MB）
- 環境変数 `LOG_LEVEL`（デフォルト: `INFO`）でレベル制御

---

## 13. テスト戦略

### 13.1 TDD 運用方針

仕様の追加・変更・削除があるたびに、以下の順序で作業を行う：

1. **仕様変更を `development_background.md` に反映**
2. **テストを先に書く**（Red フェーズ）
3. **実装を行う**（Green フェーズ）
4. **リファクタリング**（Refactor フェーズ）
5. **テストを実行し、全件 PASSED を確認する**
6. 作業ブランチを作成し PR を出す（`main` への直接コミット禁止）

> **重要**: commit / push / PR 作成の前に、必ず `pytest` を実行してすべてのテストが通ることを確認すること。

### 13.2 テストスイート構成

```
tests/
├── conftest.py               # フィクスチャ（テスト用 DB・TestClient・CSRF ヘッダーヘルパー）
├── test_conftest.py          # conftest.py のテストヘルパーに対するテスト
├── test_scoring.py           # スコア計算ロジックのユニットテスト
├── test_questions_data.py    # 設問データの整合性テスト
├── test_messages_data.py     # メッセージデータのユニットテスト
├── test_api.py               # HTTP エンドポイントの統合テスト
├── test_security.py          # セキュリティヘッダー・入力検証テスト
├── test_main.py              # Basic 認証・CSRF ヘッダー欠如・access_token・ログマスキングのテスト
├── test_scheduler.py         # スケジューラのユニットテスト
└── test_environment.py       # 実行環境・バージョン整合性テスト（§5.1）
```

フロントエンド JS（`app/static/js/*.js`）については Node.js 標準の `node:test` によるユニットテストを併設している（`*.test.js`、`node --test app/static/js/*.test.js` で実行）。DOM は最小限のスタブで代替している。

### 13.3 テスト環境

| 項目 | 内容 |
|---|---|
| フレームワーク | pytest 9.x |
| HTTP クライアント | FastAPI TestClient (httpx) |
| テスト DB | SQLite インメモリ（`/tmp/tancha_naran_do_test.db`） |
| 時刻モック | freezegun |
| カバレッジ | pytest-cov |

### 13.4 テスト実行方法

```bash
# Docker コンテナ内で実行（推奨）
docker exec -w /app <container_id> python -m pytest tests/ -v

# カバレッジレポート付き
docker exec -w /app <container_id> python -m pytest tests/ --cov=app --cov-report=term-missing
```

### 13.5 テスト件数（2026-08-08 時点）

| テストファイル | テストクラス | テスト件数 |
|---|---|---|
| test_scoring.py | TestCalculateScores, TestGetScoreLabel | 29 |
| test_questions_data.py | TestQuestionsData, TestQuestionById | 28 |
| test_messages_data.py | TestRelaxationMessages, TestGetRandomMessage, TestGetMessages | 12 |
| test_api.py | 9クラス（全エンドポイント + 週末セッション） | 65 |
| test_security.py | 7クラス（ヘッダー・CSRF・ヘルスチェック・バリデーション・境界値） | 48 |
| test_main.py | Basic 認証・CSRF ヘッダー欠如・access_token オンデマンド発行・ログマスキング | 10 |
| test_conftest.py | TestWithoutCsrfHeaders | 1 |
| test_scheduler.py | TestGenerateDailySessions, TestGenerateWeekendSession | 21 |
| test_environment.py | TestPythonVersionConsistency, TestDependencyPins | 9 |
| **合計（pytest）** | | **223** |

上記に加え、`app/static/js/*.test.js`（`node --test`）11件がフロントエンド JS を対象にカバーする。

---

## 14. GitHub リポジトリ

- リポジトリ名: `tancha-naran-do`
- デフォルトブランチ: `main`
- **作業ブランチルール**: `main` への直接コミット禁止。必ず作業ブランチを作成してから作業する。

---

## 15. 変更履歴

| 日付 | 内容 |
|---|---|
| 2026-03-27 | 初版作成。要件・設計・技術スタック確定。 |
| 2026-03-27 | チェックイン時刻のチャイム通知機能を追加（Web Audio API）。 |
| 2026-03-27 | セキュリティ強化（入力検証・HTTPヘッダー・非 root 実行・ドキュメント非公開）。 |
| 2026-03-27 | アクセスログ・業務操作ログのファイル出力機能を追加（RotatingFileHandler）。 |
| 2026-03-27 | テストスイート新設（pytest, 161件）。TDD 運用方針を策定。 |
| 2026-03-28 | バグ修正・品質改善（overall スコア計算式修正、二重送信防止、セッション固定サンプリング、テスト追加）。 |
| 2026-03-28 | overall スコア計算修正: regulation_score を反転（DERS は高い=困難=悪い状態のため `(100-regulation)×0.2` に統一）。 |
| 2026-03-28 | 週末振り返りチェックイン機能を追加（§3.5）。土日にホーム画面でモーダルプロンプト表示、`POST /api/sessions/weekend` で 18:00〜21:00 にセッション生成。 |
| 2026-03-28 | GitHub Actions CI を再構成: pytest ジョブ → Docker build ジョブ（push なし）の2ジョブ構成に変更。スモークテストを pytest に置き換え。 |
| 2026-03-28 | セキュリティ強化（fix/security-hardening）: CSP ヘッダー追加、X-XSS-Protection 削除、SRI ハッシュ追加、キャッシュ制御、XSS 修正。§11.1 更新。 |
| 2026-03-28 | 依存パッケージ・GitHub Actions をすべて最新安定版に更新。GitHub Actions はコミットハッシュ固定に変更。 |
| 2026-03-28 | §4 設問出典を調査結果に基づき修正（CERQ: 橋本・田中 2005 → 榊原 2015、STAXI-2: 著作権確認不可として注記）。README.md に「出典・免責事項」セクション追加。 |
| 2026-03-29 | コードレビュー対応（全11項目）。詳細は以下のとおり。 |
| 2026-03-29 | [S-1] セッション識別子にランダムトークン（UUID v4）を導入。結果ページURLを `/check-in/result/{access_token}` 形式に変更し、連番整数による推測を防止。DB スキーマ変更: `check_in_sessions.access_token` カラム追加（§7, §11.3）。 |
| 2026-03-29 | [S-2] CSRF 保護ミドルウェアを追加（`CsrfMiddleware`）。Origin/Referer ヘッダーを検証し、クロスオリジンからの不正 POST を 403 で拒否（§11.4）。 |
| 2026-03-29 | [S-3] slowapi によるレート制限を導入。`/check-in/submit` 60回/分、`/api/sessions/weekend` 10回/分（§11.5）。 |
| 2026-03-29 | [C-1] `scheduler.py` の例外処理を具体化。`SQLAlchemyError` とその他の `Exception` を分離してログ出力を改善（§12.3）。 |
| 2026-03-29 | [C-2] アクセスログに UUID v4 形式のリクエスト ID を追加。リクエスト単位での追跡が可能に（§12.2）。 |
| 2026-03-29 | [O-1] ヘルスチェックエンドポイント `GET /health` を追加（§10）。 |
| 2026-03-29 | [O-2] Dependabot 設定（`.github/dependabot.yml`）を追加。pip および GitHub Actions の依存関係を週次で自動更新（§8）。 |
| 2026-03-29 | [O-3] Alembic マイグレーション基盤を追加（`alembic.ini`, `alembic/env.py`, `alembic/versions/0001_add_access_token_to_sessions.py`）。`requirements-dev.txt` に `alembic` を追加（§8）。 |
| 2026-03-29 | [T-1] スコア計算の境界値テストを6件追加（全回答値1/4・中間値・カテゴリ単独・認知的調節の方向性）。 |
| 2026-03-29 | [T-2] 並行送信によるスコア重複保存が発生しないことを確認するテストを追加（`ThreadPoolExecutor` 使用）。 |
| 2026-03-29 | テスト件数: 181 → 193 件（§13.5）。 |
| 2026-03-30 | バグ修正: mindfulness・cognitive_regulation の overall スコア方向を統一。逆転項目（reverse=True）の設計に合わせ、全カテゴリ「低い=良好」に統一。overall 計算式を `(100-mindfulness)×0.2 + (100-cognitive_regulation)×0.1` に修正（§7）。依存: alembic 1.16.1 → 1.18.4。 |
| 2026-04-02 | 仕様書ドキュメントバグ修正: `regulation_score` の方向性説明を「高いほど良好」→「低いほど良好」に修正（§7）。2026-03-28 のコード修正（DERS は高い=困難=悪い）が仕様書に未反映だったため。 |
| 2026-05-04 | 大規模仕様変更: (1) スケジュールを平日9-18時×3回 → 曜日問わず9-22時×2回に変更（§3.1, §3.4）。(2) 設問を200問5カテゴリ → 120問6カテゴリに再編成。CBT（認知行動療法）・アンガーマネジメント文献に基づき、現在の心理状態・怒りの状態をより的確に評価できる設問構成に刷新（§4）。新カテゴリ: anger_state, cognitive_pattern, physiological, behavioral, emotion_regulation, psychological_state。(3) スコアリングを文献に基づく重み付けに最適化（§4.1）。重症度ラベル閾値を CAS・K6・DASS-21 の検証済み閾値に基づき 70/45/25 に変更。(4) emotional_scores テーブルのカラムを新カテゴリに対応するよう変更（§7）。週末振り返り機能は維持。 |
| 2026-07-09 | Python を最新安定版 3.14 に統一し、バージョンポリシーを策定（§5, §5.1）。CI（3.11→3.14）・README を Dockerfile（python:3.14-slim）に合わせて修正。バージョン整合性テスト `test_environment.py` を新設（9件）。依存パッケージを最新化: fastapi 0.136.3→0.139.0, uvicorn 0.49.0→0.51.0, sqlalchemy 2.0.50→2.0.51, apscheduler 3.11.2→3.11.3, slowapi 0.1.9→0.1.10, pytest 9.0.3→9.1.1, alembic 1.18.4→1.18.5。pip-audit で既知脆弱性ゼロを確認。テスト件数: 202→211 件（§13.5）。 |
| 2026-08-08 | Lint 自動化を導入: `pyproject.toml` を新規作成し `ruff`（line-length=120）を設定、`requirements-dev.txt` に `ruff==0.16.2` を追加。`ruff check --fix` により import 順序・未使用 import 等 32件を自動修正。テスト211件全通過を確認。**保留事項**: 行長超過・デフォルト引数でのミュータブル変数使用など手動修正が必要な135件は未対応のまま残置（別途対応予定）。 |
| 2026-08-08 | 俯瞰的セキュリティレビュー対応（全6項目）。詳細は以下のとおり。 |
| 2026-08-08 | [1] エンドポイント無認証を解消: `BasicAuthMiddleware` を追加（オプトイン方式）。`BASIC_AUTH_USER` / `BASIC_AUTH_PASSWORD` を両方設定した場合のみ全エンドポイント（`/health`, `/static/*` を除く）に Basic 認証がかかる。未設定時は起動時に警告ログを出力（§10, §11.6）。 |
| 2026-08-08 | [2] CSP から `'unsafe-inline'` を除去: テンプレートのインライン `<script>`/`style` 属性/`onclick` 属性を全廃し、`app/static/js/check-in.js`・`weekend-modal.js`・`progress-bars.js` へ外部化。`dashboard.js` の期間切替ボタンは `data-days` 属性 + `addEventListener` に変更（§11.1）。 |
| 2026-08-08 | [3] CSRF 保護を強化: `Origin`/`Referer` ヘッダーが両方欠如する POST も 403 で拒否するよう変更（従来は許可していた。§11.4）。 |
| 2026-08-08 | [4] `access_token` の `session.id` フォールバックを除去: 未設定時は連番 ID を使わずその場で UUID v4 をオンデマンド発行する `_ensure_access_token()` に統一（§11.3）。 |
| 2026-08-08 | [5] アクセスログの `access_token` をマスク: `/check-in/result/{access_token}` のトークン部分をログ上で `***` に置換（§11.3, §12.2）。 |
| 2026-08-08 | [6] `docker-compose.yml` に `ENABLE_DOCS=false` / `DISABLE_RATE_LIMIT=false` を明示し、意図しない有効化を防止。README に運用上の注意（Basic 認証の推奨設定）を追記。 |
| 2026-08-08 | テストファイル `test_main.py`（10件）・`test_conftest.py`（1件）を新設。フロントエンド JS に `node:test` によるユニットテスト（11件）を追加。テスト件数: 211 → 222 件（pytest）+ 11件（node:test）（§13.2, §13.5）。 |
| 2026-08-08 | v2.2.0 リリース後の深掘りセキュリティレビューで [S-4] `CsrfMiddleware` の Referer 検証に部分文字列一致の脆弱性を発見・修正: `host in referer` 判定だと `https://attacker.example/<host>/evil-page` のような Referer で CSRF 保護をバイパスできたため、`urlparse(referer).netloc` による厳密なホスト比較に変更（§11.4）。あわせて [O-4] `Strict-Transport-Security` ヘッダーを追加（HTTPS 終端をリバースプロキシに委ねる構成を見据えた予防的対応。§11.1）。pip-audit で requirements.txt / requirements-dev.txt の既知脆弱性ゼロを確認。テスト1件追加（§13.5、合計223件）。v2.2.1 としてリリース。 |
| 2026-08-08 | Dependabot PR（fastapi 0.139.0→0.141.1 ほか GitHub Actions 更新）マージ後、依存関係を再点検。PyPI 最新版に追随していなかった `uvicorn` 0.52.0→0.52.1・`alembic` 1.18.5→1.19.0 を更新し、直接依存パッケージ全てが最新版に追随していることを確認。pip-audit で既知脆弱性ゼロを再確認。Docker ベースイメージ（`python:3.14-slim`）を `docker pull` で最新化した上で `--no-cache --pull` によりイメージを再ビルドし、コンテナ内のバージョンとセキュリティヘッダー・CSRF 保護・`/docs` 非公開の動作を確認。v2.2.2 としてリリース。 |
