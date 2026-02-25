const {
  Document,
  Packer,
  Paragraph,
  TextRun,
  Table,
  TableRow,
  TableCell,
  HeadingLevel,
  AlignmentType,
  BorderStyle,
  WidthType,
  ShadingType,
  LevelFormat,
  PageNumber,
  PageNumberElement,
  Header,
  Footer,
  TabStopType,
  TabStopPosition,
} = require("docx");
const fs = require("fs");

// ── 공통 스타일 ──────────────────────────────
const BRAND_BLUE = "1A4A8A";
const BRAND_DARK = "0D2240";
const ACCENT_CYAN = "007BB5";
const LIGHT_BG = "E8F0F8";
const HEADER_BG = "1A4A8A";
const ROW_ALT = "F0F5FB";
const ROW_WHITE = "FFFFFF";
const WARN_YELLOW = "FFF8E0";
const TEXT_MAIN = "1A1A2E";
const TEXT_GRAY = "4A5568";

const border = { style: BorderStyle.SINGLE, size: 1, color: "C5D5E8" };
const borders = { top: border, bottom: border, left: border, right: border };
const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = {
  top: noBorder,
  bottom: noBorder,
  left: noBorder,
  right: noBorder,
};

function cellMargins() {
  return { top: 100, bottom: 100, left: 160, right: 160 };
}

function hCell(text, width, color = HEADER_BG) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: color, type: ShadingType.CLEAR },
    margins: cellMargins(),
    children: [
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({
            text,
            bold: true,
            color: "FFFFFF",
            size: 20,
            font: "Malgun Gothic",
          }),
        ],
      }),
    ],
  });
}

function dCell(
  text,
  width,
  bgColor = ROW_WHITE,
  align = AlignmentType.LEFT,
  opts = {},
) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: bgColor, type: ShadingType.CLEAR },
    margins: cellMargins(),
    children: [
      new Paragraph({
        alignment: align,
        children: [
          new TextRun({
            text,
            size: 18,
            font: "Malgun Gothic",
            color: TEXT_MAIN,
            ...opts,
          }),
        ],
      }),
    ],
  });
}

function badgeCell(text, width, bg, textColor, bgRow = ROW_WHITE) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: { fill: bgRow, type: ShadingType.CLEAR },
    margins: cellMargins(),
    children: [
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({
            text: ` ${text} `,
            bold: true,
            size: 16,
            font: "Malgun Gothic",
            color: textColor,
          }),
        ],
      }),
    ],
  });
}

function sectionTitle(text, level = HeadingLevel.HEADING_1) {
  return new Paragraph({
    heading: level,
    spacing: { before: 320, after: 160 },
    children: [new TextRun({ text, font: "Malgun Gothic" })],
  });
}

function bodyText(text, opts = {}) {
  return new Paragraph({
    spacing: { before: 60, after: 60 },
    children: [
      new TextRun({
        text,
        size: 20,
        font: "Malgun Gothic",
        color: TEXT_MAIN,
        ...opts,
      }),
    ],
  });
}

function spacer(n = 1) {
  return Array.from(
    { length: n },
    () =>
      new Paragraph({
        children: [new TextRun("")],
        spacing: { before: 60, after: 60 },
      }),
  );
}

