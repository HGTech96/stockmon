/* ============ Icons (hand-rolled minimal glyph set — no CDN allowed in a self-contained artifact) ============ */
const ICON = {
  check: '<svg viewBox="0 0 16 16" fill="none"><path d="M3.5 8.5 6.5 11.5 12.5 4.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  cross: '<svg viewBox="0 0 16 16" fill="none"><path d="M4.5 4.5l7 7M11.5 4.5l-7 7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
  up: '<svg viewBox="0 0 16 16" fill="none"><path d="M8 12.5V3.5M8 3.5 4 7.5M8 3.5l4 4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  down: '<svg viewBox="0 0 16 16" fill="none"><path d="M8 3.5v9M8 12.5 4 8.5M8 12.5l4-4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  minus: '<svg viewBox="0 0 16 16" fill="none"><path d="M4 8h8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
  warnTri: '<svg viewBox="0 0 16 16" fill="none"><path d="M8 6.1v3.4M8 11.6h.01M6.9 2.9 1.3 12.6a1.2 1.2 0 0 0 1 1.8h11.4a1.2 1.2 0 0 0 1-1.8L9.1 2.9a1.2 1.2 0 0 0-2.2 0Z" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  external: '<svg viewBox="0 0 16 16" fill="none"><path d="M6.5 4.5h-2A1.5 1.5 0 0 0 3 6v6a1.5 1.5 0 0 0 1.5 1.5h6A1.5 1.5 0 0 0 12 12v-2M9.5 3h3.5v3.5M12.5 3.5 7 9" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  plus: '<svg viewBox="0 0 16 16" fill="none"><path d="M8 3.5v9M3.5 8h9" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
  clock: '<svg viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.4"/><path d="M8 4.8V8l2.3 1.3" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  clockLg: '<svg viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.5"/><path d="M12 7v5l3.5 2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  inboxLg: '<svg viewBox="0 0 24 24" fill="none"><path d="M4 12.5V7.5A1.5 1.5 0 0 1 5.5 6h13A1.5 1.5 0 0 1 20 7.5v5M4 12.5h4.2c.3 0 .55.18.66.46l.5 1.3c.1.28.36.46.66.46h4c.3 0 .56-.18.66-.46l.5-1.3c.1-.28.36-.46.66-.46H20M4 12.5v4A1.5 1.5 0 0 0 5.5 18h13a1.5 1.5 0 0 0 1.5-1.5v-4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
  chartEmpty: '<svg viewBox="0 0 24 24" fill="none"><path d="M4 19h16M6 16V9M11 16V5M16 16v-7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>',
};

/* ============ Formatting ============ */
function fmtMoney(n){ return '$'+Math.abs(n).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2}); }
function fmtMoneyWhole(n){ return (n<0?'-':'')+'$'+Math.round(Math.abs(n)).toLocaleString('en-US'); }
function fmtMoneySigned(n){ return (n>=0?'+':'-')+'$'+Math.abs(n).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2}); }
function fmtPct(n){ if(Math.abs(n)<0.005) return '0.00%'; return (n>0?'+':'-')+Math.abs(n).toFixed(2)+'%'; }
function fmtVol(n){ return n.toFixed(1)+'M'; }
function fmtPrice(n){ return '$'+n.toFixed(2); }
function fmtShares(n){ return n.toLocaleString('en-US'); }
function fmtDateShort(d){ return d.toLocaleDateString('en-US',{month:'short',day:'numeric'}); }
function fmtDateLong(d){ return d.toLocaleDateString('en-US',{weekday:'short',month:'short',day:'numeric'}); }

function trendHtml(pct){
  const dir = pct>0.05?'up':(pct<-0.05?'down':'flat');
  const icon = dir==='up'?ICON.up:(dir==='down'?ICON.down:'');
  return `<span class="trend is-${dir}">${icon}${fmtPct(pct)}</span>`;
}
const BADGE_MAP = {
  buy:{cls:'badge--buy',label:'Possible buy',icon:ICON.up},
  sell:{cls:'badge--sell',label:'Possible sell',icon:ICON.down},
  wait:{cls:'badge--wait',label:'Wait',icon:ICON.minus},
  insufficient:{cls:'badge--insufficient',label:'Not enough data',icon:ICON.clock},
};
function badgeHtml(type,opts){
  opts=opts||{};
  const m=BADGE_MAP[type];
  return `<span class="badge ${m.cls}${opts.lg?' badge--lg':''}">${m.icon}${m.label}</span>`;
}

/* ============ Deterministic pseudo-random history generator ============
   Each ticker gets its own seeded generator so reloading the page always
   produces the same chart — this is a design demo, not live market data. */
function hashSeed(str){
  let h=1779033703^str.length;
  for(let i=0;i<str.length;i++){ h=Math.imul(h^str.charCodeAt(i),3432918353); h=h<<13|h>>>19; }
  h=Math.imul(h^h>>>16,2246822507); h=Math.imul(h^h>>>13,3266489909);
  return (h^h>>>16)>>>0;
}
function mulberry32(seed){
  return function(){
    seed|=0; seed=seed+0x6D2B79F5|0;
    let t=Math.imul(seed^seed>>>15,1|seed);
    t=t+Math.imul(t^t>>>7,61|t)^t;
    return ((t^t>>>14)>>>0)/4294967296;
  };
}
const REFERENCE_TODAY = new Date(2026,7,19); // Wednesday, Aug 19 2026

