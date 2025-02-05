
import matplotlib.pyplot as plt
import io
import base64
import urllib


def bar_chart(x_axis, y_axis, Y='Y', X='X', title='Bar Chart'):
    
    # Create a bar chart
    plt.switch_backend('AGG')
    plt.figure(figsize=(6, 4))
    plt.bar(x_axis, y_axis, color='maroon')
    plt.xlabel(X)
    plt.ylabel(Y)
    plt.title(title)
    plt.tight_layout()

    # Save the plot to a BytesIO object
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    # Encode the image to base64
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()

    return image_base64
