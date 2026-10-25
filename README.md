# MOODID.

MELONADE LAB / PROJECT 03 — 좋아하는 감각을 모아 나만의 미감을 발견하는 서비스.

## 기능
- 11가지 감각 카테고리와 88개 이미지 선택지, 카테고리별 최대 3개 중복 선택
- 고정 DB의 일관된 속성 점수 및 5색 팔레트
- Gemini 종합 미감 해석, 감각 DNA, 숨겨진 취향 연결고리
- 실제 Pinterest 핀 임베드, 탐색 검색어, 새로운 미감 추천과 피드백
- 결과 카드 저장과 브라우저 로컬 보드

## 로컬 실행
Node.js 20 이상과 Python 3을 사용합니다. npm 의존성 설치는 필요하지 않습니다.

```sh
npm run dev
```

http://localhost:4173 에서 확인합니다. 로컬 미리보기는 프런트엔드와 고정 DB 결과를 제공하며 `/api/analyze` 서버 연결은 포함하지 않습니다.

## 빌드 및 검사
```sh
npm run build
npm run validate
node scripts/check-result-engine.mjs
node scripts/check-progressive-results.mjs
node scripts/check-curiosity-cards.mjs
node scripts/check-option-images.mjs
```

`assemble.py`가 HTML·DB·이미지를 묶어 `worker/index.js`를 생성하며 배포 산출물은 `dist/server/index.js`입니다. `.openai/hosting.json`은 기존 Sites 프로젝트의 호스팅 메타데이터입니다.

## AI 연결
배포 환경의 서버 전용 secret `GEMINI_API_KEY`를 설정하세요. `.env.example`은 변수 이름 참고용이며 현재 로컬 미리보기는 `.env`를 자동으로 읽지 않습니다. 키를 브라우저 코드나 Git에 넣지 마세요. AI 연결이 지연되거나 없어도 고정 DB 결과를 먼저 표시합니다.

## 주요 소스
- `page.html`: 질문과 결과 UI
- `database.json`: 감각 선택지 및 속성
- `aesthetic-engine.js`: 점수, 팔레트, 추천 로직
- `pinterest-catalog.json`: 검증된 핀 목록
- `discoveries.json`: 새로운 미감 후보
- `assets/options/`: 질문용 생성 이미지 (현재 88개 선택지)
- `assemble.py`: Worker 생성 및 AI API 처리

Pinterest 이미지는 공식 임베드로 표시하며 외부 콘텐츠는 해당 출처의 권리를 따릅니다.

Instagram: [@melonade.lab](https://www.instagram.com/melonade.lab/)

## 결과 DB v3
- `result-reference-db.json`: 131개 결과 탐색 항목 (음악 제거 후 현재 DB 기준). 실제 Pinterest 사진이 131장이라는 뜻이 아닙니다.
- `discoveries.json`: 37개 새 취향 제안. 고정 사용자 유형이 아니라 여러 후보를 독립적으로 추천합니다.
- 복합 장면은 최소 두 선택 그룹 및 두 감각 범주가 일치해야 후보가 됩니다. 사진이 없는 탐색 항목은 기존 MOODID AI 생성 이미지를 대표 감각 예시로 표시합니다.
- 직접 연결되는 핀이 없으면 05번 원본 핀 영역은 빈 상태를 안내하며, 06번에서 감각 예시와 Pinterest 검색으로 탐색을 이어갑니다.
- AI에는 적합한 후보 최대 24개와 실제 일치 선택만 전달합니다. 제목·검색어·이미지 연결은 DB로 고정하고 AI는 연결 설명을 작성합니다.
- 검증: `node scripts/check-result-db.mjs` (88개 선택지 전체, 240개 응답 조합, 다양성·결정성·핀 조건). 새 핀은 실제 출처와 장면을 확인한 후 두 카탈로그에 함께 추가하세요.

## 안정성 점검
`npm run check`로 빌드·산출물·선택 이미지·결과 DB·AI 응답·비동기 경쟁 상태·오류 복구를 한 번에 검사합니다.

- 분석을 중단하고 다른 화면으로 이동하면 이전 응답과 캐시 쓰기를 무시합니다.
- 잘못된 저장 데이터와 잘못된 AI 응답을 검증하며 기본 DB 결과를 유지합니다.
- 최근 결과는 이 브라우저에서 이어볼 수 있습니다. 처음부터 새로 시작할 수도 있습니다.
- 공유 이미지의 각 텍스트 영역은 글자 크기를 조절하고 긴 문장을 제한합니다.
- 캐시를 먼저 확인하며 Worker 인스턴스별로 IP당 분당 6회와 동시 분석 4회 제한을 둡니다. 인스턴스가 여러 개일 때 공유되는 전역 과금 한도는 아니므로 Cloudflare 및 Gemini의 계정별 사용량 설정도 별도로 관리하세요.
- `GEMINI_MODEL` 서버 변수로 모델 ID를 변경할 수 있습니다. 기본 모델 ID는 `assemble.py`를 참고하세요. 실제 모델 사용 가능 여부와 API 키는 배포 환경에서 확인해야 합니다.
- Cloudflare 빌드 명령 `npm run check`, 배포 명령 `npx wrangler deploy`. `wrangler.jsonc`에 진입 파일을 명시했습니다.

음악 카테고리와 음악 추천은 제외했습니다. 자연 소리는 유지하며, 이전 12개 질문 결과는 선택지 ID를 기준으로 11개 감각으로 변환하고 해석을 새로 구성합니다.
