import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir = path.join(root, "outputs", "pilot_v0.1");
const outputPath = path.join(outputDir, "manual_scoring_selected_001_009_012_017_020_025.xlsx");

const selectedTaskIds = [
  "easy_heat_1d_dirichlet_001",
  "medium_heat_inverse_alpha_009",
  "medium_wave_sparse_sensors_012",
  "hard_cahn_hilliard_017",
  "hard_helmholtz_high_frequency_020",
  "hard_plus_mhd_divergence_025",
];

const facetOrder = [
  ["Problem Formalization", "问题形式化", "problem_formalization"],
  ["Physics Constraints", "物理约束", "physics_constraints"],
  ["Model Choice", "模型选择", "model_choice"],
  ["Training Strategy", "训练策略", "training_strategy"],
  ["Validation Failure Risks", "验证与失败风险", "validation_failure_risks"],
];

const modelFiles = [
  {
    display: "DeepSeek-V4-Flash",
    original: "deepseek-ai/DeepSeek-V4-Flash",
    path: "runs/pilot_v0.1/normalized/deepseek-ai_DeepSeek-V4-Flash__canonical_v0.1.jsonl",
  },
  {
    display: "GPT-5.5-Thinking",
    original: "Open-ai/GPT-5.5-Thinking",
    path: "runs/pilot_v0.1/normalized/Open-ai_GPT-5.5-Thinking__canonical_v0.1.jsonl",
  },
  {
    display: "Kimi-K2.6",
    original: "Pro/moonshotai/Kimi-K2.6",
    path: "runs/pilot_v0.1/normalized/Pro_moonshotai_Kimi-K2.6__canonical_v0.1.jsonl",
  },
  {
    display: "GLM-4.7",
    original: "Pro/zai-org/GLM-4.7",
    path: "runs/pilot_v0.1/normalized/Pro_zai-org_GLM-4.7__canonical_v0.1.jsonl",
  },
];

const headers = [
  "问题ID",
  "难度",
  "领域",
  "任务类型",
  "PDE/系统",
  "题面英文",
  "题面中文",
  "评价角度",
  "评价角度英文",
  "模型",
  "模型原名",
  "模型回答英文",
  "模型回答中文",
  "参考答案/要点",
  "我的初步看法",
  "评分标准",
  "你的评分0-2",
  "错误标签",
  "备注",
];

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let inQuotes = false;
  const normalized = text.replace(/^\uFEFF/, "");
  for (let i = 0; i < normalized.length; i += 1) {
    const ch = normalized[i];
    const next = normalized[i + 1];
    if (inQuotes) {
      if (ch === '"' && next === '"') {
        field += '"';
        i += 1;
      } else if (ch === '"') {
        inQuotes = false;
      } else {
        field += ch;
      }
      continue;
    }
    if (ch === '"') {
      inQuotes = true;
    } else if (ch === ",") {
      row.push(field);
      field = "";
    } else if (ch === "\n") {
      row.push(field);
      rows.push(row);
      row = [];
      field = "";
    } else if (ch !== "\r") {
      field += ch;
    }
  }
  if (field.length || row.length) {
    row.push(field);
    rows.push(row);
  }
  return rows;
}

function rowsToObjects(rows) {
  const header = rows[0];
  return rows.slice(1).filter((row) => row.length && row.some(Boolean)).map((row) => {
    const out = {};
    for (let i = 0; i < header.length; i += 1) {
      out[header[i]] = row[i] ?? "";
    }
    return out;
  });
}

async function readJsonl(relativePath) {
  const text = await fs.readFile(path.join(root, relativePath), "utf8");
  return text.split(/\r?\n/).filter(Boolean).map((line) => JSON.parse(line));
}

function key(parts) {
  return parts.join("\u001F");
}

