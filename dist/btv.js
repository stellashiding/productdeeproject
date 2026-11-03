// ICLR 2027 submission §3.2 Eq. (1). Supplied RHCA ratings, not a semantic judge.
export function verifyBTV(ratings,{p=1,penalty=.5,threshold=2}={}){
 if(!Number.isFinite(p)||p<1||!Number.isFinite(penalty)||penalty<0||!Number.isFinite(threshold)||threshold<1||threshold>3)throw Error('Invalid BTV parameters.');
 if(!Array.isArray(ratings)||!ratings.length)throw Error('Complete R/H/C/A ratings are required.');
 const dimensions=['R','H','C','A'],critical=[];
 const scores=ratings.map((r,i)=>{if(!r||dimensions.some(d=>!Number.isInteger(r[d])||r[d]<1||r[d]>3))throw Error('Turn '+(i+1)+' needs all four RHCA anchors (1, 2, 3).');if(dimensions.some(d=>r[d]===1))critical.push(i+1);return dimensions.reduce((s,d)=>s+r[d],0)/4});
 const low=scores.reduce((a,b)=>Math.min(a,b),3),mean=scores.reduce((a,q)=>a+(low/q)**p,0)/scores.length,generalized=low*mean**(-1/p);
 let peak=scores[0],peakTurn=1,drop=0,pair=null;
 scores.slice(1).forEach((q,i)=>{if(peak-q>drop){drop=peak-q;pair=[peakTurn,i+2]}if(q>peak){peak=q;peakTurn=i+2}});
 const score=generalized-penalty*drop;
 return {status:'computed',evaluator:'btv-equation-1-v1',paper:'ICLR 2027 submission §3.2 Eq. (1)',dimensions,weights:[.25,.25,.25,.25],p,penalty,threshold,turn_scores:scores,arithmetic_mean:scores.reduce((a,q)=>a+q,0)/scores.length,generalized_mean:generalized,max_drop:drop,drop_pair:pair,score,passed:score>=threshold,critical_anchor_turns:critical,note:'Any Anchor 1 is reported separately; BTV passing does not erase it. Ratings supplied by caller.'};
}
