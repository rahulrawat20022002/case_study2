import json, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
M=json.load(open("/tmp/claude-0/-home-claude/3f0a219a-3c0a-53e0-8360-748fb7d57569/scratchpad/metrics_all.json"))
BLUE,ORANGE,AQUA="#2a78d6","#eb6834","#1baf7a"
INK,INK2,GRID,SURF="#0b0b0b","#52514e","#e4e3df","#ffffff"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.edgecolor":INK2,"axes.labelcolor":INK,"xtick.color":INK2,"ytick.color":INK2,"axes.spines.top":False,"axes.spines.right":False})

# ---------- Fig 1: architecture ----------
fig,ax=plt.subplots(figsize=(10,6.6)); ax.set_xlim(0,100); ax.set_ylim(0,70); ax.axis("off")
def box(x,y,w,h,title,sub="",fc="#ffffff",ec="#52514e"):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.3,rounding_size=1.0",fc=fc,ec=ec,lw=1.1,zorder=3))
    if sub:
        ax.text(x+w/2,y+h*0.68,title,ha="center",va="center",fontsize=8.6,fontweight="bold",color=INK,zorder=4)
        ax.text(x+w/2,y+h*0.30,sub,ha="center",va="center",fontsize=7.3,color=INK2,linespacing=1.3,zorder=4)
    else:
        ax.text(x+w/2,y+h/2,title,ha="center",va="center",fontsize=8.2,fontweight="bold",color=INK,zorder=4)
def arr(x1,y1,x2,y2,ls="-",rad=0):
    ax.annotate("",xy=(x2,y2),xytext=(x1,y1),zorder=2,arrowprops=dict(arrowstyle="-|>",color=INK2,lw=1.1,linestyle=ls,shrinkA=1,shrinkB=1,connectionstyle=f"arc3,rad={rad}"))
def band(y,h,label):
    ax.add_patch(FancyBboxPatch((0.5,y),99,h,boxstyle="round,pad=0.2,rounding_size=1.2",fc="#f3f2ee",ec="none",zorder=0))
    ax.text(1.8,y+h-1.0,label,fontsize=7.6,color=INK2,fontweight="bold",va="top",zorder=1)
band(55.5,14,"CORPUS BUILD (once, from the frozen guidelines)")
band(27.5,26.5,"SYSTEMS UNDER TEST")
band(0.5,25.5,"EVALUATION (two independent axes)")
for x,t,sub in [(3,"Commission guidelines","Annex III draft, May 2026"),(27,"Structural chunking","400 normative chunks,\nworked examples held out"),(51,"Embed","bge-base-en-v1.5"),(75,"Index","Chroma (dense) + BM25")]:
    box(x,57,21,9,t,sub)
for x in (24,48,72): arr(x,61.5,x+3,61.5)
box(3,38,18,9,"Test input","1 of 215 descriptions\n(verdict text removed)")
box(25,38,20,9,"Hybrid retrieval","alpha 0.5, top-5 used,\ntop-10 logged")
arr(21,42.5,25,42.5)
arr(78,57,38,47.2,ls="--")
box(49,44.5,30,5,"Baseline 1: plain LLM, no retrieval")
box(49,38,30,5,"Baseline 2: RAG, generic prompt")
box(49,31.5,30,5,"Agent: RAG, step-by-step legal test",fc="#eaf2fc",ec=BLUE)
arr(12,47,49,47,ls="--",rad=-0.12); ax.text(30.5,51.0,"description only (baseline 1)",fontsize=7,color=INK2,style="italic",ha="center")
arr(45,42,49,40.5); arr(45,40.5,49,34)
box(82,30,16,11,"Generator","microsoft/phi-4\nvLLM, greedy,\npinned revision")
for y in (47,40.5,34): arr(79,y,82,35.5)
box(8,14,32,9,"Judge: RAGAS faithfulness","Qwen2.5-72B-Instruct-AWQ checks the\nexplanation against the retrieved passages")
box(56,14,32,9,"Correctness","predicted label vs the\nCommission gold label (lookup)")
arr(83,30,26,23.2); arr(90,30,74,23.2)
box(24,2.5,48,8.5,"Four-bucket matrix","right or wrong x faithful or unfaithful; off-diagonal cells are the findings")
arr(24,14,40,11.2); arr(72,14,56,11.2)
fig.savefig("fig1_architecture.png",dpi=220,bbox_inches="tight",facecolor=SURF); plt.close(fig)

