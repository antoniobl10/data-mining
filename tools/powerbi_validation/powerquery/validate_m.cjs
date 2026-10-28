// Microsoft's public parser validates syntax only; this does not execute M or refresh data.
const fs = require('fs');
const path = require('path');
const {DefaultSettings, TaskUtils} = require('@microsoft/powerquery-parser');
const root = path.resolve(__dirname, '../../..');
const model = JSON.parse(fs.readFileSync(path.join(root, 'powerbi/model/model.source.json'), 'utf8')).model;

(async () => {
  const sources = model.expressions.map(item => ({name: item.name, text: item.expression}));
  for (const table of model.tables) for (const partition of table.partitions) {
    const expression = partition.source.expression;
    sources.push({name: table.name, text: Array.isArray(expression) ? expression.join('\n') : expression});
  }
  const checks = [];
  for (const source of sources) {
    const result = await TaskUtils.tryLexParse(DefaultSettings, source.text);
    checks.push({name: source.name, status: TaskUtils.isParseStageOk(result) ? 'PASS' : 'FAIL', error: result.error?.message ?? null});
  }
  const report = {parser: '@microsoft/powerquery-parser 4.0.1', checks, syntax_only: true, refreshed: false};
  fs.writeFileSync(path.join(root, 'powerbi/validation/powerquery_syntax.json'), JSON.stringify(report, null, 2));
  console.log(JSON.stringify({expressions: checks.length, passed: checks.filter(x => x.status === 'PASS').length, failed: checks.filter(x => x.status === 'FAIL')}, null, 2));
  if (checks.some(x => x.status === 'FAIL')) process.exitCode = 1;
})().catch(error => {console.error(error); process.exitCode = 1;});