function makeAutoReview(text, facetId) {
  const lowered = String(text ?? "").toLowerCase();
  const cueSets = {
    problem_formalization: ["known", "unknown", "parameter", "domain", "geometry", "field", "forward", "inverse", "variable", "identify"],
    physics_constraints: ["pde", "residual", "equation", "initial", "boundary", "dirichlet", "neumann", "periodic", "constraint", "conservation", "divergence", "incompressible", "mass"],
    model_choice: ["pinn", "physics-informed", "neural", "mlp", "operator", "fourier", "siren", "architecture", "network", "domain decomposition"],
    training_strategy: ["loss", "residual", "data", "initial", "boundary", "sampling", "collocation", "optimizer", "adam", "l-bfgs", "weight", "normalize", "adaptive"],
    validation_failure_risks: ["validate", "validation", "residual", "error", "compare", "risk", "failure", "identifiability", "conservation", "divergence", "stability", "benchmark"],
  };
  const cues = (cueSets[facetId] ?? []).filter((cue) => lowered.includes(cue));
  const shown = cues.slice(0, 10).join("、");
  return shown
    ? `初步看法：回答中出现了这些关键线索：${shown}；这只是阅读辅助，不是自动评分。`
    : "初步看法：未检测到明显关键线索；这只是阅读辅助，不是自动评分。";
}

function colLetter(indexOneBased) {
  let n = indexOneBased;
  let out = "";
  while (n > 0) {
    const rem = (n - 1) % 26;
    out = String.fromCharCode(65 + rem) + out;
    n = Math.floor((n - 1) / 26);
  }
  return out;
}

const scoringCsv = await fs.readFile(
  path.join(root, "scores/pilot_v0.1/manual_scoring_same_task_models_bilingual_v0.1.csv"),
  "utf8",
);
const scoringRows = rowsToObjects(parseCsv(scoringCsv));
const scoringSelected = scoringRows.filter((row) => selectedTaskIds.includes(row["问题ID"]));

const metadataByTask = new Map();
const scoringByTaskFacet = new Map();
const answerCnByTaskFacetModel = new Map();
for (const row of scoringSelected) {
  const taskId = row["问题ID"];
  if (!metadataByTask.has(taskId)) {
    metadataByTask.set(taskId, {
      difficulty: row["难度"],
      domain: row["领域"],
      taskType: row["任务类型"],
      pdeSystem: row["PDE/系统"],
      problemEn: row["题面英文"],
      problemCn: row["题面中文"],
    });
  }
  const facetEn = row["评价角度英文"];
  const taskFacetKey = key([taskId, facetEn]);
  if (!scoringByTaskFacet.has(taskFacetKey)) {
    scoringByTaskFacet.set(taskFacetKey, {
      facetCn: row["评价角度"],
      reference: row["参考答案/要点"],
      standard: row["评分标准"],
    });
  }
  answerCnByTaskFacetModel.set(
    key([taskId, facetEn, row["模型原名"]]),
    row["模型回答中文"],
  );
}

const normalizedByModel = new Map();
for (const modelFile of modelFiles) {
  const records = await readJsonl(modelFile.path);
  const byTask = new Map();
  for (const record of records) {
    if (selectedTaskIds.includes(record.id)) {
      byTask.set(record.id, record);
    }
  }
  normalizedByModel.set(modelFile.original, byTask);
}

const bodyRows = [];
for (const taskId of selectedTaskIds) {
  const meta = metadataByTask.get(taskId);
  if (!meta) throw new Error(`Missing scoring metadata for ${taskId}`);

  for (const [facetEn, facetCn, facetId] of facetOrder) {
    const facetInfo = scoringByTaskFacet.get(key([taskId, facetEn]));
    if (!facetInfo) throw new Error(`Missing scoring metadata for ${taskId} / ${facetEn}`);

    for (const model of modelFiles) {
      const modelRecord = normalizedByModel.get(model.original)?.get(taskId);
      if (!modelRecord) throw new Error(`Missing normalized answer for ${model.original} / ${taskId}`);
      const answer = modelRecord.answer?.[facetEn] ?? "";
      bodyRows.push([
        taskId,
        meta.difficulty,
        meta.domain,
        meta.taskType,
        meta.pdeSystem,
        meta.problemEn,
        meta.problemCn,
        facetCn,
        facetEn,
        model.display,
        model.original,
        answer,
        answerCnByTaskFacetModel.get(key([taskId, facetEn, model.original])) ?? "",
        facetInfo.reference,
        makeAutoReview(answer, facetId),
        facetInfo.standard,
        null,
        null,
        null,
      ]);
    }
  }
}

