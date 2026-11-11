<script setup lang="ts">
import {computed,ref,watch} from 'vue';
import {useRoute} from 'vue-router';
import {Download} from 'lucide-vue-next';
import {useResearchData} from '../hooks/useResearch';
import {useAction} from '../hooks/useAction';
import {getRunSnapshot,downloadArchive} from '../api/runs';
import RunSummary from '../components/RunSummary.vue';
import SurvivalPlot from '../components/SurvivalPlot.vue';
import RiskTable from '../components/RiskTable.vue';
import SnapshotCard from '../components/SnapshotCard.vue';
import StatusBadge from '../components/common/StatusBadge.vue';
import Notice from '../components/common/Notice.vue';
import DataTable from '../components/common/DataTable.vue';
import {number,probability} from '../utils/format';
import type {RunSnapshotView} from '../types/domain';
const s=useResearchData(true),a=useAction(),route=useRoute(),selected=ref(Number(route.query.run)||0);
const run=computed(()=>s.runs.find(r=>r.id===selected.value)||s.runs[0]);
const snapshotView=ref<RunSnapshotView|null>(null);
const approved=computed(()=>run.value?s.notes.some(n=>n.run_id===run.value!.id&&n.status==='approved'):false);
watch(run,async(r)=>{
  snapshotView.value=null;
  if(r&&r.status==='completed'&&r.input_hash){
    try{snapshotView.value=await getRunSnapshot(r.id)}catch(e){a.error.value=(e as Error).message}
  }
},{immediate:true});
function archive(){if(run.value)a.execute(async()=>downloadArchive(run.value!.id));}
</script>
<template><div class="page results-page"><div class="page-title"><div><p class="eyebrow">SURVIVAL EVIDENCE / 04</p><h1>耐久结果<span>同时阅读曲线、在险人数与不确定性。</span></h1></div><RouterLink class="outline" :to="'/notes'+(run?'?run='+run.id:'')">记录维护建议 →</RouterLink></div><Notice :message="s.error||a.error.value" @retry="s.refresh"/><div class="run-picker"><label>研究档案<select aria-label="研究档案" :value="run?.id||''" @change="selected=Number(($event.target as HTMLSelectElement).value)"><option v-for="r in s.runs" :key="r.id" :value="r.id">#{{r.id}} / {{r.name}} / {{r.status}}</option></select></label><StatusBadge v-if="run" :status="run.status"/></div><template v-if="run?.status==='completed'"><RunSummary :run="run"/><SnapshotCard :run="run"/><dl v-if="snapshotView" class="frozen-groups"><div v-for="g in snapshotView.snapshot.groups" :key="g.cohort.id"><dt>{{g.cohort.code}} / {{g.cohort.process}}</dt><dd>{{g.specimens}} 件 · {{g.events}} 失效 · {{g.censored}} 删失</dd></div><div class="frozen-method"><dt>分析口径</dt><dd>{{snapshotView.snapshot.method_version}} · 置信 {{(snapshotView.snapshot.confidence*100).toFixed(0)}}% · 在险 {{snapshotView.snapshot.risk_times.join('/')}}h · 单位 {{snapshotView.snapshot.time_unit}}</dd></div><div class="frozen-verified" :class="snapshotView.artifact_verified===false?'bad':'ok'"><dt>归档对账</dt><dd>{{snapshotView.artifact_verified===false?'文件不符，已触发按库重建':'归档哈希一致'}} · <span class="mono">{{snapshotView.artifact_path}}</span></dd></div></dl><SurvivalPlot :result="run.result"/><RiskTable :result="run.result"/><div class="comparison-note"><span>LOG-RANK</span><p>{{run.result.interpretation}}</p><b>χ² {{number(run.result.logrank.chi_square,4)}} / p {{probability(run.result.logrank.p_value)}}</b></div><p class="caption">{{run.result.assumptions}}</p><div class="section-heading"><h2>并列事件与风险集明细</h2><span>前12个事件时点</span></div><DataTable :head="['时间 / h','A在险','B在险','A事件','B事件','A期望事件','方差项']"><tr v-for="p in run.result.logrank.event_table.slice(0,12)" :key="p.time"><td>{{p.time}}</td><td>{{p.risk_a}}</td><td>{{p.risk_b}}</td><td>{{p.events_a}}</td><td>{{p.events_b}}</td><td>{{number(p.expected_a,4)}}</td><td>{{number(p.variance,4)}}</td></tr></DataTable><p class="fingerprint">输入SHA256 {{run.result.input_hash}}</p><button v-if="approved" class="outline" :disabled="a.busy.value" @click="archive"><Download :size="15"/> 下载固化归档 JSON</button><p v-else class="caption">归档含冻结输入、结果与双哈希；研究获批后可下载，获批前仍可在线查看。</p></template><div v-else-if="run" class="pending"><h2>{{run.status==='failed'?'研究未能完成':'后台正在整理耐久曲线'}}</h2><p>{{run.error||'独立worker按入队快照执行KM、Greenwood区间与log-rank；中断会自动恢复，本页每2秒更新。'}}</p></div><p v-else class="empty">尚无研究，请先选择两批工艺创建比较。</p></div></template>
