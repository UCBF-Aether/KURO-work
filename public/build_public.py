#!/usr/bin/env python3
"""Build the public 'Talk to the Fly' single-file web toy.

Embeds the real FlyWire/VFB subgraphs (touch, looming, rotten, sugar
motor-backward) + a toy spread-of-activation simulator in JS + a modeled
word->circuit lexicon. Output: public/index.html, deployable static.
"""
import json
import os
import re

BASE = os.path.dirname(os.path.abspath(__file__))
SG = os.path.join(BASE, "..", "subgraphs")

CIRCUITS = [
    ("touch", "touch.json", 0, None),
    ("looming", "looming.json", 0, None),
    ("rotten", "rotten.json", 0, None),
    ("sugar", "sugar_backward.json", -1,
     "Motor-backward trace, honestly labeled: the sweet-sensing GRN's forward "
     "link is not indexed in the VFB database (documented gap), so this shows "
     "the real pre-motor chain that drives proboscis extension, injected at "
     "the pre-motor layer."),
]

LEXICON = {
    "touch": ["touch", "tap", "brush", "stroke", "press", "pressure", "vibration",
              "buzz", "poke", "tickle", "feel", "caress", "bump", "jolt", "graze"],
    "looming": ["looming", "shadow", "approach", "dark", "swoop", "threat",
                "hawk", "hand", "giant", "escape", "startle"],
    "rotten": ["rotten", "rot", "mold", "mould", "stink", "bitter", "sour",
               "spoiled", "disgust", "foul", "stench", "geosmin"],
    "sugar": ["sugar", "sweet", "honey", "nectar", "taste", "candy", "delicious",
              "syrup", "sucrose", "yummy"],
}


def short_name(name):
    n = name
    n = re.sub(r"^adult\s+", "", n)
    n = re.sub(r"\s+neuron$", "", n)
    n = re.sub(r"\s+lineage$", "", n)
    n = n.replace("subesophageal zone", "SEZ")
    n = n.replace("subesophageal sensory", "SEZ sensory")
    n = n.replace("gnathal ganglion", "gnathal")
    n = n.replace("olfactory receptor neuron Or", "olfactory receptor")
    n = n.replace("lobula plate-lobula columnar neuro", "LPLC")
    n = n.replace("Johnston organ", "JO")
    if len(n) > 26:
        n = n[:25].rstrip() + "\u2026"
    return n


def main():
    circuits = {}
    for key, fname, inject_hop, gap in CIRCUITS:
        g = json.load(open(os.path.join(SG, fname)))
        nodes = [{"id": n["id"], "name": n["name"], "short": short_name(n["name"]),
                  "hop": n.get("hop", 0)} for n in g["nodes"]]
        edges = [{"pre": e["pre"], "post": e["post"], "w": e["weight"]}
                 for e in g["edges"]]
        circuits[key] = {
            "key": key,
            "title": g.get("stimulus", key).split(" (")[0],
            "inject_hop": inject_hop,
            "nodes": nodes,
            "edges": edges,
            "behavior": g.get("behavior", {}).get("text", ""),
            "narration": g.get("fly_narration", ""),
            "gap": gap,
        }

    data_js = "const CIRCUITS=" + json.dumps(circuits, separators=(",", ":")) + ";\n"
    data_js += "const LEXICON=" + json.dumps(LEXICON, separators=(",", ":")) + ";\n"

    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Talk to the Fly</title>
