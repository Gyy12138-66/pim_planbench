import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const outputDir = path.join(root, "outputs", "scoring_v0.3");
const outputPath = path.join(outputDir, "manual_scoring_selected_001_009_012_017_020_025_v0.3.xlsx");

const benchmarkContract = {
  publicTasks: "dataset/tasks_public_v0.3.jsonl",
  privateReferences: "dataset/references_private_v0.3.jsonl",
  promptSetting: "canonical_v0.1",
  rubric: "docs/rubric_v0.3.md",
  scoreScale: "0-5 per facet; 25 points per task",
};

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
  "任务ID",
  "难度",
  "领域",
  "任务类型",
  "PDE/系统",
  "题面英文",
  "评价角度",
  "评价角度英文",
  "Facet ID",
  "模型",
  "模型原名",
  "模型回答",
  "私有参考要点",
  "评分辅助",
  "评分标准0-5",
  "你的评分0-5",
  "错误标签",
  "备注",
];

const rubricStandards = {
  problem_formalization:
    "0=无可用形式化；1=只复述题面；2=识别部分变量/目标但有重大遗漏；3=基本正确但不完整；4=明确区分未知量、已知量、数据、域和任务目标；5=完整精确，并在不编造条件的前提下标出缺失规格。",
  physics_constraints:
    "0=遗漏或写错核心物理约束；1=只泛泛说满足 PDE；2=包含部分约束但漏 IC/BC/观测/特殊约束；3=主要 residual 与条件基本正确；4=明确给出 residual、作用区域、IC/BC/观测和物理假设；5=进一步识别兼容性、守恒、散度、变系数、正则性等任务特异要求。",
  model_choice:
    "0=无合适模型；1=泛称 NN/PINN；2=模型可行但理由弱；3=模型类别、输入输出和基本理由正确；4=架构与 PDE 类型、数据、导数、约束和正/反问题匹配；5=能针对高频、刚性、守恒、多尺度、复杂几何或可辨识性做任务感知选择。",
  training_strategy:
    "0=无可用训练方案；1=只泛称训练/最小化误差；2=有部分 loss 但漏关键项；3=包含 PDE、IC/BC/数据 loss、采样和优化；4=含归一化、Adam+L-BFGS、loss balancing、稳定性或监控；5=针对刚性、高频、长时程、边界层、多尺度、inverse/noisy 等困难给出具体训练策略。",
  validation_failure_risks:
    "0=无验证或风险分析；1=泛泛说检查精度；2=有部分验证但不任务特异；3=包含参考解/held-out/residual/IC-BC 检查和常见 PINN 风险；4=包含任务特异物理一致性指标与失败模式；5=深入说明不可验证内容、可辨识性、缺失条件、高频/守恒/散度/刚性等细节风险。",
};

async function readJsonl(relativePath) {
  const fullPath = path.join(root, relativePath);
  const text = await fs.readFile(fullPath, "utf8");
  return text
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line, index) => {
      try {
        return JSON.parse(line);
      } catch (error) {
        throw new Error(`Invalid JSONL at ${relativePath}:${index + 1}: ${error.message}`);
      }
    });
}