function genHistory(cfg){
  const rand=mulberry32(hashSeed(cfg.ticker));
  const n=cfg.days||30;
  const closes=[];
  let prevNoise=0;
  for(let i=0;i<n;i++){
    const t=n===1?1:i/(n-1);
    const hump=cfg.amplitude?cfg.amplitude*Math.sin(t*Math.PI*(cfg.bumps||1)):0;
    const trend=cfg.startPrice+(cfg.endPrice-cfg.startPrice)*t+hump;
    const noiseRaw=(rand()-0.5)*cfg.startPrice*0.014;
    const noise=noiseRaw*0.55+prevNoise*0.45;
    prevNoise=noise;
    closes.push(Math.max(0.5,trend+noise));
  }
  if(cfg.gapPrevDayPrice!=null) closes[n-2]=cfg.gapPrevDayPrice;
  closes[n-1]=cfg.endPrice;
  const volumes=[];
  for(let i=0;i<n;i++) volumes.push(Math.max(0.1,cfg.volBase*(0.72+rand()*0.56)));
  volumes[n-1]=Math.max(0.1,cfg.volBase*(cfg.volTodayMult!=null?cfg.volTodayMult:(0.72+rand()*0.56)));
  const hist=[];
  for(let i=0;i<n;i++){
    const d=new Date(REFERENCE_TODAY);
    d.setDate(d.getDate()-(n-1-i));
    hist.push({date:d,close:closes[i],volume:volumes[i]});
  }
  return hist;
}

/* ============ Indicators & suggestion logic ============
   Everything below is derived from the generated history itself, never
   hand-picked — so the badge, checklist and numbers always agree. */
function computeIndicators(history){
  const n=history.length;
  const closes=history.map(h=>h.close);
  const vols=history.map(h=>h.volume);
  const price=closes[n-1];
  const prevClose=closes[n-2];
  const change1dPct=(price-prevClose)/prevClose*100;
  const wkIdx=Math.max(0,n-8);
  const change7dPct=(price-closes[wkIdx])/closes[wkIdx]*100;
  const avg30=closes.reduce((a,b)=>a+b,0)/n;
  const high30=Math.max(...closes);
  const low30=Math.min(...closes);
  const range=high30-low30||1;
  const distFromHighRangePct=(high30-price)/range*100;
  const distFromLowRangePct=(price-low30)/range*100;
  const distFromHighSimplePct=(price-high30)/high30*100;
  const distFromLowSimplePct=(price-low30)/low30*100;
  const volToday=vols[n-1];
  const avgVolume=vols.reduce((a,b)=>a+b,0)/n;
  const volVsAvgPct=(volToday/avgVolume-1)*100;
  const periods=Math.min(14,n-1);
  let gains=0,losses=0;
  for(let i=n-periods;i<n;i++){ const d=closes[i]-closes[i-1]; if(d>0) gains+=d; else losses+=-d; }
  const avgGain=gains/periods, avgLoss=losses/periods;
  const rsi = avgLoss===0 ? 100 : Math.round(100-100/(1+avgGain/avgLoss));
  return {price,prevClose,change1dPct,change7dPct,avg30,high30,low30,
    distFromHighRangePct,distFromLowRangePct,distFromHighSimplePct,distFromLowSimplePct,
    rsi,volToday,avgVolume,volVsAvgPct};
}

/* Entry checklist: used to evaluate a possible BUY, for every stock (owned or not).
   Owned stocks can still fire this — buying more is a separate decision from exiting. */
function entryBuyChecklist(ind){
  return [
    {text:'Price is below its 30-day average',pass: ind.price<ind.avg30},
    {text:'Price is close to its 30-day low',pass: ind.distFromLowRangePct<=25},
    {text:`RSI is relatively low (${ind.rsi})`,pass: ind.rsi<40},
    {text:'Trading volume is above average',pass: ind.volToday>ind.avgVolume},
  ];
}
/* Entry checklist for a possible SELL — only used for stocks that are NOT owned
   (an entry-style "this looks toppy" read, not a real exit decision). */
function entrySellChecklist(ind){
  return [
    {text:'Price is above its 30-day average',pass: ind.price>ind.avg30},
    {text:'Price is close to its 30-day high',pass: ind.distFromHighRangePct<=25},
    {text:`RSI is relatively high (${ind.rsi})`,pass: ind.rsi>60},
    {text:'Trading volume is above average',pass: ind.volToday>ind.avgVolume},
  ];
}
/* Exit checklist — the ONLY basis for a SELL suggestion on a stock the user owns. */
function exitChecklist(ind,position){
  const profitLossUsd=position.shares*(ind.price-position.avgCost);
  const profitTargetReached=profitLossUsd>=position.target;
  const rsiHigh=ind.rsi>70;
  const closeToHigh=ind.distFromHighSimplePct>=-5;
  const checks=[
    {text:`Profit target reached (${fmtMoneyWhole(profitLossUsd)} of ${fmtMoneyWhole(position.target)})`,pass:profitTargetReached},
    {text:`RSI is relatively high (${ind.rsi})`,pass:rsiHigh},
    {text:'Price is close to its 30-day high',pass:closeToHigh},
  ];
  return {checks,profitTargetReached,sellFires: profitTargetReached && (rsiHigh||closeToHigh)};
}

