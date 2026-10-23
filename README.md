# MOODID.

MELONADE LAB / PROJECT 03 — 좋아하는 감각을 모아 나만의 미감을 발견하는 서비스.

## 기능
- 12가지 감각 카테고리와 96개 이미지 선택지, 카테고리별 최대 3개 중복 선택
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
- `assets/options/`: 질문용 생성 이미지 96장
- `assemble.py`: Worker 생성 및 AI API 처리

Pinterest 이미지는 공식 임베드로 표시하며 외부 콘텐츠는 해당 출처의 권리를 따릅니다.

Instagram: [@melonade.lab](https://www.instagram.com/melonade.lab/)
