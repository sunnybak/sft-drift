import type {ReportScore} from './report-types';
export type ChangeAggregation='mean'|'signed_sum'|'absolute_sum';
export function summedChange(score:ReportScore|undefined,referenceId:string,aggregation:ChangeAggregation):number|null {
 const t=score?.changeTotals;
 if(score?.value==null||!t||t.referenceModelId!==referenceId)return null;
 return aggregation==='absolute_sum'?t.absoluteSum:aggregation==='signed_sum'?t.signedSum:null;
}
export function formatSummedChange(value:number,absolute:boolean){
 const scaled=value*100,rounded=Math.round((Math.abs(scaled)+1e-10)*10)/10;
 return `${!absolute&&rounded>0?(scaled<0?'−':'+'):''}${rounded.toFixed(1)} total pp`;
}