# ---------- Fig 2: accuracy leaky vs redacted ----------
C=["baseline1_plain_llm","baseline2_standard_rag","agent_structured"]; L=["Baseline 1\nplain LLM","Baseline 2\nstandard RAG","Agent\nstructured RAG"]
fig,ax=plt.subplots(figsize=(6.4,3.6))
import numpy as np
x=np.arange(3); w=0.34
a=[M["leaky"][c]["acc"] for c in C]; b=[M["redacted"][c]["acc"] for c in C]
b1=ax.bar(x-w/2-0.01,a,w,color="#b9b8b2",label="Original inputs (verdict text present)",zorder=3)
b2=ax.bar(x+w/2+0.01,b,w,color=BLUE,label="Redacted inputs (verdict text removed)",zorder=3)
for bars in (b1,b2):
    for r in bars: ax.text(r.get_x()+r.get_width()/2,r.get_height()+0.01,f"{r.get_height():.3f}",ha="center",va="bottom",fontsize=8.5,color=INK)
ax.set_xticks(x); ax.set_xticklabels(L); ax.set_ylim(0,1.08); ax.set_ylabel("Accuracy (215 inputs)")
ax.yaxis.grid(True,color=GRID,zorder=0); ax.legend(frameon=False,fontsize=8,loc="upper left",bbox_to_anchor=(0,1.18),ncol=1)
fig.savefig("fig2_accuracy.png",dpi=220,bbox_inches="tight",facecolor=SURF); plt.close(fig)

# ---------- Fig 3: faithfulness right vs wrong ----------
fig,axs=plt.subplots(1,2,figsize=(8.2,3.6),sharey=True)
rng=np.random.default_rng(0)
for ax,c,t in zip(axs,["baseline2_standard_rag","agent_structured"],["Baseline 2: standard RAG","Agent: structured RAG"]):
    d=M["redacted"][c]; f=np.array(d["faith_list"]); y=np.array(d["ok_list"])
    for k,(mask,col,lab) in enumerate([(y,BLUE,"label right"),(~y,"#e34948","label wrong")]):
        v=f[mask]; xs=k+rng.uniform(-0.18,0.18,len(v))
        ax.scatter(xs,v,s=12,color=col,alpha=0.55,edgecolors="white",linewidths=0.4,zorder=3)
        ax.plot([k-0.28,k+0.28],[v.mean()]*2,color=INK,lw=2,zorder=4)
    ax.axhline(0.5,color=INK2,lw=0.8,ls="--",zorder=1); ax.text(-0.47,0.515,"faithful cut 0.5",fontsize=7,color=INK2,ha="left")
    ax.set_xticks([0,1]); ax.tick_params(axis="x",labelsize=8); ax.set_xticklabels([f"label right\nmean {f[y].mean():.2f}, n={y.sum()}",f"label wrong\nmean {f[~y].mean():.2f}, n={(~y).sum()}"]); ax.set_xlim(-0.5,1.5)
    ax.set_title(f"{t}\nAUC {d['auc']:.3f} (95% CI {d['auc_ci'][0]:.2f} to {d['auc_ci'][1]:.2f})",fontsize=9,color=INK)
    ax.yaxis.grid(True,color=GRID,zorder=0)
axs[0].set_ylabel("RAGAS faithfulness")
fig.savefig("fig3_faithfulness.png",dpi=220,bbox_inches="tight",facecolor=SURF); plt.close(fig)
print("ok")

# ================= extra figures =================
import collections
CFG_COL={"baseline1_plain_llm":"#4a3aa7","baseline2_standard_rag":"#eb6834","agent_structured":"#1baf7a"}
CFG_NAME={"baseline1_plain_llm":"Baseline 1: plain LLM","baseline2_standard_rag":"Baseline 2: standard RAG","agent_structured":"Agent: structured RAG"}
TS=[json.loads(l) for l in open("/home/claude/case_study2/test_set.jsonl")]
AREAS=["biometrics","critical-infrastructure","education","employment","essential-services","law-enforcement","migration","justice-democracy"]
ANAME={"biometrics":"1 Biometrics","critical-infrastructure":"2 Critical infra.","education":"3 Education","employment":"4 Employment","essential-services":"5 Essential services","law-enforcement":"6 Law enforcement","migration":"7 Migration","justice-democracy":"8 Justice & democracy"}

