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
  
def bar_chart(x_axis, y_axis, Y='Y', X='X', title='Bar Chart', y_min=None):
    
    # Create a bar chart
    plt.switch_backend('AGG')
    plt.figure(figsize=(6, 4))
    plt.bar(x_axis, y_axis, color='skyblue')
    plt.xlabel(X)
    plt.ylabel(Y)
    plt.title(title)
    plt.tight_layout()
    plt.grid(True, linestyle='--', alpha=0.6)
    if y_min:
        plt.ylim(bottom=y_min)
    # Create a bar chart

    return _plot(plt)

def donut_chart(labels:list, sizes:list):

    colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ce868c', '#5a59a5', '#848e31']

    if len(labels) == len(sizes): 
        colors = random.sample(colors, len(labels))
        
    # Create a donut chart
    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90, wedgeprops={'edgecolor': 'white'})

    # Add a white circle at the center
    centre_circle = plt.Circle((0, 0), 0.70, fc='white')
    ax.add_artist(centre_circle)

    # Equal aspect ratio
    ax.axis('equal')

    return _plot(plt)

