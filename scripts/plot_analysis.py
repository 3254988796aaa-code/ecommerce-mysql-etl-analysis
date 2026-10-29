"""Export readable static figures from prepared CSV without changing sources."""
import argparse
import csv
from pathlib import Path


def plot(products_file,output_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.ticker import FuncFormatter
    with Path(products_file).open(encoding="utf-8",newline="") as stream:
        rows=list(csv.DictReader(stream))
    output_dir=Path(output_dir);output_dir.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({"font.size":11,"axes.spines.top":False,"axes.spines.right":False,
                         "figure.facecolor":"white","axes.titleweight":"bold"})
    prices=np.array([float(row["product_price"]) for row in rows])
    fig,ax=plt.subplots(figsize=(9,4.5),layout="constrained")
    ax.hist(prices,bins=np.geomspace(prices.min(),prices.max()*1.001,55),color="#176b87",edgecolor="white",linewidth=.3)
    ax.set_xscale("log");ax.set(title="Listed prices have a long right tail",xlabel="Listed price (CNY, logarithmic scale)",ylabel="Distinct feature records")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda x,_:f"{x:g}"))
    ax.grid(axis="y",alpha=.15)
    fig.savefig(output_dir/"price_distribution.png",dpi=160);plt.close(fig)
    labels=["0–49.99","50–99.99","100–199.99","200–499.99","500+"]
    counts=np.histogram(prices,bins=[0,50,100,200,500,float("inf")])[0]
    fig,ax=plt.subplots(figsize=(9,4.5),layout="constrained")
    bars=ax.bar(labels,counts,color="#176b87")
    ax.bar_label(bars,labels=[f"{n:,} ({n/len(rows):.1%})" for n in counts],padding=4,fontsize=10)
    ax.set(title="Price bands after exact feature deduplication",xlabel="Listed price band (CNY)",ylabel="Distinct feature records",ylim=(0,max(counts)*1.18))
    ax.grid(axis="y",alpha=.15);ax.set_axisbelow(True)
    fig.savefig(output_dir/"price_bands.png",dpi=160);plt.close(fig)
    fields=["repeat_customer_index","old_shop_index","product_name_length","product_price","payment_count"]
    labels=["Repeat index","Shop age index","Title length","Listed price","Displayed payers"]
    matrix=np.corrcoef(np.array([[float(r[key]) for key in fields] for r in rows]).T)
    fig,ax=plt.subplots(figsize=(7,6),layout="constrained")
    img=ax.imshow(matrix,cmap="RdBu_r",vmin=-1,vmax=1)
    ax.set(xticks=range(5),yticks=range(5),xticklabels=labels,yticklabels=labels,title="Exploratory Pearson correlations")
    plt.setp(ax.get_xticklabels(),rotation=30,ha="right")
    for i in range(5):
        for j in range(5):
            ax.text(j,i,f"{matrix[i,j]:.2f}",ha="center",va="center",color="white" if abs(matrix[i,j])>.6 else "#222222")
    fig.colorbar(img,ax=ax,shrink=.8,label="Pearson r")
    fig.savefig(output_dir/"correlations.png",dpi=160);plt.close(fig)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",default="reports/run/products.csv")
    parser.add_argument("--output",default="reports/figures")
    args=parser.parse_args();plot(args.input,args.output)
