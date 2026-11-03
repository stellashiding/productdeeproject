import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {dimensionProfile,dimensionMatrix,trajectoryMarkup,hasDimensionIssue} from '../dist/pipeline-viz.js';
const records=JSON.parse(readFileSync(new URL('../dist/data/pipeline/results.json',import.meta.url))).records;

test('RHCA profiles count supplied per-dimension anchors without averaging or inventing scores',()=>{
 const r=dimensionProfile(records,'R'),h=dimensionProfile(records,'H');
 assert.equal(r.rated,60);assert.equal(r.affected,48);assert.equal(r.critical,0);
 assert.equal(h.affected,48);assert.equal(h.critical,48);
 assert.equal(r.distribution[0],0);assert.equal(h.distribution[1],0);
 assert.equal(dimensionProfile([{original:{rhca:[{scores:{A:1}}]}}],'R').rated,0);
});
test('Time matrix keeps four dimension rows and preserves missing anchors',()=>{
 const html=trajectoryMarkup(records[16]);
 for(const label of ['Reasoning transparency','Helpfulness','Consistency','Context alignment'])assert.ok(html.includes(label));
 assert.equal((html.match(/class="rhca-matrix-lane"/g)||[]).length,4);
 assert.ok(html.includes('checkpoint 3, score 2'));assert.ok(html.includes('checkpoint 3, score 1'));
 const missing=structuredClone(records[16]);delete missing.original.rhca[2].scores.R;
 const out=trajectoryMarkup(missing,2);assert.ok(out.includes('checkpoint 3, Not rated'));assert.ok(out.includes('Not rated'));
});
test('Matrix distinguishes unreported dimensions and escapes imported domain text',()=>{
 const html=dimensionMatrix([{original:{domain:'<script>',rhca:[{scores:{A:1}}]}}]);
 assert.ok(html.includes('&lt;script&gt;'));assert.ok(!html.includes('<script>'));
 assert.ok(html.includes('Not rated'));assert.ok(html.includes('1 of 1 rated trajectories'));
});

test('Dimension filters tolerate malformed imported ratings without filling missing scores',()=>{
 assert.equal(hasDimensionIssue({original:{rhca:{A:1}}},'A'),false);
 assert.equal(hasDimensionIssue({original:{rhca:[{scores:{A:1}}]}},'A'),true);
 assert.equal(hasDimensionIssue({original:{rhca:[{scores:{A:1}}]}},'R'),false);
});

test('Selected matrix cell keeps both dimension and checkpoint identity',()=>{
 const html=trajectoryMarkup(records[16],2,'H');
 assert.ok(html.includes('is-selected" data-rhca-checkpoint="2" data-rhca-cell="H" aria-pressed="true"'));
 assert.equal((html.match(/aria-pressed="true"/g)||[]).length,1);
 assert.equal((html.match(/data-rhca-cell=/g)||[]).length,24);
});
