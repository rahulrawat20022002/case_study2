const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5
pres.title = "Faithful but wrong? Case Study 2";
pres.author = "Rahul Rawat";

const F = "/home/claude/case_study2/report_figs/";
const NAVY = "14213D", INK = "1B1B1B", MUTED = "5A6070", LIGHT = "EEF2F8", GOLD = "E8A317", RED = "C0392B", WHITE = "FFFFFF";
const B1C = "4A3AA7", B2C = "EB6834", AGC = "1BAF7A";
const HEAD = "Cambria", BODY = "Calibri";
const W = 13.33;

function title(s, text, sub) {
  s.addText(text, { x: 0.6, y: 0.35, w: W - 1.2, h: 0.8, fontFace: HEAD, fontSize: 32, bold: true, color: NAVY, margin: 0, isTextBox: true });
  if (sub) s.addText(sub, { x: 0.6, y: 1.1, w: W - 1.2, h: 0.45, fontFace: BODY, fontSize: 16, color: MUTED, margin: 0, isTextBox: true });
}
function footer(s, n) {
  s.addText(`Case Study 2  |  Rahul Rawat  |  SRH Hochschule Heidelberg`, { x: 0.6, y: 7.05, w: 8, h: 0.3, fontFace: BODY, fontSize: 9, color: "8A90A0", margin: 0, isTextBox: true });
  s.addText(String(n), { x: W - 1.1, y: 7.05, w: 0.5, h: 0.3, fontFace: BODY, fontSize: 9, color: "8A90A0", align: "right", margin: 0, isTextBox: true });
}
function stat(s, x, y, w, big, label, color) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h: 1.45, fill: { color: LIGHT }, line: { color: LIGHT }, rectRadius: 0.08 });
  s.addText(big, { x: x + 0.15, y: y + 0.12, w: w - 0.3, h: 0.75, fontFace: HEAD, fontSize: 36, bold: true, color: color || NAVY, margin: 0, isTextBox: true });
  s.addText(label, { x: x + 0.15, y: y + 0.85, w: w - 0.3, h: 0.5, fontFace: BODY, fontSize: 12, color: MUTED, margin: 0, isTextBox: true, valign: "top" });
}
function card(s, x, y, w, h, head, body, dot) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: WHITE }, line: { color: "D5DBE6", width: 1 }, rectRadius: 0.08,
    shadow: { type: "outer", color: "000000", opacity: 0.12, blur: 6, offset: 2, angle: 90 } });
  if (dot) s.addShape(pres.shapes.OVAL, { x: x + 0.25, y: y + 0.27, w: 0.3, h: 0.3, fill: { color: dot }, line: { color: dot } });
  s.addText(head, { x: x + (dot ? 0.7 : 0.25), y: y + 0.18, w: w - (dot ? 0.95 : 0.5), h: 0.5, fontFace: HEAD, fontSize: 17, bold: true, color: NAVY, margin: 0, isTextBox: true, valign: "middle" });
  s.addText(body, { x: x + 0.25, y: y + 0.75, w: w - 0.5, h: h - 0.9, fontFace: BODY, fontSize: 13.5, color: INK, margin: 0, isTextBox: true, valign: "top" });
}
function bullets(s, items, x, y, w, h, size, color) {
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 8 } })),
    { x, y, w, h, fontFace: BODY, fontSize: size || 15, color: color || INK, margin: 0, isTextBox: true, valign: "top" });
}
function img(s, file, x, y, w, px) { s.addImage({ path: F + file, x, y, w, h: w * px[1] / px[0] }); }
const quiet = { catAxisLabelColor: MUTED, valAxisLabelColor: MUTED, catAxisLabelFontFace: BODY, valAxisLabelFontFace: BODY, catAxisLabelFontSize: 11, valAxisLabelFontSize: 10,
  valGridLine: { color: "E3E6EC", size: 0.5 }, catGridLine: { style: "none" }, dataLabelFontFace: BODY, dataLabelFontSize: 10, dataLabelColor: INK, legendFontFace: BODY, legendFontSize: 11 };

