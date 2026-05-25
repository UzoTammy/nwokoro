import matplotlib.pyplot as plt
import io
import base64
import random


def _plot(plt):
    # Save the plot to a BytesIO object
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    # Encode the image to base64
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()
    return image_base64
  
_PALETTE = ['#33548a', '#1e3a5f', '#4a7fb5', '#2d6a9f', '#1a4a7a', '#5b8db8', '#7aafd4']


def bar_chart(x_axis: list, y_axis: list, Y='Y', X='X', title='Bar Chart', y_min=None):
    plt.switch_backend('AGG')
    fig, ax = plt.subplots(figsize=(5.5, 3.5))
    colors = (_PALETTE * ((len(x_axis) // len(_PALETTE)) + 1))[:len(x_axis)]
    ax.barh(x_axis, y_axis, color=colors, height=0.55)
    ax.set_title(title, fontsize=11, color='#1e293b', pad=8, fontweight='bold')
    ax.set_xlabel(Y, fontsize=9, color='#64748b')
    ax.tick_params(axis='y', labelsize=9, colors='#1e293b')
    ax.tick_params(axis='x', labelsize=8, colors='#64748b')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#e2e8f0')
    ax.spines['bottom'].set_color('#e2e8f0')
    ax.grid(axis='x', linestyle='--', alpha=0.5, color='#e2e8f0')
    if y_min:
        ax.set_xlim(left=y_min)
    plt.tight_layout()
    return _plot(plt)


def donut_chart(labels: list, sizes: list):
    plt.switch_backend('AGG')
    colors = (_PALETTE * ((len(labels) // len(_PALETTE)) + 1))[:len(labels)]
    fig, ax = plt.subplots(figsize=(4.5, 3.5))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors,
        autopct='%1.1f%%', startangle=90,
        wedgeprops={'edgecolor': 'white', 'linewidth': 1.5},
        textprops={'fontsize': 9, 'color': '#1e293b'},
        pctdistance=0.78
    )
    for at in autotexts:
        at.set_fontsize(8)
        at.set_color('white')
    centre_circle = plt.Circle((0, 0), 0.60, fc='white')
    ax.add_artist(centre_circle)
    ax.set_title('', fontsize=10)
    ax.axis('equal')
    plt.tight_layout()
    return _plot(plt)

def plot(x_axis, y_axis1, y_axis2=None, Y1='Y', Y2=None, X='X', title='Bar Chart', y_min=None):
    # Create a bar chart
    plt.switch_backend('AGG')
    plt.figure(figsize=(6, 4))
    plt.xlabel(X)
    plt.plot(x_axis, y_axis1, label=Y1, color='dodgerblue', marker='s')
    # plt.ylabel(Y1)
    if y_axis2 is not None:
        plt.plot(x_axis, y_axis2, linestyle='-', color='red', marker='o', label=Y2)
    plt.title(title)
    plt.legend(loc='center')
    plt.tight_layout()
    plt.grid(True, linestyle='--', alpha=0.6)
    if y_min:
        plt.ylim(bottom=y_min)
    # plt.show()
    return _plot(plt)