// ── 히스토리 데이터 ──────────────────────────
const historyRows = [
  {
    ver: "v1.0.0",
    date: "2026-02-20",
    author: "김개발",
    type: "신규",
    summary: "최초 RAG 파이프라인 모니터링 대시보드 개발",
    detail: "기본 플로우차트, 청크 뷰어, 벡터 미리보기, 처리량 차트 구현",
  },
  {
    ver: "v1.0.1",
    date: "2026-02-21",
    author: "김개발",
    type: "수정",
    summary: "사이드바 DB 엔진 선택 옵션 추가 (Pinecone, Weaviate)",
    detail: "selectbox 항목 4종 → 5종 확장, embed_model 기본값 변경",
  },
  {
    ver: "v1.0.2",
    date: "2026-02-22",
    author: "이운영",
    type: "버그수정",
    summary: "자동 새로고침 시 캐시 미해제 오류 수정",
    detail: "st.cache_data ttl=3 → ttl=5 조정, rerun() 타이밍 버그 패치",
  },
  {
    ver: "v1.1.0",
    date: "2026-02-24",
    author: "박데이터",
    type: "기능추가",
    summary: "인덱스 상태 테이블 및 샤드 모니터링 기능 추가",
    detail:
      "4개 샤드 상태(OK/REBAL) 표시, Progress Column 적용, 인덱스 크기 메트릭 추가",
  },
  {
    ver: "v1.2.0",
    date: "2026-02-25",
    author: "김개발",
    type: "기능추가",
    summary: "개발이력 문서 및 사용자 매뉴얼 Word 파일 생성 기능 추가",
    detail: "docx 라이브러리 활용, 수정이력 자동 추가 가능한 문서 템플릿 구축",
  },
];

const typeColors = {
  신규: { bg: "1A4A8A", text: "FFFFFF" },
  수정: { bg: "2E7D32", text: "FFFFFF" },
  버그수정: { bg: "C62828", text: "FFFFFF" },
  기능추가: { bg: "6A1B9A", text: "FFFFFF" },
  보안패치: { bg: "E65100", text: "FFFFFF" },
};

function buildHistoryTable(rows) {
  const COL = [900, 1100, 1000, 1000, 2600, 2760]; // total = 9360
  const headerRow = new TableRow({
    tableHeader: true,
    children: [
      hCell("버전", COL[0]),
      hCell("날짜", COL[1]),
      hCell("작성자", COL[2]),
      hCell("구분", COL[3]),
      hCell("변경 요약", COL[4]),
      hCell("상세 내용", COL[5]),
    ],
  });

  const dataRows = rows.map((r, i) => {
    const bg = i % 2 === 0 ? ROW_WHITE : ROW_ALT;
    const tc = typeColors[r.type] || { bg: "607D8B", text: "FFFFFF" };
    return new TableRow({
      children: [
        dCell(r.ver, COL[0], bg, AlignmentType.CENTER, {
          bold: true,
          color: ACCENT_CYAN,
        }),
        dCell(r.date, COL[1], bg, AlignmentType.CENTER),
        dCell(r.author, COL[2], bg, AlignmentType.CENTER),
        new TableCell({
          borders,
          width: { size: COL[3], type: WidthType.DXA },
          shading: { fill: bg, type: ShadingType.CLEAR },
          margins: cellMargins(),
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              children: [
                new TextRun({
                  text: ` ${r.type} `,
                  bold: true,
                  size: 16,
                  font: "Malgun Gothic",
                  color: tc.bg,
                }),
              ],
            }),
          ],
        }),
        dCell(r.summary, COL[4], bg),
        dCell(r.detail, COL[5], bg, AlignmentType.LEFT, { color: TEXT_GRAY }),
      ],
    });
  });

  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: COL,
    rows: [headerRow, ...dataRows],
  });
}