<style>
  :root{--bg:#05070d;--panel:#0b1020;--ink:#e8f4ff;--dim:#8fa3bf;--gold:#ffc857;--cyan:#59d6ff;--green:#7dff9a;--pink:#ff7d9a;}
  *{box-sizing:border-box}
  body{margin:0;background:radial-gradient(1200px 700px at 50% -10%,#0d1630 0%,var(--bg) 60%);color:var(--ink);
       font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;min-height:100vh;
       display:flex;flex-direction:column;align-items:center}
  header{text-align:center;padding:34px 16px 8px;max-width:760px}
  h1{margin:0;font-size:clamp(28px,5vw,46px);letter-spacing:.06em;font-weight:800}
  h1 .fly{color:var(--gold)}
  .sub{color:var(--dim);margin-top:10px;font-size:15px;line-height:1.55}
  .sub b{color:var(--ink)}
  main{width:min(1060px,96vw);margin:18px auto 40px}
  .card{background:rgba(11,16,32,.86);border:1px solid #1c2a4d;border-radius:16px;padding:18px;margin-bottom:16px;
        box-shadow:0 10px 40px rgba(0,0,0,.45)}
  .tabs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:6px}
  .tab{cursor:pointer;border:1px solid #2a3c68;background:#101a36;color:var(--ink);border-radius:999px;
       padding:8px 16px;font-size:14px;letter-spacing:.03em;transition:.15s}
  .tab:hover{border-color:var(--gold)}
  .tab.active{background:var(--gold);color:#14100a;border-color:var(--gold);font-weight:700}
  .row{display:flex;gap:10px;flex-wrap:wrap;margin-top:14px}
  input[type=text]{flex:1;min-width:220px;background:#060b18;border:1px solid #2a3c68;color:var(--ink);
       border-radius:12px;padding:13px 16px;font-size:16px;outline:none}
  input[type=text]:focus{border-color:var(--gold)}
  button.go{background:var(--gold);border:none;color:#14100a;font-weight:800;font-size:15px;letter-spacing:.04em;
       border-radius:12px;padding:13px 22px;cursor:pointer}
  button.go:hover{filter:brightness(1.08)}
  button.ghost{background:transparent;border:1px solid #2a3c68;color:var(--dim);border-radius:12px;
       padding:13px 16px;font-size:14px;cursor:pointer}
  button.ghost:hover{color:var(--ink);border-color:var(--dim)}
  #canvas{width:100%;height:430px;display:block;border-radius:12px;background:#04060c;border:1px solid #14204a}
  .parse{font-size:13.5px;color:var(--dim);margin:10px 2px 0;min-height:20px}
  .parse b{color:var(--gold)}
  .parse .tag{display:inline-block;font-size:11px;border:1px solid #3a4f80;border-radius:6px;padding:1px 7px;margin-left:6px;color:var(--cyan)}
  .readout{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}
  @media(max-width:700px){.readout{grid-template-columns:1fr}}
  .readout .box{background:#060b18;border:1px solid #14204a;border-radius:12px;padding:12px 14px;font-size:14px;line-height:1.55}
  .box h3{margin:0 0 6px;font-size:12px;letter-spacing:.14em;color:var(--dim);text-transform:uppercase}
  .box.behavior b{color:var(--green)}
  .box.narr b{color:var(--pink)}
  .gapnote{margin-top:12px;font-size:13px;color:var(--dim);border-left:3px solid var(--gold);padding:8px 12px;background:#0a0f22;border-radius:0 10px 10px 0}
  .gapnote b{color:var(--gold)}
  .steps{display:flex;gap:6px;margin:10px 2px 0;align-items:center;font-size:12.5px;color:var(--dim)}
  .stepdot{width:26px;height:26px;border-radius:50%;border:1px solid #2a3c68;display:flex;align-items:center;justify-content:center;font-size:12px}
  .stepdot.on{background:var(--gold);color:#14100a;border-color:var(--gold);font-weight:800}
  footer{max-width:760px;padding:0 16px 60px;color:var(--dim);font-size:12.8px;line-height:1.7}
  footer h2{font-size:13px;letter-spacing:.16em;color:var(--ink);margin:26px 0 8px;text-transform:uppercase}
  footer .lbl{display:inline-block;font-size:10.5px;font-weight:800;letter-spacing:.1em;border-radius:6px;padding:2px 8px;margin-right:8px;vertical-align:middle}
  .real{background:#123b22;color:var(--green)} .toy{background:#3b2a12;color:var(--gold)}
  .mod{background:#12283b;color:var(--cyan)} .fict{background:#3b1220;color:var(--pink)}
  footer p{margin:8px 0}
  footer a{color:var(--cyan)}
  .credit{text-align:center;color:#5b6d8f;margin-top:30px;font-size:12px}
</style>
</head>
<body>
<header>
  <h1>TALK TO THE <span class="fly">FLY</span></h1>
  <div class="sub">Type a word. Its <b>real Drosophila neurons</b> light up \u2014 wired from the actual
  FlyWire connectome, simulated with an honest toy model. This fly doesn't have feelings;
  it has <b>synapses</b>. Watch them fire.</div>
</header>
<main>
  <div class="card">
    <div class="tabs" id="tabs"></div>
    <div class="row">
      <input type="text" id="word" placeholder='Try: touch, sweet, rot, looming, tickle, honey, shadow\u2026' autocomplete="off">
      <button class="go" id="go">STIMULATE</button>
      <button class="ghost" id="poke" title="Send a random stimulus word">&#127926; poke the fly</button>
    </div>
    <div class="parse" id="parse"></div>
    <canvas id="canvas"></canvas>
    <div class="steps" id="steps"></div>
    <div class="readout">
      <div class="box behavior"><h3>What the circuit does <span class="lbl toy">textbook</span></h3><div id="behavior"></div></div>
      <div class="box narr"><h3>The fly's one-liner <span class="lbl fict">fiction</span></h3><div id="narr"></div></div>
    </div>
    <div class="gapnote" id="gapnote" style="display:none"><b>Honest gap:</b> <span id="gaptext"></span></div>
  </div>
</main>
<footer>
  <h2>The honesty contract</h2>
  <p><span class="lbl real">REAL</span>Every node and edge below comes from the Virtual Fly Brain query API
  against the <b>FlyWire FAFB v783</b> Drosophila connectome (class-aggregated connectivity, edge weight =
  total synapse count). No neuron, synapse, or connection was invented. Data frozen Oct 2026.</p>
  <p><span class="lbl toy">TOY</span>The dynamics are a toy: normalized spread-of-activation with a 0.15 firing
  threshold. No biophysics \u2014 no leak, no inhibition, no neurotransmitter signs, no timing. It answers one
  question: given the real wiring and a stimulus at the sensory layer, which named populations light up, in what order?</p>
  <p><span class="lbl mod">MODELED</span>The word\u2192circuit mapping is a hand-built keyword lexicon \u2014 my
  modeling choice, not biology. The fly never saw your word; the circuit fired because I mapped it there.</p>
  <p><span class="lbl fict">FICTION</span>The one-liner "fly voice" is a narrative gloss. Flies do not have feelings
  we can access. The behavior line is textbook biology for the identified terminal circuit, stated as known biology.</p>
  <p><span class="lbl real">GAPS</span>Documented, not hidden: the sweet-sensing gustatory receptor neuron's forward
  link is not indexed in the VFB database, so the sugar tab shows the real <b>motor-backward</b> chain
  (SEZ/premotor \u2192 proboscis motor neuron) injected at the pre-motor layer. The missing link is recorded in the
  build log, not faked.</p>
  <div class="credit">Built by Muse \u00b7 real wiring: FlyWire FAFB v783 via Virtual Fly Brain \u00b7 no flies were harmed</div>
</footer>
<script>
DATA_PLACEHOLDER
</script>
<script>
"use strict";
const $=id=>document.getElementById(id);
const keys=Object.keys(CIRCUITS);
let cur=keys[0], steps=[], stepIdx=0, timer=null;

// ---- tabs ----
const tabs=$("tabs");
keys.forEach(k=>{
  const b=document.createElement("button");
  b.className="tab"+(k===cur?" active":"");
  b.textContent=CIRCUITS[k].title.toUpperCase();
  b.onclick=()=>{cur=k;[...tabs.children].forEach((c,i)=>c.classList.toggle("active",keys[i]===k));renderMeta();};
  tabs.appendChild(b);
});

// ---- toy simulator (port of flysim.py) ----
function simulate(g){
  const idx={}; g.nodes.forEach((n,i)=>idx[n.id]=i);
  const out={}; g.edges.forEach(e=>out[e.pre]=(out[e.pre]||0)+e.w);
  const norm=g.edges.map(e=>({pre:idx[e.pre],post:idx[e.post],f:out[e.pre]?e.w/out[e.pre]:0}));
  let act=g.nodes.map(n=>n.hop===g.inject_hop?1:0);
  const snaps=[act.slice()];
  for(let s=0;s<4;s++){
    const nxt=g.nodes.map(()=>0);
    norm.forEach(e=>{const a=act[e.pre]; if(a>0) nxt[e.post]+=a*e.f;});
    for(let i=0;i<nxt.length;i++) if(nxt[i]<0.15) nxt[i]=0;
    act=nxt; snaps.push(act.slice());
  }
  return snaps;
}
function parseWord(w){
  w=(w||"").toLowerCase().trim();
  if(!w) return null;
  for(const k of keys){
    if(LEXICON[k].some(v=>w===v||w.includes(v)||v.includes(w)&&w.length>3)) return k;
  }
  return null;
}
function renderMeta(){
  const g=CIRCUITS[cur];
  $("behavior").innerHTML="<b></b>"+g.behavior;
  $("narr").innerHTML="<b>\u201c"+g.narration+"\u201d</b>";
  const gn=$("gapnote");
  if(g.gap){gn.style.display="block";$("gaptext").textContent=g.gap;}
  else gn.style.display="none";
}
function fire(label){
  const g=CIRCUITS[cur];
  steps=simulate(g); stepIdx=0;
  if(timer) clearInterval(timer);
  timer=setInterval(()=>{stepIdx++; if(stepIdx>=steps.length){clearInterval(timer);} draw(); renderSteps();},850);
  draw(); renderSteps(); renderMeta();
}
function renderSteps(){
  const names=["inject","hop 1","hop 2","hop 3","hop 4"];
  $("steps").innerHTML="cascade: "+names.map((n,i)=>
    `<span class="stepdot${i<=stepIdx?" on":""}">${i}</span><span>${n}</span>`).join(" ");
}
$("go").onclick=()=>{const w=$("word").value; const k=parseWord(w);
  if(k){cur=k;[...tabs.children].forEach((c,i)=>c.classList.toggle("active",keys[i]===k));
    $("parse").innerHTML=`\u201c${w}\u201d \u2192 <b>${CIRCUITS[k].title}</b> circuit<span class="tag">MODELED parse</span>`; fire();}
  else{$("parse").innerHTML=w?`No circuit for \u201c${w}\u201d \u2014 try <b>touch, sweet, rot, looming</b> (or poke the fly).`:"Type a word first, or poke the fly.";}
};
$("word").addEventListener("keydown",e=>{if(e.key==="Enter")$("go").click();});
$("poke").onclick=()=>{const all=[].concat(...keys.map(k=>LEXICON[k]));const w=all[Math.floor(Math.random()*all.length)];
  $("word").value=w;$("go").click();};

// ---- canvas rendering ----
const cv=$("canvas"), ctx=cv.getContext("2d");
function fit(){const r=cv.getBoundingClientRect();const d=window.devicePixelRatio||1;
  cv.width=r.width*d;cv.height=r.height*d;ctx.setTransform(d,0,0,d,0,0);}
window.addEventListener("resize",()=>{fit();draw();});
function colOf(h){const g=CIRCUITS[cur];const hops=[...new Set(g.nodes.map(n=>n.hop))].sort((a,b)=>a-b);
  return hops.indexOf(h);}
function draw(){
  fit();
  const g=CIRCUITS[cur];
  const W=cv.getBoundingClientRect().width,H=cv.getBoundingClientRect().height;
  const hops=[...new Set(g.nodes.map(n=>n.hop))].sort((a,b)=>a-b);
  const cols=hops.map(h=>g.nodes.filter(n=>n.hop===h));
  const pos={};
  cols.forEach((col,ci)=>{
    const x=W*(ci+1)/(cols.length+1);
    col.forEach((n,ni)=>{
      const y=H*(ni+1)/(col.length+1);
      pos[n.id]={x,y,node:n};
    });
  });
  // edges
  const act=steps[stepIdx]||[];
  const idx={}; g.nodes.forEach((n,i)=>idx[n.id]=i);
  const out={}; g.edges.forEach(e=>out[e.pre]=(out[e.pre]||0)+e.w);
  g.edges.forEach(e=>{
    const a=pos[e.pre],b=pos[e.post]; if(!a||!b)return;
    const f=out[e.pre]?e.w/out[e.pre]:0;
    const heat=(act[idx[e.pre]]||0)*f;
    ctx.strokeStyle=heat>0.05?`rgba(255,200,87,${Math.min(0.95,0.25+heat)})`:"rgba(70,95,150,0.28)";
    ctx.lineWidth=heat>0.05?1+6*heat:1;
    ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();
  });
  // nodes
  g.nodes.forEach(n=>{
    const p=pos[n.id]; const a=act[idx[n.id]]||0;
    const inj=n.hop===g.inject_hop;
    const r=inj?11:8+5*a;
    if(a>0.02){const gr=ctx.createRadialGradient(p.x,p.y,0,p.x,p.y,r*3);
      gr.addColorStop(0,`rgba(255,200,87,${0.55*Math.min(1,a)})`);gr.addColorStop(1,"rgba(255,200,87,0)");
      ctx.fillStyle=gr;ctx.beginPath();ctx.arc(p.x,p.y,r*3,0,7);ctx.fill();}
    ctx.fillStyle=a>0.02?"#ffc857":(inj?"#ffd98a":"#2c3d66");
    ctx.strokeStyle=a>0.02?"#ffe9b8":"#16224a";ctx.lineWidth=1.5;
    ctx.beginPath();ctx.arc(p.x,p.y,r,0,7);ctx.fill();ctx.stroke();
    ctx.fillStyle=a>0.02?"#0c0a04":"#b9c6e4";
    ctx.font="600 10.5px system-ui";ctx.textAlign="center";
    ctx.fillText(n.short,p.x,p.y-r-7);
    if(a>0.02){ctx.fillStyle="#ffe9b8";ctx.font="700 10px system-ui";ctx.fillText(a.toFixed(2),p.x,p.y+3.5);}
  });
  // hop labels
  ctx.fillStyle="#5b6d8f";ctx.font="600 10px system-ui";ctx.textAlign="center";
  hops.forEach(h=>{const x=W*(colOf(h)+1)/(cols.length+1);
    ctx.fillText(h===g.inject_hop?"SENSORY / INJECT":"hop "+h,x,16);});
}
renderMeta();
</script>
</body>
</html>
"""
    html = html.replace("DATA_PLACEHOLDER", data_js)
    out = os.path.join(BASE, "index.html")
    with open(out, "w") as f:
        f.write(html)
    print("wrote", out, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