# F: dataset distribution
fig,ax=plt.subplots(figsize=(7,3.4))
hr=[sum(1 for r in TS if r["annex_iii_area"]==a and r["label"]=="high-risk") for a in AREAS]
filt=[sum(1 for r in TS if r["annex_iii_area"]==a and r["label"]!="high-risk" and r.get("edge_case_type")=="article-6-3-filter") for a in AREAS]
nhr=[sum(1 for r in TS if r["annex_iii_area"]==a and r["label"]!="high-risk") - f for a,f in zip(AREAS,filt)]
y=np.arange(len(AREAS))[::-1]
ax.barh(y,hr,color="#2a78d6",height=0.62,label="High-risk",zorder=3)
ax.barh(y,filt,left=hr,color="#eda100",height=0.62,label="Not high-risk: Article 6(3) filter case",zorder=3,edgecolor="white",linewidth=1.5)
ax.barh(y,nhr,left=[a+b for a,b in zip(hr,filt)],color="#b9b8b2",height=0.62,label="Not high-risk: other",zorder=3,edgecolor="white",linewidth=1.5)
for yi,a,b,c in zip(y,hr,filt,nhr): ax.text(a+b+c+0.6,yi,str(a+b+c),va="center",fontsize=8.5,color=INK)
ax.set_yticks(y); ax.set_yticklabels([ANAME[a] for a in AREAS]); ax.set_xlabel("Test inputs"); ax.xaxis.grid(True,color=GRID,zorder=0)
ax.legend(frameon=False,fontsize=8,loc="lower right")
fig.savefig("fig_dataset.png",dpi=220,bbox_inches="tight",facecolor=SURF); plt.close(fig)

# F: leak effect on original run: flagged vs clean
leak=set(json.load(open("/tmp/claude-0/-home-claude/3f0a219a-3c0a-53e0-8360-748fb7d57569/scratchpad/leak2.json")))
fig,ax=plt.subplots(figsize=(6.4,3.3)); x=np.arange(3); w=0.34
vals={}
for c in C:
    R={json.loads(l)["id"]:json.loads(l) for l in open(f"/tmp/claude-0/-home-claude/3f0a219a-3c0a-53e0-8360-748fb7d57569/scratchpad/full/results/runs/{c}.jsonl")}
    a1=np.mean([R[i]["pred_label"]==R[i]["gold_label"] for i in R if i in leak]); a2=np.mean([R[i]["pred_label"]==R[i]["gold_label"] for i in R if i not in leak])
    vals[c]=(a1,a2)
bA=ax.bar(x-w/2-0.01,[vals[c][0] for c in C],w,color="#e34948",label="129 inputs that state the verdict",zorder=3)
bB=ax.bar(x+w/2+0.01,[vals[c][1] for c in C],w,color="#2a78d6",label="86 clean inputs",zorder=3)
for bars in (bA,bB):
    for r in bars: ax.text(r.get_x()+r.get_width()/2,r.get_height()+0.01,f"{r.get_height():.3f}",ha="center",fontsize=8.5,color=INK)
ax.set_xticks(x); ax.set_xticklabels(L); ax.set_ylim(0,1.1); ax.set_ylabel("Accuracy (original run)"); ax.yaxis.grid(True,color=GRID,zorder=0)
ax.legend(frameon=False,fontsize=8,loc="upper left",bbox_to_anchor=(0,1.2))
fig.savefig("fig_leak.png",dpi=220,bbox_inches="tight",facecolor=SURF); plt.close(fig)

# F: per-area accuracy heatmap (redacted)
from matplotlib.colors import LinearSegmentedColormap
cmap=LinearSegmentedColormap.from_list("b",["#f6f9fe","#a9c9f1","#2a78d6","#123e7a"])
mat=np.array([[M["redacted"][c]["by_area"][a] for a in AREAS] for c in C])
fig,ax=plt.subplots(figsize=(8,2.6))
im=ax.imshow(mat,cmap=cmap,vmin=0.2,vmax=1.0,aspect="auto")
for i in range(3):
    for j in range(8):
        v=mat[i,j]; ax.text(j,i,f"{v:.2f}",ha="center",va="center",fontsize=8.5,color="white" if v>0.7 else INK)