function computeSuggestion(ind,position){
  const buyChecks=entryBuyChecklist(ind);
  const buyPass=buyChecks.filter(c=>c.pass).length;

  if(!position){
    // Not owned: unchanged 4-condition entry logic (buy vs. sell read, whichever the data supports).
    const sellChecks=entrySellChecklist(ind);
    const sellPass=sellChecks.filter(c=>c.pass).length;
    if(buyPass>=3) return {type:'buy',checklist:buyChecks,pass:buyPass,total:4};
    if(sellPass>=3) return {type:'sell',checklist:sellChecks,pass:sellPass,total:4};
    return buyPass>=sellPass
      ? {type:'wait',checklist:buyChecks,pass:buyPass,total:4}
      : {type:'wait',checklist:sellChecks,pass:sellPass,total:4};
  }

  // Owned: SELL is decided by the 3-condition exit checklist only. BUY (buy more) can
  // still fire from the entry checklist. Exit is checked first since it's the higher-stakes call.
  const exit=exitChecklist(ind,position);
  const exitPass=exit.checks.filter(c=>c.pass).length;
  if(exit.sellFires) return {type:'sell',checklist:exit.checks,pass:exitPass,total:3};
  if(buyPass>=3) return {type:'buy',checklist:buyChecks,pass:buyPass,total:4};
  return {type:'wait',checklist:exit.checks,pass:exitPass,total:3,
    note: exit.profitTargetReached ? 'Profit target reached — consider your plan.' : null};
}

/* ============ Sample watchlist ============ */
const STOCK_CONFIGS=[
  {ticker:'TSLA',name:'Tesla, Inc.',startPrice:258.40,endPrice:231.85,gapPrevDayPrice:247.10,volBase:98,volTodayMult:1.42,warning:true,
    position:{shares:6,avgCost:265.00,target:300}},
  {ticker:'NVDA',name:'NVIDIA Corporation',startPrice:132.80,endPrice:121.35,volBase:210,volTodayMult:0.78,warning:false,position:null},
  {ticker:'JPM',name:'JPMorgan Chase & Co.',startPrice:182.60,endPrice:197.50,volBase:8.4,volTodayMult:1.31,warning:false,
    position:{shares:20,avgCost:178.40,target:400}},
  {ticker:'META',name:'Meta Platforms, Inc.',startPrice:521.30,endPrice:611.75,volBase:15,volTodayMult:0.66,warning:false,position:null},
  {ticker:'AAPL',name:'Apple Inc.',startPrice:183.10,endPrice:185.90,amplitude:6.5,bumps:2.4,volBase:54,volTodayMult:0.84,warning:false,
    position:{shares:12,avgCost:172.30,target:250}},
  {ticker:'MSFT',name:'Microsoft Corporation',startPrice:406.40,endPrice:405.60,amplitude:-10,bumps:2.6,volBase:21,volTodayMult:1.02,warning:false,
    position:{shares:5,avgCost:402.10,target:150}},
  {ticker:'AMZN',name:'Amazon.com, Inc.',startPrice:179.30,endPrice:181.60,amplitude:6.2,bumps:2.3,volBase:38,volTodayMult:0.74,warning:false,position:null},
  {ticker:'DIS',name:'The Walt Disney Company',startPrice:96.10,endPrice:94.90,amplitude:-4.2,bumps:2.5,volBase:9.1,volTodayMult:0.97,warning:false,position:null},
  {ticker:'NFLX',name:'Netflix, Inc.',startPrice:691.40,endPrice:695.80,amplitude:11.5,bumps:2.7,volBase:3.2,volTodayMult:0.88,warning:false,position:null},
  {ticker:'RKLB',name:'Rocket Lab USA, Inc.',startPrice:24.10,endPrice:27.85,volBase:12,volTodayMult:1.08,warning:false,position:null,days:14},
];

let STOCKS={};
let chartState=null;
let state={tradeSide:'buy',portfolioEmpty:false,dataState:'live'};

function buildStocksData(){
  STOCK_CONFIGS.forEach(cfg=>{
    STOCKS[cfg.ticker]={
      ticker:cfg.ticker,name:cfg.name,history:genHistory(cfg),
      warning:!!cfg.warning,position:cfg.position?Object.assign({},cfg.position):null,
    };
  });
}