// ── 추가 이력 가이드 박스 ─────────────────────
function guideBox() {
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: [9360],
    rows: [
      new TableRow({
        children: [
          new TableCell({
            borders: {
              top: { style: BorderStyle.SINGLE, size: 3, color: BRAND_BLUE },
              bottom: { style: BorderStyle.SINGLE, size: 3, color: BRAND_BLUE },
              left: { style: BorderStyle.THICK, size: 12, color: ACCENT_CYAN },
              right: { style: BorderStyle.SINGLE, size: 3, color: BRAND_BLUE },
            },
            width: { size: 9360, type: WidthType.DXA },
            shading: { fill: "E8F4FB", type: ShadingType.CLEAR },
            margins: { top: 120, bottom: 120, left: 240, right: 240 },
            children: [
              new Paragraph({
                children: [
                  new TextRun({
                    text: "📌 이력 추가 방법",
                    bold: true,
                    size: 22,
                    font: "Malgun Gothic",
                    color: BRAND_BLUE,
                  }),
                ],
              }),
              new Paragraph({
                spacing: { before: 80 },
                children: [
                  new TextRun({
                    text: "수정 사항 발생 시 아래 형식으로 이력 테이블에 행을 추가하세요.",
                    size: 19,
                    font: "Malgun Gothic",
                    color: TEXT_MAIN,
                  }),
                ],
              }),
              new Paragraph({
                spacing: { before: 80 },
                children: [
                  new TextRun({
                    text: "  버전: 이전 버전의 마지막 자리 +1 (예: v1.2.0 → v1.2.1 / 주요 변경 시 v1.3.0)",
                    size: 18,
                    font: "Malgun Gothic",
                    color: TEXT_GRAY,
                  }),
                ],
              }),
              new Paragraph({
                children: [
                  new TextRun({
                    text: "  날짜: YYYY-MM-DD 형식 (예: 2026-03-01)",
                    size: 18,
                    font: "Malgun Gothic",
                    color: TEXT_GRAY,
                  }),
                ],
              }),
              new Paragraph({
                children: [
                  new TextRun({
                    text: "  구분: 신규 / 수정 / 버그수정 / 기능추가 / 보안패치 중 선택",
                    size: 18,
                    font: "Malgun Gothic",
                    color: TEXT_GRAY,
                  }),
                ],
              }),
              new Paragraph({
                children: [
                  new TextRun({
                    text: "  작성자: 변경 작업 담당자 이름 기재",
                    size: 18,
                    font: "Malgun Gothic",
                    color: TEXT_GRAY,
                  }),
                ],
              }),
            ],
          }),
        ],
      }),
    ],
  });
}

// ── 변경 이력 분류 기준표 ────────────────────
function typeGuideTable() {
  const COL2 = [1500, 4000, 3860];
  const rows = [
    ["신규", "최초 기능 또는 화면 개발", "초기 릴리즈, 새 페이지 추가"],
    ["수정", "기존 기능의 변경 또는 개선", "UI 레이아웃 변경, 설정값 수정"],
    [
      "버그수정",
      "오류 수정 및 예외처리 보완",
      "캐시 오류, Null 처리, 렌더링 오류",
    ],
    ["기능추가", "기존 화면에 새 기능 통합", "새 위젯, API 연동, 차트 추가"],
    [
      "보안패치",
      "보안 취약점 패치 및 인증 강화",
      "API Key 노출 방지, 권한 검증",
    ],
  ];
  const hRow = new TableRow({
    tableHeader: true,
    children: [
      hCell("구분", COL2[0]),
      hCell("설명", COL2[1]),
      hCell("예시", COL2[2]),
    ],
  });
  const dRows = rows.map((r, i) => {
    const bg = i % 2 === 0 ? ROW_WHITE : ROW_ALT;
    const tc = typeColors[r[0]] || { bg: "607D8B" };
    return new TableRow({
      children: [
        new TableCell({
          borders,
          width: { size: COL2[0], type: WidthType.DXA },
          shading: { fill: bg, type: ShadingType.CLEAR },
          margins: cellMargins(),
          children: [
            new Paragraph({
              alignment: AlignmentType.CENTER,
              children: [
                new TextRun({
                  text: r[0],
                  bold: true,
                  size: 18,
                  font: "Malgun Gothic",
                  color: tc.bg,
                }),
              ],
            }),
          ],
        }),
        dCell(r[1], COL2[1], bg),
        dCell(r[2], COL2[2], bg, AlignmentType.LEFT, { color: TEXT_GRAY }),
      ],
    });
  });
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: COL2,
    rows: [hRow, ...dRows],
  });
}