function byId(rows) {
  return new Map(rows.map((row) => [row.id, row]));
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

function formatValue(value) {
  if (value === undefined || value === null || value === "") return "";
  if (typeof value === "string") return value;
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (Array.isArray(value)) return value.map(formatValue).filter(Boolean).join("; ");
  if (typeof value === "object") {
    return Object.entries(value)
      .map(([key, item]) => {
        const formatted = formatValue(item);
        return formatted ? `${key}: ${formatted}` : "";
      })
      .filter(Boolean)
      .join(" | ");
  }
  return String(value);
}

function capRulesForFacet(reference, facetId) {
  return (reference.facet_cap_rules ?? [])
    .filter((rule) => Array.isArray(rule.affected_facets) && rule.affected_facets.includes(facetId))
    .map((rule) => `${rule.condition} => max ${rule.max_score}. ${rule.rationale ?? ""}`);
}

function referenceForFacet(reference, facetId) {
  const critical = reference.critical_points?.[facetId] ?? [];
  const capRules = capRulesForFacet(reference, facetId);
  const pieces = [];

  if (critical.length) pieces.push(`关键点: ${formatValue(critical)}`);

  if (facetId === "problem_formalization") {
    pieces.push(`变量: ${formatValue(reference.variables)}`);
    pieces.push(`已知参数: ${formatValue(reference.known_parameters)}`);
    pieces.push(`未知量: ${formatValue(reference.unknowns)}`);
    pieces.push(`域/参数: ${formatValue(reference.domain_spec)} ${formatValue(reference.parameter_values)}`.trim());
  } else if (facetId === "physics_constraints") {
    pieces.push(`Canonical PDE: ${formatValue(reference.canonical_pde)}`);
    pieces.push(`约束: ${formatValue(reference.constraints)}`);
    pieces.push(`参考条件: ${formatValue(reference.reference_conditions)}`);
  } else if (facetId === "model_choice") {
    pieces.push(`可接受模型: ${formatValue(reference.acceptable_model_choices)}`);
  } else if (facetId === "training_strategy") {
    pieces.push(`期望 loss: ${formatValue(reference.expected_loss_terms)}`);
    pieces.push(`期望训练策略: ${formatValue(reference.expected_training_strategy)}`);
  } else if (facetId === "validation_failure_risks") {
    pieces.push(`期望验证: ${formatValue(reference.expected_validation)}`);
    pieces.push(`Failure traps: ${formatValue(reference.failure_traps)}`);
  }

  if (reference.scoring_note) pieces.push(`评分提醒: ${reference.scoring_note}`);
  if (capRules.length) pieces.push(`Facet cap rules: ${formatValue(capRules)}`);

  return pieces.filter(Boolean).join("\n");
}

function makeAutoReview(answer, facetId, normalizedRecord) {
  const lowered = String(answer ?? "").toLowerCase();
  const cueSets = {
    problem_formalization: ["known", "unknown", "parameter", "domain", "geometry", "field", "forward", "inverse", "variable", "identify", "missing"],
    physics_constraints: ["pde", "residual", "equation", "initial", "boundary", "dirichlet", "neumann", "periodic", "constraint", "conservation", "divergence", "incompressible", "mass"],
    model_choice: ["pinn", "physics-informed", "neural", "mlp", "operator", "fourier", "siren", "architecture", "network", "domain decomposition", "weak"],
    training_strategy: ["loss", "residual", "data", "initial", "boundary", "sampling", "collocation", "optimizer", "adam", "l-bfgs", "weight", "normalize", "adaptive"],
    validation_failure_risks: ["validate", "validation", "residual", "error", "compare", "risk", "failure", "identifiability", "conservation", "divergence", "stability", "reference"],
  };
  const cues = (cueSets[facetId] ?? []).filter((cue) => lowered.includes(cue));
  const schemaNote = normalizedRecord?.schema_valid === false
    ? `Schema invalid: ${formatValue(normalizedRecord.missing_section_keys ?? normalizedRecord.parse_error)}`
    : "Schema valid.";
  const cueNote = cues.length
    ? `初步线索: ${cues.slice(0, 12).join("、")}.`
    : "初步线索: 未检测到明显关键词.";
  return `${schemaNote} ${cueNote} 这只是阅读辅助，不是自动评分。`;
}

const tasksById = byId(await readJsonl(benchmarkContract.publicTasks));
const referencesById = byId(await readJsonl(benchmarkContract.privateReferences));

const normalizedByModel = new Map();
for (const modelFile of modelFiles) {
  const records = await readJsonl(modelFile.path);
  const byTask = new Map();
  for (const record of records) {
    if (selectedTaskIds.includes(record.id)) byTask.set(record.id, record);
  }
  normalizedByModel.set(modelFile.original, byTask);
}

const bodyRows = [];
for (const taskId of selectedTaskIds) {
  const task = tasksById.get(taskId);
  const reference = referencesById.get(taskId);
  if (!task) throw new Error(`Missing public task: ${taskId}`);
  if (!reference) throw new Error(`Missing private reference: ${taskId}`);

  for (const [facetEn, facetCn, facetId] of facetOrder) {
    const referenceText = referenceForFacet(reference, facetId);
    for (const model of modelFiles) {
      const modelRecord = normalizedByModel.get(model.original)?.get(taskId);
      if (!modelRecord) throw new Error(`Missing normalized answer for ${model.original} / ${taskId}`);
      const answer = modelRecord.answer?.[facetEn] ?? "";
      bodyRows.push([
        taskId,
        task.difficulty ?? reference.public_metadata?.difficulty ?? "",
        task.domain ?? reference.public_metadata?.domain ?? "",
        task.task_type ?? reference.public_metadata?.task_type ?? "",
        task.pde_system ?? reference.public_metadata?.pde_system ?? "",
        task.problem ?? "",
        facetCn,
        facetEn,
        facetId,
        model.display,
        model.original,
        answer,
        referenceText,
        makeAutoReview(answer, facetId, modelRecord),
        rubricStandards[facetId],
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
const scoreCol = colLetter(headers.indexOf("你的评分0-5") + 1);

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
scoringSheet.getRange(`${scoreCol}1:${lastCol}${lastRow}`).format = {
  fill: "#FFF2CC",
  verticalAlignment: "top",
  wrapText: true,
};
scoringSheet.getRange(`${scoreCol}2:${scoreCol}${lastRow}`).dataValidation = {
  rule: { type: "list", values: ["0", "0.5", "1", "1.5", "2", "2.5", "3", "3.5", "4", "4.5", "5"] },
};

const widthsPx = [
  215, 70, 130, 165, 190, 440, 110, 145, 145, 140,
  195, 560, 520, 380, 460, 95, 160, 260,
];
for (let i = 0; i < widthsPx.length; i += 1) {
  scoringSheet.getRange(`${colLetter(i + 1)}:${colLetter(i + 1)}`).format.columnWidthPx = widthsPx[i];
}
scoringSheet.getRange(`A1:${lastCol}1`).format.rowHeightPx = 40;
scoringSheet.getRange(`A2:${lastCol}${lastRow}`).format.rowHeightPx = 128;
scoringSheet.freezePanes.freezeRows(1);
scoringSheet.freezePanes.freezeColumns(3);
const scoringTable = scoringSheet.tables.add(`A1:${lastCol}${lastRow}`, true, "ManualScoringRowsV02");
scoringTable.style = "TableStyleMedium2";
scoringTable.showFilterButton = true;

const guideSheet = workbook.worksheets.add("说明");
guideSheet.showGridLines = false;
guideSheet.getRange("A1:F1").values = [["PIM-PlanBench 人工评分表 v0.2", "", "", "", "", ""]];
guideSheet.mergeCells("A1:F1");
guideSheet.getRange("A1:F1").format = {
  fill: "#1F4E79",
  font: { bold: true, color: "#FFFFFF", size: 15 },
  horizontalAlignment: "center",
};
guideSheet.getRange("A3:B10").values = [
  ["Public tasks", benchmarkContract.publicTasks],
  ["Private references", benchmarkContract.privateReferences],
  ["Prompt setting", benchmarkContract.promptSetting],
  ["Rubric", benchmarkContract.rubric],
  ["Score scale", benchmarkContract.scoreScale],
  ["任务数量", selectedTaskIds.length],
  ["模型数量", modelFiles.length],
  ["评分行数", bodyRows.length],
];
guideSheet.getRange("A12:B18").values = [
  ["0", "缺失、错误或无法评分"],
  ["1", "有少量相关内容但关键缺陷明显"],
  ["2", "方向部分正确但遗漏重要要点"],
  ["3", "基本正确，仍偏通用或不完整"],
  ["4", "较完整、任务贴合，有少量缺失"],
  ["5", "完整、准确、任务特异、可执行，并正确处理缺失信息"],
  ["空白", "尚未人工评分"],
];
guideSheet.getRange("D3:E8").values = selectedTaskIds.map((taskId) => {
  const task = tasksById.get(taskId);
  return [taskId, task?.pde_system ?? ""];
});
guideSheet.getRange("D2:E2").values = [["选中题目", "PDE/系统"]];
guideSheet.getRange("D11:F14").values = modelFiles.map((model) => [model.display, model.original, model.path]);
guideSheet.getRange("D10:F10").values = [["模型", "模型原名", "Normalized file"]];
guideSheet.getRange("A3:F18").format = { wrapText: true, verticalAlignment: "top" };
guideSheet.getRange("A3:A10").format = { font: { bold: true }, fill: "#D9EAF7" };
guideSheet.getRange("A12:A18").format = { font: { bold: true }, fill: "#FFF2CC" };
guideSheet.getRange("D2:E2").format = { fill: "#D9EAF7", font: { bold: true } };
guideSheet.getRange("D10:F10").format = { fill: "#D9EAF7", font: { bold: true } };
for (const range of ["A:A", "B:B", "D:D", "E:E", "F:F"]) {
  guideSheet.getRange(range).format.columnWidthPx = range === "B:B" || range === "E:E" || range === "F:F" ? 360 : 170;
}

const progressSheet = workbook.worksheets.add("评分进度");
progressSheet.showGridLines = false;
progressSheet.getRange("A1:F1").values = [["任务ID", "评分行数", "已评分", "未评分", "完成率", "平均分"]];
progressSheet.getRange("A1:F1").format = {
  fill: "#1F4E79",
  font: { bold: true, color: "#FFFFFF" },
  horizontalAlignment: "center",
};
const summaryTaskRows = selectedTaskIds.map((taskId) => [taskId]);
const summaryFormulaRows = selectedTaskIds.map((_taskId, idx) => {
  const rowNum = idx + 2;
  return [
    `=COUNTIF('人工评分'!$A$2:$A$${lastRow},A${rowNum})`,
    `=SUMPRODUCT(('人工评分'!$A$2:$A$${lastRow}=A${rowNum})*ISNUMBER('人工评分'!$${scoreCol}$2:$${scoreCol}$${lastRow})*('人工评分'!$${scoreCol}$2:$${scoreCol}$${lastRow}>=0)*('人工评分'!$${scoreCol}$2:$${scoreCol}$${lastRow}<=5))`,
    `=B${rowNum}-C${rowNum}`,
    `=IF(B${rowNum}=0,"",C${rowNum}/B${rowNum})`,
    `=IF(C${rowNum}=0,"",SUMPRODUCT(('人工评分'!$A$2:$A$${lastRow}=A${rowNum})*ISNUMBER('人工评分'!$${scoreCol}$2:$${scoreCol}$${lastRow})*'人工评分'!$${scoreCol}$2:$${scoreCol}$${lastRow})/C${rowNum})`,
  ];
});
progressSheet.getRange(`A2:A${selectedTaskIds.length + 1}`).values = summaryTaskRows;
progressSheet.getRange(`B2:F${selectedTaskIds.length + 1}`).formulas = summaryFormulaRows;
progressSheet.getRange(`B2:D${selectedTaskIds.length + 1}`).format.numberFormat = "0";
progressSheet.getRange(`E2:E${selectedTaskIds.length + 1}`).format.numberFormat = "0%";
progressSheet.getRange(`F2:F${selectedTaskIds.length + 1}`).format.numberFormat = "0.00";
progressSheet.getRange("A:F").format.columnWidthPx = 155;
progressSheet.freezePanes.freezeRows(1);
const progressTable = progressSheet.tables.add(`A1:F${selectedTaskIds.length + 1}`, true, "ScoringProgressV02");
progressTable.style = "TableStyleMedium4";

const topCheck = await workbook.inspect({
  kind: "table",
  range: "人工评分!A1:R8",
  include: "values,formulas",
  tableMaxRows: 8,
  tableMaxCols: 18,
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

await workbook.render({ sheetName: "人工评分", range: "A1:R12", scale: 1, format: "png" });
await workbook.render({ sheetName: "说明", range: "A1:F18", scale: 1, format: "png" });
await workbook.render({ sheetName: "评分进度", range: "A1:F8", scale: 1, format: "png" });

await fs.mkdir(outputDir, { recursive: true });
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(JSON.stringify({
  outputPath,
  rows: bodyRows.length,
  tasks: selectedTaskIds.length,
  models: modelFiles.length,
  scoreScale: benchmarkContract.scoreScale,
}));