/* ============ Charts (hand-built SVG, shared x-axis, hover crosshair) ============ */
function buildCharts(hist,ind,position){
  const n=hist.length, W=680, priceH=190, volH=60, pad=8;
  const pTop=10, pBottom=priceH-16;
  const slot=(W-2*pad)/n;
  const xs=[]; for(let i=0;i<n;i++) xs.push(pad+slot*i+slot/2);
  const closes=hist.map(h=>h.close), vols=hist.map(h=>h.volume);
  let minP=Math.min(...closes,ind.avg30,position?position.avgCost:Infinity);
  let maxP=Math.max(...closes,ind.avg30,position?position.avgCost:-Infinity);
  const rangeP=(maxP-minP)||1; minP-=rangeP*0.1; maxP+=rangeP*0.1;
  const yPrice=v=> pBottom-((v-minP)/(maxP-minP))*(pBottom-pTop);
  const maxVol=Math.max(...vols);
  const volBarH=v=> (v/maxVol)*(volH-10);

  const pathD=xs.map((x,i)=>`${i===0?'M':'L'}${x.toFixed(1)},${yPrice(closes[i]).toFixed(1)}`).join(' ');
  const avgY=yPrice(ind.avg30).toFixed(1);
  let userAvgLine='', userAvgLegend='';
  if(position){
    const uy=yPrice(position.avgCost).toFixed(1);
    userAvgLine=`<line x1="${pad}" y1="${uy}" x2="${W-pad}" y2="${uy}" stroke="var(--accent)" stroke-width="1.4" stroke-dasharray="4 3"/>
      <text x="${W-pad-4}" y="${(parseFloat(uy)-5).toFixed(1)}" text-anchor="end" font-size="10.5" fill="var(--accent)" font-family="'Public Sans',sans-serif" font-weight="600">Your avg ${fmtPrice(position.avgCost)}</text>`;
    userAvgLegend=`<span class="chart-legend__item"><span class="chart-legend__swatch" style="background:var(--accent)"></span>Your average cost</span>`;
  }
  let grid='';
  for(let g=0;g<3;g++){ const gy=(pTop+(pBottom-pTop)*g/2).toFixed(1); grid+=`<line x1="${pad}" y1="${gy}" x2="${W-pad}" y2="${gy}" stroke="var(--border)" stroke-width="1"/>`; }
  const lastX=xs[n-1].toFixed(1), lastY=yPrice(closes[n-1]).toFixed(1);

  const priceSvg=`<svg class="chart-svg" id="chart-price-svg" viewBox="0 0 ${W} ${priceH}" style="aspect-ratio:${W}/${priceH}" preserveAspectRatio="none">
    ${grid}
    <line x1="${pad}" y1="${avgY}" x2="${W-pad}" y2="${avgY}" stroke="var(--ink-faint)" stroke-width="1.3" stroke-dasharray="3 3"/>
    ${userAvgLine}
    <path d="${pathD}" fill="none" stroke="var(--ink)" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
    <circle cx="${lastX}" cy="${lastY}" r="4" fill="var(--ink)" stroke="var(--surface)" stroke-width="1.5"/>
    <line id="chart-guide-price" x1="0" y1="0" x2="0" y2="${priceH}" stroke="var(--ink-faint)" stroke-width="1" stroke-dasharray="2 3" opacity="0"/>
    <circle id="chart-hover-dot" r="4.5" fill="var(--accent)" stroke="var(--surface)" stroke-width="1.5" opacity="0"/>
  </svg>`;

  const bars=xs.map((x,i)=>{
    const h=volBarH(vols[i]).toFixed(1);
    const barw=Math.max(2,slot*0.5).toFixed(1);
    const isToday=i===n-1;
    return `<rect data-i="${i}" x="${(x-barw/2).toFixed(1)}" y="${(volH-6-h).toFixed(1)}" width="${barw}" height="${h}" rx="1" fill="${isToday?'var(--accent)':'var(--border-strong)'}"/>`;
  }).join('');
  const volSvg=`<svg class="chart-svg" id="chart-vol-svg" viewBox="0 0 ${W} ${volH}" style="aspect-ratio:${W}/${volH};margin-top:6px" preserveAspectRatio="none">
    ${bars}
    <line id="chart-guide-vol" x1="0" y1="0" x2="0" y2="${volH}" stroke="var(--ink-faint)" stroke-width="1" stroke-dasharray="2 3" opacity="0"/>
  </svg>`;

  chartState={n,xs,closes,vols,dates:hist.map(h=>h.date),yPrice};

  const firstLabel=fmtDateShort(hist[0].date), midLabel=fmtDateShort(hist[Math.floor(n/2)].date), lastLabel=fmtDateShort(hist[n-1].date);

  return `<div class="chart-legend">
      <span class="chart-legend__item"><span class="chart-legend__swatch" style="background:var(--ink)"></span>Price</span>
      <span class="chart-legend__item"><span class="chart-legend__swatch" style="background:var(--ink-faint);border-top:1px dashed var(--ink-faint);height:0"></span>30-day average</span>
      ${userAvgLegend}
    </div>
    <div class="chart-wrap" id="chart-wrap">
      ${priceSvg}${volSvg}
      <div class="chart-tooltip" id="chart-tooltip"></div>
    </div>
    <div style="display:flex;justify-content:space-between;font-size:11px;color:var(--ink-faint);margin-top:5px">
      <span>${firstLabel}</span><span>${midLabel}</span><span>${lastLabel}</span>
    </div>`;
}

function onChartPointerMove(e){
  const wrap=document.getElementById('chart-wrap');
  if(!wrap||!chartState) return;
  const rect=wrap.getBoundingClientRect();
  if(e.clientX<rect.left||e.clientX>rect.right||e.clientY<rect.top||e.clientY>rect.bottom){ hideChartHover(); return; }
  const ratio=(e.clientX-rect.left)/rect.width;
  const i=Math.min(chartState.n-1,Math.max(0,Math.round(ratio*chartState.n-0.5)));
  showChartHover(i,rect);
}
function hideChartHover(){
  const tt=document.getElementById('chart-tooltip'); if(tt) tt.classList.remove('is-visible');
  const gp=document.getElementById('chart-guide-price'); if(gp) gp.setAttribute('opacity','0');
  const gv=document.getElementById('chart-guide-vol'); if(gv) gv.setAttribute('opacity','0');
  const hd=document.getElementById('chart-hover-dot'); if(hd) hd.setAttribute('opacity','0');
  document.querySelectorAll('#chart-vol-svg rect[data-i]').forEach((r,i,arr)=>{
    r.setAttribute('fill', Number(r.dataset.i)===arr.length-1?'var(--accent)':'var(--border-strong)');
  });
}
function showChartHover(i,wrapRect){
  const x=chartState.xs[i];
  const gp=document.getElementById('chart-guide-price');
  const gv=document.getElementById('chart-guide-vol');
  const hd=document.getElementById('chart-hover-dot');
  if(gp){gp.setAttribute('x1',x);gp.setAttribute('x2',x);gp.setAttribute('opacity','1');}
  if(gv){gv.setAttribute('x1',x);gv.setAttribute('x2',x);gv.setAttribute('opacity','1');}
  if(hd){hd.setAttribute('cx',x);hd.setAttribute('cy',chartState.yPrice(chartState.closes[i]));hd.setAttribute('opacity','1');}
  document.querySelectorAll('#chart-vol-svg rect[data-i]').forEach(r=>{
    r.setAttribute('fill', Number(r.dataset.i)===i?'var(--accent)':'var(--border-strong)');
  });
  const tt=document.getElementById('chart-tooltip');
  if(tt){
    tt.innerHTML=`<div style="font-weight:600;margin-bottom:3px">${fmtDateLong(chartState.dates[i])}</div>
      <div class="chart-tooltip__row"><span class="chart-tooltip__dim">Close</span><span>${fmtPrice(chartState.closes[i])}</span></div>
      <div class="chart-tooltip__row"><span class="chart-tooltip__dim">Volume</span><span>${fmtVol(chartState.vols[i])}</span></div>`;
    tt.style.left=((x/680)*wrapRect.width)+'px';
    tt.style.top='-6px';
    tt.classList.add('is-visible');
  }
}