ax.set_xticks(range(8)); ax.set_xticklabels([ANAME[a] for a in AREAS],rotation=30,ha="right",fontsize=8)
ax.set_yticks(range(3)); ax.set_yticklabels([CFG_NAME[c] for c in C],fontsize=8.5)
for s in ax.spines.values(): s.set_visible(False)
ax.set_xticks(np.arange(-.5,8,1),minor=True); ax.set_yticks(np.arange(-.5,3,1),minor=True); ax.grid(which="minor",color="white",linewidth=2); ax.tick_params(which="minor",length=0)
cb=fig.colorbar(im,ax=ax,fraction=0.03,pad=0.02); cb.set_label("Accuracy",fontsize=8); cb.ax.tick_params(labelsize=7)
fig.savefig("fig_area_heatmap.png",dpi=220,bbox_inches="tight",facecolor=SURF); plt.close(fig)

# F: four-bucket grids
fig,axs=plt.subplots(1,2,figsize=(7.4,3.1))
BK={"baseline2_standard_rag":[[110,79],[14,12]],"agent_structured":[[91,93],[17,14]]}
for ax,c in zip(axs,["baseline2_standard_rag","agent_structured"]):
    m=np.array(BK[c]); tot=m.sum()
    cols=[["#dbe8f9","#fbe3d7"],["#fbe3d7","#eceae4"]]
    for i in range(2):
        for j in range(2):
            ax.add_patch(plt.Rectangle((j,1-i),1,1,fc=cols[i][j],ec="white",lw=3))
            tag={(0,0):"right + faithful",(0,1):"right + unfaithful",(1,0):"FAITHFUL BUT WRONG",(1,1):"wrong + unfaithful"}[(i,j)]
            ax.text(j+0.5,1-i+0.6,str(m[i,j]),ha="center",va="center",fontsize=17,fontweight="bold",color=INK)
            ax.text(j+0.5,1-i+0.3,f"{tag}\n{m[i,j]/tot:.0%}",ha="center",va="center",fontsize=7.5,color="#b3261e" if (i,j)==(1,0) else INK2)
    ax.set_xlim(0,2); ax.set_ylim(0,2); ax.set_xticks([0.5,1.5]); ax.set_xticklabels(["faithful (>= 0.5)","unfaithful (< 0.5)"],fontsize=8)
    ax.set_yticks([1.5,0.5]); ax.set_yticklabels(["label right","label wrong"],fontsize=8)
    for s in ax.spines.values(): s.set_visible(False)
    ax.tick_params(length=0); ax.set_title(CFG_NAME[c],fontsize=9.5,color=INK)
fig.savefig("fig_buckets.png",dpi=220,bbox_inches="tight",facecolor=SURF); plt.close(fig)

# F: threshold sweep, share of wrong answers that pass as faithful
cuts=[0.3,0.5,0.7,0.9]
SW={"baseline2_standard_rag":[21,14,1,0],"agent_structured":[22,17,7,1]}; NW={"baseline2_standard_rag":26,"agent_structured":31}
fig,ax=plt.subplots(figsize=(5.8,3.2))
for c in SW:
    v=[k/NW[c] for k in SW[c]]
    ax.plot(cuts,v,color=CFG_COL[c],lw=2,marker="o",ms=7,markeredgecolor="white",markeredgewidth=1.5,zorder=3)
    ax.plot([],[],color=CFG_COL[c],lw=2,marker="o",label=CFG_NAME[c])
    for cx,vv,k in zip(cuts,v,SW[c]):
        up = (c=="agent_structured") != (cx==0.3)
        ax.text(cx+0.02,vv+(0.05 if up else -0.08),f"{k} of {NW[c]}",ha="left",fontsize=7.3,color=INK2)
ax.set_xlabel("Faithful cut (score counted as faithful at or above)"); ax.set_ylabel("Share of wrong answers\nthat pass as faithful")
ax.set_xticks(cuts); ax.set_xlim(0.25,1.0); ax.set_ylim(-0.1,0.95); ax.legend(frameon=False,fontsize=8,loc="upper right"); ax.yaxis.grid(True,color=GRID,zorder=0)
ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
fig.savefig("fig_sweep.png",dpi=220,bbox_inches="tight",facecolor=SURF); plt.close(fig)

