import {request} from './client';import {Specimen} from '../types/domain';export const getSpecimens=(id:number)=>request<Specimen[]>(`/cohorts/${id}/specimens`);