/* ============ Panel builders ============ */
function indicatorsHtml(ind){
  const rowsL=[
    ['Current price',fmtPrice(ind.price)],
    ['1-day change',fmtPct(ind.change1dPct)],
    ['7-day change',fmtPct(ind.change7dPct)],
    ['30-day average',fmtPrice(ind.avg30)],
    ['30-day high',fmtPrice(ind.high30)],
    ['30-day low',fmtPrice(ind.low30)],
  ];
  const rowsR=[
    ['Distance from 30-day high',fmtPct(ind.distFromHighSimplePct)],
    ['Distance from 30-day low',fmtPct(ind.distFromLowSimplePct)],
    ['RSI (14-day)',String(ind.rsi)],
    ["Today's volume",fmtVol(ind.volToday)],
    ['Average volume',fmtVol(ind.avgVolume)],
    ['Volume vs. average',fmtPct(ind.volVsAvgPct)],
  ];
  const col=rows=>rows.map(([k,v])=>`<div class="ind-row"><dt>${k}</dt><dd class="num">${v}</dd></div>`).join('');
  return `<div class="indicators"><dl>${col(rowsL)}</dl><dl>${col(rowsR)}</dl></div>`;
}

function positionHtml(position,ind){
  const currentValue=position.shares*ind.price;
  const invested=position.shares*position.avgCost;
  const pl=currentValue-invested;
  const plPct=pl/invested*100;
  const progress=Math.max(0,Math.min(100,pl/position.target*100));
  const plClass=pl>=0?'pl-pos':'pl-neg';
  return `<div class="panel">
    <div class="panel__title">Your position</div>
    <div class="position-grid">
      <div><div class="position-item__label">Shares held</div><div class="position-item__value num">${fmtShares(position.shares)}</div></div>
      <div><div class="position-item__label">Average purchase price</div><div class="position-item__value num">${fmtPrice(position.avgCost)}</div></div>
      <div><div class="position-item__label">Amount invested</div><div class="position-item__value num">${fmtMoney(invested)}</div></div>
      <div><div class="position-item__label">Current value</div><div class="position-item__value num">${fmtMoney(currentValue)}</div></div>
      <div><div class="position-item__label">Profit / loss</div><div class="position-item__value num ${plClass}">${fmtMoneySigned(pl)}</div></div>
      <div><div class="position-item__label">Profit / loss %</div><div class="position-item__value num ${plClass}">${fmtPct(plPct)}</div></div>
    </div>
    <div class="progress-block">
      <div class="progress-block__row"><span>Progress to profit target</span><strong class="num">${pl>=0?fmtMoney(pl):'$0.00'} of ${fmtMoney(position.target)}</strong></div>
      <div class="progress-track"><div class="progress-fill" style="width:${progress}%"></div></div>
    </div>
  </div>`;
}

function newsHtml(ticker){
  return `<div class="panel">
    <div class="panel__title">News &amp; further reading</div>
    <div class="news-links">
      <a class="news-link" href="https://finance.yahoo.com/quote/${ticker}" target="_blank" rel="noopener">Yahoo Finance ${ICON.external}</a>
      <a class="news-link" href="https://www.google.com/finance/quote/${ticker}:NASDAQ" target="_blank" rel="noopener">Google Finance ${ICON.external}</a>
      <a class="news-link" href="https://www.google.com/search?q=${ticker}+investor+relations" target="_blank" rel="noopener">Investor relations ${ICON.external}</a>
    </div>
    <div class="news-reminder">Unusual price moves can be caused by company news that these numbers cannot explain.</div>
  </div>`;
}

function summaryStripHtml(inv,val,pl,plPct){
  return `<div class="summary-strip">
    <div class="summary-tile"><div class="summary-tile__label">Total invested</div><div class="summary-tile__value num">${fmtMoney(inv)}</div></div>
    <div class="summary-tile"><div class="summary-tile__label">Total current value</div><div class="summary-tile__value num">${fmtMoney(val)}</div></div>
    <div class="summary-tile"><div class="summary-tile__label">Total profit / loss</div><div class="summary-tile__value num ${pl>=0?'pl-pos':'pl-neg'}">${fmtMoneySigned(pl)}</div><div class="summary-tile__sub ${pl>=0?'pl-pos':'pl-neg'}">${fmtPct(plPct)}</div></div>
  </div>`;
}

