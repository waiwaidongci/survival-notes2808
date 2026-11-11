import {request,download} from './client';import {Run,RunSnapshotView} from '../types/domain';
export const getRuns=()=>request<Run[]>('/runs');
export const createRun=(data:{name:string;cohort_a_id:number;cohort_b_id:number;confidence:number})=>request<Run>('/runs',{method:'POST',body:JSON.stringify(data)});
export const getRunSnapshot=(id:number)=>request<RunSnapshotView>(`/runs/${id}/snapshot`);
export const downloadArchive=(id:number)=>download(`/runs/${id}/archive`,`survival-run-${id}-archive.json`);