# F: retrieval hit@5 by area, original vs redacted
RO={r["id"]:r for r in json.load(open("/home/claude/case_study2/results/retrieval_eval.json"))["per_row"]}
RR={r["id"]:r for r in json.load(open("/tmp/claude-0/-home-claude/3f0a219a-3c0a-53e0-8360-748fb7d57569/scratchpad/red/results/retrieval_eval_redacted.json"))["per_row"]}
fig,ax=plt.subplots(figsize=(7,3.4)); y=np.arange(len(AREAS))[::-1]; h=0.36
o=[np.mean([RO[r["id"]]["hit@5"] for r in TS if r["annex_iii_area"]==a]) for a in AREAS]
rd=[np.mean([RR[r["id"]]["hit@5"] for r in TS if r["annex_iii_area"]==a]) for a in AREAS]
ax.barh(y+h/2+0.01,o,h,color="#b9b8b2",label="Original inputs",zorder=3); ax.barh(y-h/2-0.01,rd,h,color="#2a78d6",label="Redacted inputs",zorder=3)
for yi,v in zip(y,rd): ax.text(v+0.01,yi-h/2-0.01,f"{v:.2f}",va="center",fontsize=7.5,color=INK)
ax.set_yticks(y); ax.set_yticklabels([ANAME[a] for a in AREAS]); ax.set_xlim(0,1.08); ax.set_xlabel("Hit@5 (gold section in top 5 passages)")
ax.xaxis.grid(True,color=GRID,zorder=0); ax.legend(frameon=False,fontsize=8,loc="lower left",bbox_to_anchor=(0,1.0),ncol=2)
fig.savefig("fig_retrieval_area.png",dpi=220,bbox_inches="tight",facecolor=SURF); plt.close(fig)

# F: error taxonomy
cats=[("A. Sector taken as the use case",6),("B. Article 6(3) exception not applied",4),("C. Profiling / sensitive-data rule misused",3),("D. Condition misread or fact invented",2),("E. Too cautious on a short description",2)]
fig,ax=plt.subplots(figsize=(6.4,2.6)); y=np.arange(len(cats))[::-1]
ax.barh(y,[c[1] for c in cats],color="#1baf7a",height=0.6,zorder=3)
for yi,(n,v) in zip(y,cats): ax.text(v+0.1,yi,str(v),va="center",fontsize=9,color=INK)
ax.set_yticks(y); ax.set_yticklabels([c[0] for c in cats],fontsize=8.5); ax.set_xlabel("Faithful-but-wrong answers (agent, n = 17)"); ax.set_xlim(0,7.2)
ax.xaxis.grid(True,color=GRID,zorder=0)
fig.savefig("fig_errors.png",dpi=220,bbox_inches="tight",facecolor=SURF); plt.close(fig)

# F: confusion matrices redacted
CONF={"baseline1_plain_llm":(59,60,7,89),"baseline2_standard_rag":(57,17,9,132),"agent_structured":(57,22,9,127)}
fig,axs=plt.subplots(1,3,figsize=(8.4,2.7),gridspec_kw=dict(wspace=0.08))
for ax,c in zip(axs,C):
    tp,fp,fn,tn=CONF[c]; m=np.array([[tp,fn],[fp,tn]])
    ax.imshow(m,cmap=cmap,vmin=0,vmax=150)
    for i in range(2):
        for j in range(2): ax.text(j,i,str(m[i,j]),ha="center",va="center",fontsize=12,fontweight="bold",color="white" if m[i,j]>90 else INK)
    ax.set_xticks([0,1]); ax.set_xticklabels(["pred HR","pred not HR"],fontsize=8); ax.set_yticks([0,1]); ax.set_yticklabels(["gold HR","gold not HR"] if c==C[0] else ["",""],fontsize=8)
    for s in ax.spines.values(): s.set_visible(False)
    ax.tick_params(length=0); ax.set_title(CFG_NAME[c],fontsize=9,color=INK)
fig.savefig("fig_confusion.png",dpi=220,bbox_inches="tight",facecolor=SURF); plt.close(fig)
print("extra ok")