if (bodyRows.length !== selectedTaskIds.length * modelFiles.length * facetOrder.length) {
  throw new Error(`Unexpected row count: ${bodyRows.length}`);
}

const workbook = Workbook.create();
const scoringSheet = workbook.worksheets.getOrAdd("人工评分", { renameFirstIfOnlyNewSpreadsheet: true });
scoringSheet.showGridLines = false;
const matrix = [headers, ...bodyRows];
const lastCol = colLetter(headers.length);
const lastRow = matrix.length;
scoringSheet.getRange(`A1:${lastCol}${lastRow}`).values = matrix;

scoringSheet.getRange(`A1:${lastCol}1`).format = {
  fill: "#1F4E79",
  font: { bold: true, color: "#FFFFFF" },
  horizontalAlignment: "center",
  verticalAlignment: "center",
  wrapText: true,
};
scoringSheet.getRange(`A2:${lastCol}${lastRow}`).format = {
  verticalAlignment: "top",
  wrapText: true,
};
scoringSheet.getRange(`Q1:S${lastRow}`).format = {
  fill: "#FFF2CC",
  verticalAlignment: "top",
  wrapText: true,
};
scoringSheet.getRange(`Q2:Q${lastRow}`).dataValidation = {
  rule: { type: "list", values: ["0", "0.5", "1", "1.5", "2"] },
};

const widthsPx = [
  210, 70, 130, 165, 175, 380, 380, 110, 130, 140,
  190, 520, 520, 440, 360, 430, 95, 150, 240,
];
for (let i = 0; i < widthsPx.length; i += 1) {
  const col = colLetter(i + 1);
  scoringSheet.getRange(`${col}:${col}`).format.columnWidthPx = widthsPx[i];
}
scoringSheet.getRange(`A1:${lastCol}1`).format.rowHeightPx = 38;
scoringSheet.getRange(`A2:${lastCol}${lastRow}`).format.rowHeightPx = 112;
scoringSheet.freezePanes.freezeRows(1);
scoringSheet.freezePanes.freezeColumns(3);
const scoringTable = scoringSheet.tables.add(`A1:${lastCol}${lastRow}`, true, "ManualScoringRows");
scoringTable.style = "TableStyleMedium2";
scoringTable.showFilterButton = true;

const guideSheet = workbook.worksheets.add("说明");
guideSheet.showGridLines = false;
guideSheet.getRange("A1:D1").values = [["人工评分表说明", "", "", ""]];
guideSheet.mergeCells("A1:D1");
guideSheet.getRange("A1:D1").format = {
  fill: "#1F4E79",
  font: { bold: true, color: "#FFFFFF", size: 15 },
  horizontalAlignment: "center",
};
guideSheet.getRange("A3:B8").values = [
  ["任务数量", selectedTaskIds.length],
  ["模型数量", modelFiles.length],
  ["Rubric 数量", facetOrder.length],
  ["评分行数", bodyRows.length],
  ["评分列", "你的评分0-2、错误标签、备注"],
  ["建议", "先按评价角度筛选，再在同一题目下横向比较四个模型。"],
];
guideSheet.getRange("A10:B15").values = [
  ["0", "缺失、错误或无法评分"],
  ["0.5", "有少量相关内容但关键缺陷明显"],
  ["1", "方向基本正确但遗漏重要要点"],
  ["1.5", "较完整，仍有局部缺失或风险"],
  ["2", "完整、准确、贴合任务特异性要求"],
  ["空白", "尚未人工评分"],
];
guideSheet.getRange("D3:E8").values = selectedTaskIds.map((taskId) => [taskId, metadataByTask.get(taskId)?.pdeSystem ?? ""]);
guideSheet.getRange("G3:H6").values = modelFiles.map((model) => [model.display, model.original]);
guideSheet.getRange("A3:H15").format = { wrapText: true, verticalAlignment: "top" };
guideSheet.getRange("A3:A8").format = { font: { bold: true }, fill: "#D9EAF7" };
guideSheet.getRange("A10:A15").format = { font: { bold: true }, fill: "#FFF2CC" };
guideSheet.getRange("D2:E2").values = [["选中题目", "PDE/系统"]];
guideSheet.getRange("G2:H2").values = [["模型", "模型原名"]];
guideSheet.getRange("D2:E2").format = { fill: "#D9EAF7", font: { bold: true } };
guideSheet.getRange("G2:H2").format = { fill: "#D9EAF7", font: { bold: true } };
for (const range of ["A:A", "B:B", "D:D", "E:E", "G:G", "H:H"]) {
  guideSheet.getRange(range).format.columnWidthPx = range === "B:B" || range === "E:E" || range === "H:H" ? 300 : 170;
}