/* ============ Dashboard ============ */
function renderDashboard(){
  const list=Object.values(STOCKS).map(stock=>{
    if(stock.history.length<30) return {stock,insufficient:true};
    const ind=computeIndicators(stock.history);
    const sug=computeSuggestion(ind,stock.position);
    return {stock,ind,sug,insufficient:false};
  });
  const rank=r=> r.insufficient?2:(r.sug.type==='wait'?1:0);
  list.sort((a,b)=>rank(a)-rank(b));

  const owned=list.filter(r=>r.stock.position && !r.insufficient);
  const totalInvested=owned.reduce((s,r)=>s+r.stock.position.shares*r.stock.position.avgCost,0);
  const totalValue=owned.reduce((s,r)=>s+r.stock.position.shares*r.ind.price,0);
  const totalPl=totalValue-totalInvested;
  const totalPlPct=totalInvested?totalPl/totalInvested*100:0;
  document.getElementById('dashboard-summary').innerHTML = owned.length? summaryStripHtml(totalInvested,totalValue,totalPl,totalPlPct) : '';

  const rowsHtml=list.map(r=>{
    const stock=r.stock;
    if(r.insufficient){
      return `<tr class="row-clickable" tabindex="0" data-ticker="${stock.ticker}">
        <td><div class="stock-id"><div><div class="stock-id__ticker">${stock.ticker}</div><div class="stock-id__name">${stock.name}</div></div></div></td>
        <td class="num">${fmtPrice(stock.history[stock.history.length-1].close)}</td>
        <td class="num"><span class="dash">-</span></td>
        <td>${badgeHtml('insufficient')}</td>
        <td class="num"><span class="dash">-</span></td>
      </tr>`;
    }
    const ind=r.ind, sug=r.sug, pos=stock.position;
    let plCell='<span class="dash">-</span>';
    if(pos){
      const currentValue=pos.shares*ind.price, invested=pos.shares*pos.avgCost, pl=currentValue-invested, plPct=pl/invested*100;
      plCell=`<span class="${pl>=0?'pl-pos':'pl-neg'}">${fmtMoneySigned(pl)} <span style="color:var(--ink-faint)">(${fmtPct(plPct)})</span></span>`;
    }
    return `<tr class="row-clickable" tabindex="0" data-ticker="${stock.ticker}">
      <td><div class="stock-id">${stock.warning?`<span class="warn-flag" title="Sharp recent price move, check news">${ICON.warnTri}</span>`:''}<div><div class="stock-id__ticker">${stock.ticker}</div><div class="stock-id__name">${stock.name}</div></div></div></td>
      <td class="num">${fmtPrice(ind.price)}</td>
      <td class="num">${trendHtml(ind.change1dPct)}</td>
      <td>${badgeHtml(sug.type)}</td>
      <td class="num">${plCell}</td>
    </tr>`;
  }).join('');
  document.getElementById('dashboard-rows').innerHTML=rowsHtml;
  bindRowClicks(document.getElementById('dashboard-rows'));
}

function bindRowClicks(container){
  container.querySelectorAll('tr[data-ticker]').forEach(tr=>{
    tr.addEventListener('click',()=>openDetail(tr.dataset.ticker));
    tr.addEventListener('keydown',e=>{ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); openDetail(tr.dataset.ticker); } });
  });
}

/* ============ Stock detail ============ */
function renderDetailContent(ticker){
  const stock=STOCKS[ticker];
  const insufficient=stock.history.length<30;
  const price=stock.history[stock.history.length-1].close;
  const prevClose=stock.history[stock.history.length-2]?stock.history[stock.history.length-2].close:price;
  const change1dPct=(price-prevClose)/prevClose*100;

  const warnEl=document.getElementById('detail-warnbanner');
  warnEl.innerHTML = (!insufficient && stock.warning) ? `<div class="warn-banner">${ICON.warnTri}<div><div class="warn-banner__title">Sharp recent price move, check the news before acting</div><div class="warn-banner__sub">${ticker} moved ${fmtPct(change1dPct)} today. Large single-day moves are sometimes driven by news that these numbers can't capture.</div></div></div>` : '';

  const head=document.getElementById('detail-head');
  const bodyWrap=document.getElementById('detail-body-wrap');

  if(insufficient){
    head.innerHTML=`<div>
        <div class="detail-head__id"><span class="detail-head__ticker">${ticker}</span><span class="detail-head__name">${stock.name}</span></div>
        <div class="detail-head__pricerow"><span class="detail-head__price num">${fmtPrice(price)}</span>${trendHtml(change1dPct)}</div>
        <div class="detail-head__badgewrap">${badgeHtml('insufficient',{lg:true})}</div>
        <div class="detail-head__timestamp">${freshnessLabel()}</div>
      </div>
      <div class="checklist-box">
        <div class="checklist-box__title">Why</div>
        <div class="insufficient-box">${ICON.clockLg}
          <div><div class="insufficient-box__title">Not enough data yet</div>
          <div class="insufficient-box__sub">Needs 30 days of price history to generate a suggestion. Currently tracking ${stock.history.length} of 30 days, check back in ${30-stock.history.length} more trading days.</div></div>
        </div>
      </div>`;
    bodyWrap.innerHTML=`<div class="detail-body">
        <div><div class="panel"><div class="chart-empty">${ICON.chartEmpty}<div>Not enough price history yet to draw a chart.</div></div></div></div>
        <div>${newsHtml(ticker)}</div>
      </div>`;
    chartState=null;
    return;
  }

  const ind=computeIndicators(stock.history);
  const sug=computeSuggestion(ind,stock.position);
  const checklistHtml=sug.checklist.map(c=>`<li class="${c.pass?'is-pass':'is-fail'}"><span class="checklist__icon">${c.pass?ICON.check:ICON.cross}</span><span>${c.text}</span></li>`).join('');
  const noteHtml=sug.note?`<div class="insufficient-box__sub" style="margin-top:10px">${sug.note}</div>`:'';

  head.innerHTML=`<div>
      <div class="detail-head__id"><span class="detail-head__ticker">${ticker}</span><span class="detail-head__name">${stock.name}</span></div>
      <div class="detail-head__pricerow"><span class="detail-head__price num">${fmtPrice(ind.price)}</span>${trendHtml(ind.change1dPct)}</div>
      <div class="detail-head__badgewrap">${badgeHtml(sug.type,{lg:true})}</div>
      <div class="detail-head__timestamp">${freshnessLabel()}</div>
    </div>
    <div class="checklist-box">
      <div class="checklist-box__title">Why &middot; ${sug.pass} of ${sug.total} conditions met</div>
      <ul class="checklist">${checklistHtml}</ul>
      ${noteHtml}
    </div>`;

  const chartsHtml=buildCharts(stock.history,ind,stock.position);
  const mainCol=`<div class="panel">
      <div class="panel__title">30-day price &amp; volume<span class="panel__title-sub">Closing prices, delayed up to 15 minutes</span></div>
      ${chartsHtml}
    </div>
    <div class="panel"><div class="panel__title">Indicators</div>${indicatorsHtml(ind)}</div>`;
  const sideCol=(stock.position?positionHtml(stock.position,ind):'')+newsHtml(ticker);
  bodyWrap.innerHTML=`<div class="detail-body"><div>${mainCol}</div><div>${sideCol}</div></div>`;
}

