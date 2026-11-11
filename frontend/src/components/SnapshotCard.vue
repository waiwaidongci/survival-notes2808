<script setup lang="ts">
import {computed} from 'vue';
import {Lock,Snowflake,FileCheck2,FileWarning} from 'lucide-vue-next';
import {Run} from '../types/domain';
const props=defineProps<{run:Run}>();
const frozen=computed(()=>Boolean(props.run.input_hash));
</script>
<template>
  <section class="snapshot-card">
    <div class="snapshot-head">
      <span class="eyebrow"><Lock :size="13"/> 入队固化依据</span>
      <span :class="['snapshot-state',frozen?'ok':'legacy']">{{frozen?'已冻结输入':'旧研究 · 已回填'}}</span>
    </div>
    <p v-if="frozen" class="snapshot-hash mono">SHA256 {{run.input_hash}}</p>
    <p class="snapshot-note">研究排队瞬间冻结两批试件、终态随访（含当时备注）与分析口径；之后补写随访备注只影响新研究，不改变本档案。</p>
    <dl class="snapshot-meta">
      <div><dt>归档文件</dt><dd :class="['mono',run.artifact_verified===false?'bad':'']">
        <component :is="run.artifact_verified===false?FileWarning:FileCheck2" :size="13"/>
        {{run.artifact_path||'—'}}
      </dd></div>
      <div><dt>档案哈希</dt><dd class="mono">{{run.artifact_hash?run.artifact_hash.slice(0,16)+'…':'—'}}</dd></div>
      <div v-if="run.running_at"><dt>计算心跳</dt><dd class="mono"><Snowflake :size="13"/>{{run.running_at}}</dd></div>
    </dl>
  </section>
</template>