// ── 문서 구성 ──────────────────────────────────
const doc = new Document({
  styles: {
    default: {
      document: { run: { font: "Malgun Gothic", size: 20, color: TEXT_MAIN } },
    },
    paragraphStyles: [
      {
        id: "Heading1",
        name: "Heading 1",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 32, bold: true, font: "Malgun Gothic", color: BRAND_DARK },
        paragraph: {
          spacing: { before: 360, after: 200 },
          outlineLevel: 0,
          border: {
            bottom: {
              style: BorderStyle.SINGLE,
              size: 4,
              color: ACCENT_CYAN,
              space: 4,
            },
          },
        },
      },
      {
        id: "Heading2",
        name: "Heading 2",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 24, bold: true, font: "Malgun Gothic", color: BRAND_BLUE },
        paragraph: { spacing: { before: 280, after: 140 }, outlineLevel: 1 },
      },
      {
        id: "Heading3",
        name: "Heading 3",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: {
          size: 22,
          bold: true,
          font: "Malgun Gothic",
          color: ACCENT_CYAN,
        },
        paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2 },
      },
    ],
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: 16838, height: 11906 }, // A4 가로
          margin: { top: 1134, right: 1134, bottom: 1134, left: 1134 },
        },
      },
      headers: {
        default: new Header({
          children: [
            new Paragraph({
              tabStops: [{ type: TabStopType.RIGHT, position: 14400 }],
              border: {
                bottom: {
                  style: BorderStyle.SINGLE,
                  size: 4,
                  color: ACCENT_CYAN,
                  space: 2,
                },
              },
              children: [
                new TextRun({
                  text: "RAG Pipeline Monitor  |  개발 이력서",
                  bold: true,
                  size: 18,
                  font: "Malgun Gothic",
                  color: BRAND_BLUE,
                }),
                new TextRun({ text: "\t", size: 18 }),
                new TextRun({
                  text: "기밀 · 내부 배포용",
                  size: 16,
                  font: "Malgun Gothic",
                  color: "A0A0A0",
                }),
              ],
            }),
          ],
        }),
      },
      footers: {
        default: new Footer({
          children: [
            new Paragraph({
              tabStops: [{ type: TabStopType.RIGHT, position: 14400 }],
              border: {
                top: {
                  style: BorderStyle.SINGLE,
                  size: 2,
                  color: "C5D5E8",
                  space: 2,
                },
              },
              children: [
                new TextRun({
                  text: "© 2026 RAG Monitor Team. All rights reserved.",
                  size: 16,
                  font: "Malgun Gothic",
                  color: "A0A0A0",
                }),
                new TextRun({ text: "\t", size: 16 }),
                new TextRun({
                  text: "페이지 ",
                  size: 16,
                  font: "Malgun Gothic",
                  color: "A0A0A0",
                }),
                new PageNumberElement(),
              ],
            }),
          ],
        }),
      },
      children: [
        // ─── 표지 타이틀 ───
        ...spacer(2),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 0, after: 80 },
          children: [
            new TextRun({
              text: "RAG Pipeline Monitor",
              size: 64,
              bold: true,
              font: "Malgun Gothic",
              color: BRAND_DARK,
            }),
          ],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 0, after: 60 },
          children: [
            new TextRun({
              text: "개발 이력서 (Development History)",
              size: 32,
              font: "Malgun Gothic",
              color: ACCENT_CYAN,
            }),
          ],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 0, after: 280 },
          children: [
            new TextRun({
              text: "문서 버전: v1.2.0   |   최종 수정: 2026-02-25   |   작성팀: RAG 개발팀",
              size: 18,
              font: "Malgun Gothic",
              color: TEXT_GRAY,
            }),
          ],
        }),

        // ─── 1. 프로젝트 개요 ───
        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          children: [
            new TextRun({ text: "1. 프로젝트 개요", font: "Malgun Gothic" }),
          ],
        }),
        new Table({
          width: { size: 9360, type: WidthType.DXA },
          columnWidths: [2200, 7160],
          rows: [
            new TableRow({
              children: [hCell("항목", 2200), hCell("내용", 7160)],
            }),
            ...[
              ["프로젝트명", "RAG Pipeline Monitoring Dashboard"],
              [
                "목적",
                "벡터 DB 데이터 적재 파이프라인 실시간 모니터링 및 관리",
              ],
              [
                "사용 기술",
                "Python 3.11, Streamlit 1.32, NumPy, Pandas, FAISS",
              ],
              ["지원 DB 엔진", "FAISS, Pinecone, Weaviate, Qdrant, Chroma"],
              ["담당팀", "RAG 개발팀 (김개발, 이운영, 박데이터)"],
              ["최초 배포일", "2026-02-20"],
              ["현재 버전", "v1.2.0"],
            ].map(
              ([k, v], i) =>
                new TableRow({
                  children: [
                    dCell(
                      k,
                      2200,
                      i % 2 === 0 ? ROW_WHITE : ROW_ALT,
                      AlignmentType.LEFT,
                      { bold: true, color: BRAND_BLUE },
                    ),
                    dCell(v, 7160, i % 2 === 0 ? ROW_WHITE : ROW_ALT),
                  ],
                }),
            ),
          ],
        }),

        // ─── 2. 개발 이력 테이블 ───
        ...spacer(1),
        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          children: [
            new TextRun({
              text: "2. 개발 이력 (Change Log)",
              font: "Malgun Gothic",
            }),
          ],
        }),
        bodyText(
          "하단 표는 릴리즈 순서에 따라 기재되며, 수정 사항 발생 시 최하단에 행을 추가합니다.",
        ),
        ...spacer(1),
        buildHistoryTable(historyRows),

        // ─── 3. 이력 추가 가이드 ───
        ...spacer(1),
        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          children: [
            new TextRun({ text: "3. 이력 추가 가이드", font: "Malgun Gothic" }),
          ],
        }),
        guideBox(),
        ...spacer(1),
        new Paragraph({
          heading: HeadingLevel.HEADING_2,
          children: [
            new TextRun({ text: "3-1. 변경 구분 기준", font: "Malgun Gothic" }),
          ],
        }),
        typeGuideTable(),

        // ─── 4. 버전 정책 ───
        ...spacer(1),
        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          children: [
            new TextRun({
              text: "4. 버전 명명 정책 (Semantic Versioning)",
              font: "Malgun Gothic",
            }),
          ],
        }),
        new Table({
          width: { size: 9360, type: WidthType.DXA },
          columnWidths: [2200, 3800, 3360],
          rows: [
            new TableRow({
              children: [
                hCell("버전 자리", 2200),
                hCell("변경 기준", 3800),
                hCell("예시", 3360),
              ],
            }),
            ...[
              [
                "MAJOR (v X.0.0)",
                "아키텍처 전면 개편 또는 하위 호환 불가 변경",
                "v1.0.0 → v2.0.0",
              ],
              [
                "MINOR (v0. X .0)",
                "새 기능 추가, 기존 기능 유지",
                "v1.1.0 → v1.2.0",
              ],
              [
                "PATCH (v0.0. X )",
                "버그 수정, 소규모 UI 수정",
                "v1.2.0 → v1.2.1",
              ],
            ].map(
              ([k, v, ex], i) =>
                new TableRow({
                  children: [
                    dCell(
                      k,
                      2200,
                      i % 2 === 0 ? ROW_WHITE : ROW_ALT,
                      AlignmentType.LEFT,
                      { bold: true, color: BRAND_BLUE },
                    ),
                    dCell(v, 3800, i % 2 === 0 ? ROW_WHITE : ROW_ALT),
                    dCell(
                      ex,
                      3360,
                      i % 2 === 0 ? ROW_WHITE : ROW_ALT,
                      AlignmentType.CENTER,
                      { color: ACCENT_CYAN, bold: true },
                    ),
                  ],
                }),
            ),
          ],
        }),

        ...spacer(2),
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("/home/claude/dev_history.docx", buf);
  console.log("✅ dev_history.docx created");
});