/* ============ Portfolio ============ */
function renderPortfolio(){
  const container=document.getElementById('portfolio-content');
  const sub=document.getElementById('portfolio-sub');
  if(state.portfolioEmpty){
    sub.textContent='No trades recorded yet';
    container.innerHTML=`<div class="empty-state">${ICON.inboxLg}
      <h2>No trades recorded yet</h2>
      <p>Your watchlist has stocks, but you haven't logged any trades. Add your first trade to start tracking positions, profit and loss, and progress toward your targets.</p>
      <button class="btn btn-primary" id="empty-add-trade">${ICON.plus}Add trade</button>
    </div>`;
    document.getElementById('empty-add-trade').addEventListener('click',()=>openModal());
    return;
  }
  const owned=Object.values(STOCKS).filter(s=>s.position);
  sub.textContent=owned.length+' position'+(owned.length===1?'':'s');
  let totalInvested=0, totalValue=0;
  const rows=owned.map(stock=>{
    const ind=computeIndicators(stock.history);
    const sug=computeSuggestion(ind,stock.position);
    const pos=stock.position;
    const currentValue=pos.shares*ind.price, invested=pos.shares*pos.avgCost, pl=currentValue-invested, plPct=pl/invested*100;
    totalInvested+=invested; totalValue+=currentValue;
    const distToTarget=Math.max(0,pos.target-pl);
    return `<tr class="row-clickable" tabindex="0" data-ticker="${stock.ticker}">
      <td><div class="stock-id__ticker">${stock.ticker}</div><div class="stock-id__name">${stock.name}</div></td>
      <td class="num">${fmtShares(pos.shares)}</td>
      <td class="num">${fmtPrice(pos.avgCost)}</td>
      <td class="num">${fmtMoney(invested)}</td>
      <td class="num">${fmtMoney(currentValue)}</td>
      <td class="num"><span class="${pl>=0?'pl-pos':'pl-neg'}">${fmtMoneySigned(pl)} <span style="color:var(--ink-faint)">(${fmtPct(plPct)})</span></span></td>
      <td class="num">${pl>=pos.target?'Goal reached':fmtMoney(distToTarget)+' to go'}</td>
      <td>${badgeHtml(sug.type)}</td>
    </tr>`;
  }).join('');
  const totalPl=totalValue-totalInvested, totalPlPct=totalInvested?totalPl/totalInvested*100:0;
  container.innerHTML=`${summaryStripHtml(totalInvested,totalValue,totalPl,totalPlPct)}
    <div style="display:flex;justify-content:flex-end;margin-bottom:14px">
      <button class="btn btn-primary" id="portfolio-add-trade">${ICON.plus}Add trade</button>
    </div>
    <div class="table-card"><div class="table-scroll"><table class="grid">
      <thead><tr><th>Stock</th><th class="num">Shares</th><th class="num">Avg cost</th><th class="num">Invested</th><th class="num">Current value</th><th class="num">P/L</th><th class="num">To target</th><th>Suggestion</th></tr></thead>
      <tbody>${rows}</tbody>
    </table></div></div>`;
  document.getElementById('portfolio-add-trade').addEventListener('click',()=>openModal());
  bindRowClicks(container);
}

/* ============ Navigation ============ */
function navigateTo(page){
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('is-active'));
  document.getElementById('page-'+page).classList.add('is-active');
  document.querySelectorAll('.appbar__tab').forEach(t=>{
    if(t.dataset.nav===page) t.setAttribute('aria-current','page'); else t.removeAttribute('aria-current');
  });
  window.scrollTo({top:0,behavior:'auto'});
}
function openDetail(ticker){
  navigateTo('detail');
  document.querySelectorAll('.appbar__tab').forEach(t=>t.removeAttribute('aria-current'));
  renderDetailContent(ticker);
  const pdStock=document.getElementById('pd-stock');
  if(pdStock) pdStock.value=ticker;
}