const scoreSummarySheet = workbook.worksheets.add("评分进度");
scoreSummarySheet.showGridLines = false;
scoreSummarySheet.getRange("A1:F1").values = [["问题ID", "评分行数", "已评分", "未评分", "完成率", "平均分"]];
scoreSummarySheet.getRange("A1:F1").format = {
  fill: "#1F4E79",
  font: { bold: true, color: "#FFFFFF" },
  horizontalAlignment: "center",
};
const summaryTaskRows = selectedTaskIds.map((taskId) => [taskId]);
const summaryFormulaRows = selectedTaskIds.map((_taskId, idx) => {
  const rowNum = idx + 2;
  return [
    `=COUNTIF('人工评分'!$A$2:$A$${lastRow},A${rowNum})`,
    `=SUMPRODUCT(('人工评分'!$A$2:$A$${lastRow}=A${rowNum})*ISNUMBER('人工评分'!$Q$2:$Q$${lastRow})*('人工评分'!$Q$2:$Q$${lastRow}>=0)*('人工评分'!$Q$2:$Q$${lastRow}<=2))`,
    `=B${rowNum}-C${rowNum}`,
    `=IF(B${rowNum}=0,"",C${rowNum}/B${rowNum})`,
    `=IF(C${rowNum}=0,"",SUMPRODUCT(('人工评分'!$A$2:$A$${lastRow}=A${rowNum})*ISNUMBER('人工评分'!$Q$2:$Q$${lastRow})*'人工评分'!$Q$2:$Q$${lastRow})/C${rowNum})`,
  ];
});
scoreSummarySheet.getRange(`A2:A${selectedTaskIds.length + 1}`).values = summaryTaskRows;
scoreSummarySheet.getRange(`B2:F${selectedTaskIds.length + 1}`).formulas = summaryFormulaRows;
scoreSummarySheet.getRange(`B2:D${selectedTaskIds.length + 1}`).format.numberFormat = "0";
scoreSummarySheet.getRange(`E2:E${selectedTaskIds.length + 1}`).format.numberFormat = "0%";
scoreSummarySheet.getRange(`F2:F${selectedTaskIds.length + 1}`).format.numberFormat = "0.00";
scoreSummarySheet.getRange("A:F").format.columnWidthPx = 155;
scoreSummarySheet.freezePanes.freezeRows(1);
const progressTable = scoreSummarySheet.tables.add(`A1:F${selectedTaskIds.length + 1}`, true, "ScoringProgress");
progressTable.style = "TableStyleMedium4";

const topCheck = await workbook.inspect({
  kind: "table",
  range: "人工评分!A1:S8",
  include: "values,formulas",
  tableMaxRows: 8,
  tableMaxCols: 19,
  tableMaxCellChars: 120,
});
console.log(topCheck.ndjson);

const errorCheck = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
});
console.log(errorCheck.ndjson);

await workbook.render({ sheetName: "人工评分", range: "A1:S12", scale: 1, format: "png" });
await workbook.render({ sheetName: "说明", range: "A1:H15", scale: 1, format: "png" });
await workbook.render({ sheetName: "评分进度", range: "A1:F8", scale: 1, format: "png" });

await fs.mkdir(outputDir, { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(JSON.stringify({ outputPath, rows: bodyRows.length, tasks: selectedTaskIds.length, models: modelFiles.length }));