let n = 0;
// ---------------- 1 Title
{
  const s = pres.addSlide(); n++; s.background = { color: NAVY };
  s.addText("CASE STUDY 2  |  M.Sc. DATA SCIENCE AND ANALYTICS", { x: 0.8, y: 0.8, w: 11, h: 0.4, fontFace: BODY, fontSize: 13, color: GOLD, bold: true, charSpacing: 2, margin: 0, isTextBox: true });
  s.addText("Faithful but wrong?", { x: 0.8, y: 1.6, w: 11.5, h: 1.2, fontFace: HEAD, fontSize: 54, bold: true, color: WHITE, margin: 0, isTextBox: true });
  s.addText("Evaluating RAG-based high-risk classification under the EU AI Act against an authoritative answer key",
    { x: 0.8, y: 2.85, w: 10.5, h: 1.1, fontFace: BODY, fontSize: 22, color: "CADCFC", margin: 0, isTextBox: true });
  s.addText([{ text: "Rahul Rawat", options: { bold: true, breakLine: true } }, { text: "Supervisor: Prof. Dr. Swati Chandna", options: { breakLine: true } }, { text: "SRH Hochschule Heidelberg  |  September 2026" }],
    { x: 0.8, y: 5.2, w: 8, h: 1.2, fontFace: BODY, fontSize: 15, color: WHITE, margin: 0, isTextBox: true });
  s.addNotes("Title. One sentence: this study asks whether the standard faithfulness metric for RAG systems tells you anything about whether a legal classification is actually correct.");
}
// ---------------- 2 The question
{
  const s = pres.addSlide(); n++; title(s, "The question", "RAG compliance tools are judged by how grounded they are. Is grounded the same as right?");
  card(s, 0.6, 1.9, 5.9, 2.1, "Faithfulness (RAGAS)", "Share of the answer's claims that can be traced to the retrieved passages. Needs no answer key, which is why it is so widely used.", GOLD);
  card(s, 6.85, 1.9, 5.9, 2.2, "Correctness", "Does the predicted label match the official answer? Needs a ground truth, which legal tasks rarely have.", NAVY);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 4.45, w: 12.15, h: 2.25, fill: { color: LIGHT }, line: { color: LIGHT }, rectRadius: 0.08 });
  s.addText("Two independent axes, four buckets", { x: 0.9, y: 4.6, w: 11.5, h: 0.45, fontFace: HEAD, fontSize: 18, bold: true, color: NAVY, margin: 0, isTextBox: true });
  const b = [["Right and faithful", "expected", NAVY], ["Right but unfaithful", "finding", RED], ["Faithful but wrong", "headline finding", RED], ["Wrong and unfaithful", "expected", NAVY]];
  b.forEach((t, i) => {
    const x = 0.9 + i * 2.95;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 5.2, w: 2.75, h: 1.25, fill: { color: WHITE }, line: { color: t[2] === RED ? RED : "C9D1DE", width: t[2] === RED ? 2 : 1 }, rectRadius: 0.06 });
    s.addText([{ text: t[0], options: { bold: true, breakLine: true, fontSize: 15, color: t[2] === RED ? RED : NAVY } }, { text: t[1], options: { fontSize: 12, color: MUTED } }],
      { x: x + 0.15, y: 5.28, w: 2.45, h: 1.1, fontFace: BODY, align: "center", valign: "middle", margin: 0, isTextBox: true });
  });
  footer(s, n);
  s.addNotes("Faithfulness checks grounding, not correctness. Crossing the two gives four buckets; the off-diagonal ones are the findings. The study is designed to give a real answer either way.");
}
// ---------------- 3 Task
{
  const s = pres.addSlide(); n++; title(s, "The task: Article 6 high-risk classification", "Annex III route of the EU AI Act, including the Article 6(3) filter");
  const steps = [["1", "Intended purpose", "What does the system do, for whom, with which data?"],
    ["2", "Annex III use case?", "Eight areas: biometrics, critical infrastructure, education, employment, essential services, law enforcement, migration, justice and democracy"],
    ["3", "Article 6(3) filter", "Out again if only a narrow procedural or preparatory task, or improving completed human work. Profiling always stays high-risk."],
    ["4", "Label", "high-risk  or  not-high-risk, with an explanation"]];
  steps.forEach((t, i) => {
    const x = 0.6 + i * 3.1;
    s.addShape(pres.shapes.OVAL, { x: x, y: 2.0, w: 0.75, h: 0.75, fill: { color: i === 3 ? GOLD : NAVY }, line: { color: i === 3 ? GOLD : NAVY } });
    s.addText(t[0], { x, y: 2.0, w: 0.75, h: 0.75, fontFace: HEAD, fontSize: 24, bold: true, color: WHITE, align: "center", valign: "middle", margin: 0, isTextBox: true });
    if (i < 3) s.addShape(pres.shapes.LINE, { x: x + 0.85, y: 2.375, w: 2.1, h: 0, line: { color: "B8C2D4", width: 2, endArrowType: "triangle" } });
    s.addText(t[1], { x, y: 2.95, w: 2.8, h: 0.5, fontFace: HEAD, fontSize: 17, bold: true, color: NAVY, margin: 0, isTextBox: true });
    s.addText(t[2], { x, y: 3.45, w: 2.8, h: 1.8, fontFace: BODY, fontSize: 13.5, color: INK, margin: 0, isTextBox: true, valign: "top" });
  });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 5.55, w: 12.15, h: 1.2, fill: { color: LIGHT }, line: { color: LIGHT }, rectRadius: 0.08 });
  s.addText([{ text: "Ground truth: ", options: { bold: true, color: NAVY } }, { text: "the European Commission's draft guidelines on Annex III (May 2026, frozen). Every worked example ends in an authoritative verdict, so each test input has one known correct answer. Article 6(1) product safety is out of scope." }],
    { x: 0.9, y: 5.65, w: 11.6, h: 1.0, fontFace: BODY, fontSize: 14, color: INK, margin: 0, isTextBox: true, valign: "middle" });
  footer(s, n);
  s.addNotes("The legal test in four steps. The answer key comes from the Commission's own worked examples, which is what makes a correctness axis possible at all.");
}
// ---------------- 4 Data
{
  const s = pres.addSlide(); n++; title(s, "Test set: 215 inputs with official labels", "Extracted from the worked examples; all eight Annex III areas covered");
  stat(s, 0.6, 1.8, 2.7, "215", "test inputs, one gold label each");
  stat(s, 0.6, 3.4, 2.7, "66 / 149", "high-risk / not high-risk (31% / 69%)");
  stat(s, 0.6, 5.0, 2.7, "41", "Article 6(3) filter cases, all not high-risk", GOLD);
  const areas = ["Biometrics", "Critical infra.", "Education", "Employment", "Essential services", "Law enforcement", "Migration", "Justice & democracy"];
  s.addChart(pres.charts.BAR, [
    { name: "High-risk", labels: areas, values: [14, 8, 9, 14, 21, 0, 0, 0] },
    { name: "Not high-risk", labels: areas, values: [18, 10, 19, 18, 22, 23, 23, 16] }],
    Object.assign({}, quiet, { x: 3.7, y: 1.7, w: 9.05, h: 5.1, barDir: "bar", barGrouping: "stacked", chartColors: ["2A78D6", "B9B8B2"],
      showLegend: true, legendPos: "t", showValue: true, dataLabelPosition: "ctr", dataLabelColor: WHITE, catAxisOrientation: "maxMin",
      showTitle: true, title: "Inputs per Annex III area", titleFontFace: HEAD, titleFontSize: 14, titleColor: NAVY }));
  footer(s, n);
  s.addNotes("The source has no high-risk examples for law enforcement, migration and justice, so those areas test correct rejection only. Imbalance handled by reporting precision, recall and F1 next to accuracy.");
}
// ---------------- 5 Pipeline
{
  const s = pres.addSlide(); n++; title(s, "Evaluation framework");
  img(s, "arch_detailed.png", 0.6, 1.2, 4.55, [2759, 3485]);
  const pts = [["Source split", "Worked examples become the test set; only normative text (400 chunks) goes into the retrieval corpus, so labels cannot leak through retrieval."],
    ["One shared pipeline", "Hybrid BM25 + dense retrieval (bge-base-en-v1.5, Chroma, alpha 0.5, top 5). One generator for all three systems: only the prompt changes."],
    ["Two independent axes", "Judge (Qwen2.5-72B, separate model family) scores RAGAS faithfulness; correctness is a plain lookup against the Commission label."],
    ["Reproducible", "Local models on the university GPU with pinned revisions, greedy decoding, every prompt, passage and output logged."]];
  pts.forEach((p, i) => {
    const y = 1.35 + i * 1.4;
    s.addShape(pres.shapes.OVAL, { x: 5.6, y: y + 0.05, w: 0.42, h: 0.42, fill: { color: NAVY }, line: { color: NAVY } });
    s.addText(String(i + 1), { x: 5.6, y: y + 0.05, w: 0.42, h: 0.42, fontFace: HEAD, fontSize: 15, bold: true, color: WHITE, align: "center", valign: "middle", margin: 0, isTextBox: true });
    s.addText(p[0], { x: 6.2, y, w: 6.5, h: 0.45, fontFace: HEAD, fontSize: 17, bold: true, color: NAVY, margin: 0, isTextBox: true, valign: "middle" });
    s.addText(p[1], { x: 6.2, y: y + 0.45, w: 6.5, h: 0.85, fontFace: BODY, fontSize: 13.5, color: INK, margin: 0, isTextBox: true, valign: "top" });
  });
  footer(s, n);
  s.addNotes("Walk the diagram top to bottom: source split, shared retrieval, three configurations, evaluation harness, four buckets.");
}
// ---------------- 6 Systems
{
  const s = pres.addSlide(); n++; title(s, "Three systems, one generator", "Everything is held fixed except the prompt");
  card(s, 0.6, 1.8, 3.9, 2.9, "Baseline 1: plain LLM", "System description only, no retrieved text. Label plus a short reason. No faithfulness score by design.", B1C);
  card(s, 4.72, 1.8, 3.9, 2.9, "Baseline 2: standard RAG", "Description plus the top 5 passages and a generic instruction to classify and ground the explanation.", B2C);
  card(s, 8.85, 1.8, 3.9, 2.9, "Agent: structured RAG", "Same passages, prompt walks the legal test step by step: purpose, Annex III area, Article 6(3) conditions, profiling rule.", AGC);
  stat(s, 0.6, 5.1, 3.9, "phi-4", "generator: microsoft/phi-4 (14B), local vLLM, greedy, pinned");
  stat(s, 4.72, 5.1, 3.9, "Qwen 72B", "judge: Qwen2.5-72B-Instruct-AWQ, other model family");
  stat(s, 8.85, 5.1, 3.9, "645", "generations, 0 parse failures, 0 empty, 0 errors");
  footer(s, n);
  s.addNotes("A local open generator replaced the planned paid API model: it can be pinned, rerun and costs nothing. It proved fully reliable, so model reliability is not a story here.");
}
// ---------------- 7 Leak
{
  const s = pres.addSlide(); n++; title(s, "A label leak found and fixed", "60% of inputs contained the Commission's own verdict");
  s.addChart(pres.charts.BAR, [
    { name: "129 inputs stating the verdict", labels: ["Plain LLM", "Standard RAG", "Agent"], values: [0.938, 0.922, 0.961] },
    { name: "86 clean inputs", labels: ["Plain LLM", "Standard RAG", "Agent"], values: [0.674, 0.953, 0.953] }],
    Object.assign({}, quiet, { x: 0.6, y: 1.7, w: 6.6, h: 4.9, barDir: "col", barGrouping: "clustered", chartColors: ["E34948", "2A78D6"], barGapWidthPct: 60,
      showLegend: true, legendPos: "t", showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.00", valAxisMinVal: 0, valAxisMaxVal: 1, valAxisLabelFormatCode: "0.0",
      showTitle: true, title: "Accuracy in the first run", titleFontFace: HEAD, titleFontSize: 14, titleColor: NAVY }));
  s.addText([{ text: "What happened", options: { bold: true, color: NAVY, fontSize: 17, fontFace: HEAD, breakLine: true } },
    { text: "The extractor kept each example's closing verdict, e.g. \"It therefore falls outside the use case of point 4(a)\". The plain model was reading the answer.", options: { breakLine: true } }],
    { x: 7.6, y: 1.8, w: 5.1, h: 1.9, fontFace: BODY, fontSize: 14, color: INK, margin: 0, isTextBox: true, valign: "top" });
  s.addText([{ text: "How it was fixed", options: { bold: true, color: NAVY, fontSize: 17, fontFace: HEAD, breakLine: true } }], { x: 7.6, y: 3.8, w: 5.1, h: 0.45, margin: 0, isTextBox: true });
  bullets(s, ["Keep what the system does; remove every legal conclusion and citation", "96 rows automatic, 31 hand-edited, 46 reviewed by the author", "IDs and gold labels unchanged; all systems rerun",
    "Mean input length 557 to 392 characters"], 7.6, 4.3, 5.1, 2.4, 14);
  footer(s, n);
  s.addNotes("Plain model: 0.94 on leaky rows, 0.67 on clean rows. Retrieval systems barely affected. Fixed by redaction and a full rerun; disclosed in the report.");
}
// ---------------- 8 Correctness
{
  const s = pres.addSlide(); n++; title(s, "Result 1: retrieval helps, the structured prompt does not", "Accuracy on 215 inputs, before and after redaction");
  s.addChart(pres.charts.BAR, [
    { name: "Original inputs", labels: ["Plain LLM", "Standard RAG", "Agent"], values: [0.833, 0.935, 0.958] },
    { name: "Redacted inputs", labels: ["Plain LLM", "Standard RAG", "Agent"], values: [0.688, 0.879, 0.856] }],
    Object.assign({}, quiet, { x: 0.6, y: 1.7, w: 7.2, h: 5.0, barDir: "col", barGrouping: "clustered", chartColors: ["B9B8B2", "2A78D6"], barGapWidthPct: 60,
      showLegend: true, legendPos: "t", showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.000", valAxisMinVal: 0, valAxisMaxVal: 1, valAxisLabelFormatCode: "0.0" }));
  stat(s, 8.2, 1.8, 4.55, "+19 pts", "standard RAG vs plain LLM, redacted inputs (McNemar p < 0.001)", "2A78D6");
  stat(s, 8.2, 3.4, 4.55, "60 vs 17", "false high-risk calls: plain LLM vs standard RAG");
  stat(s, 8.2, 5.0, 4.55, "p = 0.30", "agent vs standard RAG: no gain, slightly worse (0.856 vs 0.879)", RED);
  footer(s, n);
  s.addNotes("Grounding in the guidelines removes most false alarms. The step-by-step agent is not better than a generic RAG prompt. The leak had even flipped the ranking of the two.");
}
// ---------------- 9 Areas
{
  const s = pres.addSlide(); n++; title(s, "Where the systems struggle", "Accuracy by Annex III area (redacted inputs)");
  img(s, "fig_area_heatmap.png", 0.6, 1.65, 8.4, [1832, 671]);
  img(s, "fig_confusion.png", 0.6, 4.85, 5.8, [1631, 572]);
  card(s, 9.35, 1.7, 3.4, 2.4, "Critical infrastructure", "Hardest for both RAG systems (0.61, 0.56). The test is safety component, not sector.", GOLD);
  card(s, 9.35, 4.35, 3.4, 2.4, "Law enforcement", "Plain LLM collapses to 0.26: it calls most police uses high-risk. RAG fixes this (0.87+).", RED);
  footer(s, n);
  s.addNotes("Two patterns: critical infrastructure is hard for everyone because of the safety-component test; the plain model over-calls in law enforcement.");
}
// ---------------- 10 Headline
{
  const s = pres.addSlide(); n++; title(s, "Result 2: faithfulness cannot tell right from wrong", "RAGAS faithfulness of every answer, split by whether the label was correct");
  img(s, "fig3_faithfulness.png", 0.6, 1.7, 8.3, [1553, 799]);
  stat(s, 9.3, 1.8, 3.45, "0.465", "agent AUC (95% CI 0.36 to 0.57): chance level", RED);
  stat(s, 9.3, 3.4, 3.45, "0.49 vs 0.45", "agent: wrong answers score slightly higher than right ones");
  stat(s, 9.3, 5.0, 3.45, "0.615", "standard RAG AUC: weak signal only");
  footer(s, n);
  s.addNotes("AUC is the chance that a random right answer scores higher than a random wrong one. 0.5 is a coin flip. For the agent the confidence interval includes 0.5.");
}
// ---------------- 11 Buckets
{
  const s = pres.addSlide(); n++; title(s, "Both off-diagonal buckets are well populated", "Four-bucket matrix at a faithful cut of 0.5");
  img(s, "fig_buckets.png", 0.6, 1.75, 7.9, [1459, 644]);
  stat(s, 8.9, 1.8, 3.85, "17 of 31", "agent errors that pass as faithful (55%)", RED);
  stat(s, 8.9, 3.4, 3.85, "93 of 184", "correct agent answers scored as unfaithful");
  s.addText("Part of the right-but-unfaithful effect is mechanical: sentences that restate the input are not in the passages, so the judge marks them unsupported. That is how RAGAS is defined.",
    { x: 8.9, y: 5.05, w: 3.85, h: 1.7, fontFace: BODY, fontSize: 12.5, italic: true, color: MUTED, margin: 0, isTextBox: true, valign: "top" });
  footer(s, n);
  s.addNotes("Faithful but wrong: 17 agent, 14 standard RAG. Right but unfaithful: about half of correct answers.");
}
// ---------------- 12 Sweep
{
  const s = pres.addSlide(); n++; title(s, "Not an artefact of the cut-off", "Share of wrong answers that still pass as faithful as the threshold rises");
  s.addChart(pres.charts.LINE, [
    { name: "Standard RAG", labels: ["0.3", "0.5", "0.7", "0.9"], values: [0.808, 0.538, 0.038, 0] },
    { name: "Agent", labels: ["0.3", "0.5", "0.7", "0.9"], values: [0.710, 0.548, 0.226, 0.032] }],
    Object.assign({}, quiet, { x: 0.6, y: 1.7, w: 7.8, h: 5.0, chartColors: [B2C, AGC], lineSize: 3, lineDataSymbol: "circle", lineDataSymbolSize: 9,
      showLegend: true, legendPos: "t", showValue: false, valAxisMinVal: 0, valAxisMaxVal: 1, valAxisLabelFormatCode: "0%",
      showCatAxisTitle: true, catAxisTitle: "Faithful cut", catAxisTitleFontSize: 11, catAxisTitleColor: MUTED }));
  stat(s, 8.8, 1.8, 3.95, "7", "agent errors still count as faithful at a strict cut of 0.7", RED);
  stat(s, 8.8, 3.4, 3.95, "1.00", "perfect faithfulness score on a wrong answer (input 207)", RED);
  s.addText("Threshold-free measures (AUC, correlation) are reported alongside, so the finding does not rest on one cut.", { x: 8.8, y: 5.05, w: 3.95, h: 1.5, fontFace: BODY, fontSize: 13, color: MUTED, margin: 0, isTextBox: true, valign: "top" });
  footer(s, n);
  s.addNotes("Counts: agent 22, 17, 7, 1 of 31. Standard RAG 21, 14, 1, 0 of 26.");
}
// ---------------- 13 Errors
{
  const s = pres.addSlide(); n++; title(s, "Why the wrong answers look grounded", "All 17 faithful-but-wrong agent answers read and categorised");
  s.addChart(pres.charts.BAR, [{ name: "Answers", labels: ["A. Sector taken as the use case", "B. 6(3) exception not applied", "C. Profiling rule misused", "D. Condition misread / fact invented", "E. Too cautious on short input"], values: [6, 4, 3, 2, 2] }],
    Object.assign({}, quiet, { x: 0.6, y: 1.7, w: 6.4, h: 3.6, barDir: "bar", chartColors: [AGC], showLegend: false, showValue: true, dataLabelPosition: "outEnd", catAxisOrientation: "maxMin", valAxisHidden: true, valGridLine: { style: "none" }, catAxisLabelFontSize: 12 }));
  stat(s, 0.6, 5.35, 3.1, "14 / 17", "had the correct guideline section retrieved");
  stat(s, 3.9, 5.35, 3.1, "21 / 31", "verdict statements judged 'supported'", RED);
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 7.4, y: 1.8, w: 5.35, h: 4.95, fill: { color: NAVY }, line: { color: NAVY }, rectRadius: 0.08 });
  s.addText([{ text: "Case: input 207", options: { bold: true, fontSize: 22, color: GOLD, fontFace: HEAD, breakLine: true } },
    { text: "A tool that pre-classifies incoming court cases by type.", options: { breakLine: true, color: WHITE } },
    { text: " ", options: { breakLine: true, fontSize: 10 } },
    { text: "Agent: ", options: { bold: true, color: "CADCFC" } }, { text: "places it under point 8(a), then asserts no Article 6(3) condition applies. Label: high-risk.", options: { breakLine: true, color: WHITE } },
    { text: " ", options: { breakLine: true, fontSize: 10 } },
    { text: "Commission: ", options: { bold: true, color: "CADCFC" } }, { text: "narrow procedural / preparatory task. Not high-risk.", options: { breakLine: true, color: WHITE } },
    { text: " ", options: { breakLine: true, fontSize: 10 } },
    { text: "Faithfulness: 6 of 6 statements supported = 1.00", options: { bold: true, color: GOLD } }],
    { x: 7.75, y: 2.1, w: 4.7, h: 4.4, fontFace: BODY, fontSize: 17, valign: "middle", margin: 0, isTextBox: true });
  footer(s, n);
  s.addNotes("The model had the right rule but applied it wrongly. The judge accepts the conclusion because the passages state the general rule correctly. Faithfulness never checks the application step.");
}
// ---------------- 14 Findings
{
  const s = pres.addSlide(); n++; title(s, "Key findings");
  const f = [["Faithfulness is not correctness", "For the agent, faithfulness is at chance level for spotting wrong labels (AUC 0.465). 17 of 31 errors pass as faithful."],
    ["Errors are application errors", "The right passage was retrieved in 14 of 17 cases; the model misapplied the rule, which RAGAS cannot see."],
    ["Retrieval matters, prompt engineering did not", "RAG adds about 19 points over the plain model; the step-by-step agent is not better than a generic RAG prompt."],
    ["Benchmarks from worked examples can leak", "The verdict text inflated accuracy by up to 15 points and flipped the ranking of the two best systems."]];
  f.forEach((t, i) => {
    const x = 0.6 + (i % 2) * 6.2, y = 1.45 + Math.floor(i / 2) * 2.7;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 5.95, h: 2.45, fill: { color: LIGHT }, line: { color: LIGHT }, rectRadius: 0.08 });
    s.addText(String(i + 1), { x: x + 0.3, y: y + 0.3, w: 0.8, h: 0.9, fontFace: HEAD, fontSize: 44, bold: true, color: i === 0 ? RED : GOLD, margin: 0, isTextBox: true });
    s.addText(t[0], { x: x + 1.2, y: y + 0.3, w: 4.5, h: 0.75, fontFace: HEAD, fontSize: 18, bold: true, color: NAVY, margin: 0, isTextBox: true, valign: "top" });
    s.addText(t[1], { x: x + 1.2, y: y + 1.05, w: 4.5, h: 1.3, fontFace: BODY, fontSize: 14, color: INK, margin: 0, isTextBox: true, valign: "top" });
  });
  footer(s, n);
  s.addNotes("Four takeaways, most important first.");
}
// ---------------- 15 Limitations
{
  const s = pres.addSlide(); n++; title(s, "Limitations and future work");
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.6, y: 1.3, w: 5.95, h: 5.4, fill: { color: LIGHT }, line: { color: LIGHT }, rectRadius: 0.08 });
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 6.8, y: 1.3, w: 5.95, h: 5.4, fill: { color: NAVY }, line: { color: NAVY }, rectRadius: 0.08 });
  s.addText("Limitations", { x: 0.95, y: 1.55, w: 5.8, h: 0.5, fontFace: HEAD, fontSize: 20, bold: true, color: NAVY, margin: 0, isTextBox: true });
  bullets(s, ["One generator and one judge; results may depend on these models", "Single annotator for redaction review and error categories",
    "About 20 inputs still describe the legal test without stating the label", "26 and 31 wrong answers: wide confidence intervals",
    "Commission examples are cleaner than real product descriptions"], 0.95, 2.25, 5.3, 4.3, 17);
  s.addText("Future work", { x: 7.15, y: 1.55, w: 5.3, h: 0.5, fontFace: HEAD, fontSize: 20, bold: true, color: GOLD, margin: 0, isTextBox: true });
  bullets(s, ["A second, stronger generator, including a closed commercial model, on the same redacted inputs", "A second annotator and inter-annotator agreement",
    "Realistic product descriptions labelled against the guidelines", "A correctness-aware check: does the conclusion follow from the retrieved rule and the stated facts?",
    "Extension towards a thesis or paper"], 7.15, 2.25, 5.3, 4.3, 17, WHITE);
  footer(s, n);
  s.addNotes("Be upfront about the limits; each maps to a concrete next step.");
}
// ---------------- 16 Conclusion
{
  const s = pres.addSlide(); n++; s.background = { color: NAVY };
  s.addText("Conclusion", { x: 0.8, y: 0.8, w: 11, h: 0.6, fontFace: BODY, fontSize: 16, bold: true, color: GOLD, charSpacing: 2, margin: 0, isTextBox: true });
  s.addText("A high faithfulness score says almost nothing about whether a legal classification is right.", { x: 0.8, y: 1.6, w: 11.7, h: 1.9, fontFace: HEAD, fontSize: 36, bold: true, color: WHITE, margin: 0, isTextBox: true });
  s.addText("Faithfulness is necessary but not sufficient. Wherever a ground truth exists, report it next to a correctness check.",
    { x: 0.8, y: 3.7, w: 11, h: 1.0, fontFace: BODY, fontSize: 20, color: "CADCFC", margin: 0, isTextBox: true });
  s.addText("Thank you. Questions?", { x: 0.8, y: 5.6, w: 8, h: 0.6, fontFace: HEAD, fontSize: 24, color: WHITE, margin: 0, isTextBox: true });
  s.addText("github.com/rahulrawat20022002/case_study2", { x: 0.8, y: 6.3, w: 8, h: 0.4, fontFace: BODY, fontSize: 13, color: "8FA3C8", margin: 0, isTextBox: true });
  s.addNotes("Close on the one-line takeaway and the practical recommendation.");
}

pres.writeFile({ fileName: "/home/claude/case_study2/deck/CS2_Presentation.pptx" }).then(f => console.log("saved", f));
