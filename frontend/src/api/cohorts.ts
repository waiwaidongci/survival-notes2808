import {request} from './client';import {Cohort} from '../types/domain';export const getCohorts=()=>request<Cohort[]>('/cohorts');
