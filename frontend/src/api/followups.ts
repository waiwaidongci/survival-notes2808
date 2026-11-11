import {request} from './client';export const annotateFollowup=(id:number,note:string)=>request(`/followups/${id}`,{method:'PATCH',body:JSON.stringify({note})});