/* ============ Freshness / data-state ============ */
function freshnessLabel(){
  if(state.dataState==='stale') return 'Data as of Tuesday, 4:15 PM (stale)';
  if(state.dataState==='refreshing') return 'Refreshing, last update Wednesday, 2:47 PM';
  return 'Data as of Wednesday, 2:47 PM';
}
function setDataState(s){
  state.dataState=s;
  const dot=document.getElementById('freshness-dot');
  const text=document.getElementById('freshness-text');
  const banner=document.getElementById('global-banner');
  dot.classList.remove('is-refreshing','is-stale');
  if(s==='live'){ banner.hidden=true; }
  else if(s==='refreshing'){ dot.classList.add('is-refreshing'); banner.hidden=true; }
  else if(s==='stale'){ dot.classList.add('is-stale'); banner.hidden=false; }
  text.textContent=freshnessLabel();
  document.querySelectorAll('#pd-datastate button').forEach(b=>b.classList.toggle('is-active',b.dataset.state===s));
  const activePage=document.querySelector('.page.is-active');
  if(activePage && activePage.id==='page-detail'){
    const ticker=document.getElementById('pd-stock').value;
    if(ticker) renderDetailContent(ticker);
  }
}

/* ============ Modal ============ */
function openModal(prefillTicker){
  const overlay=document.getElementById('modal-overlay');
  const select=document.getElementById('trade-stock');
  select.innerHTML='<option value="" disabled selected>Choose a stock</option>'+Object.values(STOCKS).map(s=>`<option value="${s.ticker}">${s.ticker} &middot; ${s.name}</option>`).join('');
  if(prefillTicker) select.value=prefillTicker;
  document.getElementById('trade-date').value='2026-08-19';
  state.tradeSide='buy';
  document.querySelectorAll('#trade-side button').forEach(b=>b.classList.toggle('is-active',b.dataset.side==='buy'));
  updateTradePriceDefault();
  updateTradeHint();
  overlay.hidden=false;
  select.focus();
}
function closeModal(){ document.getElementById('modal-overlay').hidden=true; }
function updateTradePriceDefault(){
  const t=document.getElementById('trade-stock').value;
  if(t && STOCKS[t]) document.getElementById('trade-price').value=STOCKS[t].history[STOCKS[t].history.length-1].close.toFixed(2);
}
function updateTradeHint(){
  const t=document.getElementById('trade-stock').value;
  const owns=t && STOCKS[t] && STOCKS[t].position;
  document.getElementById('trade-hint').hidden = !(state.tradeSide==='buy' && owns);
}

/* ============ Toast ============ */
function showToast(msg){
  let t=document.getElementById('toast');
  if(!t){ t=document.createElement('div'); t.id='toast'; t.className='toast'; document.body.appendChild(t); }
  t.textContent=msg;
  t.classList.add('is-visible');
  clearTimeout(showToast._tm);
  showToast._tm=setTimeout(()=>t.classList.remove('is-visible'),2600);
}

/* ============ Wiring ============ */
function wireNav(){
  document.querySelectorAll('.appbar__tab').forEach(btn=>btn.addEventListener('click',()=>navigateTo(btn.dataset.nav)));
  document.getElementById('detail-back').addEventListener('click',()=>navigateTo('dashboard'));
}
function wireModal(){
  document.getElementById('modal-close').addEventListener('click',closeModal);
  document.getElementById('trade-cancel').addEventListener('click',closeModal);
  document.getElementById('modal-overlay').addEventListener('click',e=>{ if(e.target.id==='modal-overlay') closeModal(); });
  document.getElementById('trade-stock').addEventListener('change',()=>{ updateTradePriceDefault(); updateTradeHint(); });
  document.querySelectorAll('#trade-side button').forEach(b=>{
    b.addEventListener('click',()=>{
      document.querySelectorAll('#trade-side button').forEach(x=>x.classList.remove('is-active'));
      b.classList.add('is-active');
      state.tradeSide=b.dataset.side;
      updateTradeHint();
    });
  });
  document.getElementById('trade-save').addEventListener('click',()=>{
    const hintShown=!document.getElementById('trade-hint').hidden;
    closeModal();
    showToast(hintShown?'Trade saved, average purchase price updated.':'Trade saved.');
  });
  document.addEventListener('keydown',e=>{
    if(e.key==='Escape'){ const ov=document.getElementById('modal-overlay'); if(!ov.hidden) closeModal(); }
  });
}
function wirePreviewDock(){
  document.getElementById('preview-toggle').addEventListener('click',()=>{
    document.getElementById('preview-dock').classList.toggle('is-collapsed');
  });
  document.querySelectorAll('#pd-datastate button').forEach(b=>b.addEventListener('click',()=>setDataState(b.dataset.state)));
  const pdStock=document.getElementById('pd-stock');
  pdStock.innerHTML=Object.values(STOCKS).map(s=>`<option value="${s.ticker}">${s.ticker} &middot; ${s.name}</option>`).join('');
  pdStock.value='AAPL';
  pdStock.addEventListener('change',()=>openDetail(pdStock.value));
  document.querySelectorAll('#pd-portfolio button').forEach(b=>{
    b.addEventListener('click',()=>{
      document.querySelectorAll('#pd-portfolio button').forEach(x=>x.classList.remove('is-active'));
      b.classList.add('is-active');
      state.portfolioEmpty=b.dataset.state==='empty';
      renderPortfolio();
    });
  });
}

function init(){
  buildStocksData();
  wireNav();
  wireModal();
  wirePreviewDock();
  renderDashboard();
  renderPortfolio();
  setDataState('live');
  document.addEventListener('pointermove',onChartPointerMove);
}
init();
