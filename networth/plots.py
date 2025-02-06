
import matplotlib.pyplot as plt
import io
import base64
import mpld3

def bar_chart(x_axis, y_axis, Y='Y', X='X', title='Bar Chart', y_limit=None):
    
    # Create a bar chart
    plt.switch_backend('AGG')
    plt.figure(figsize=(6, 4))
    plt.bar(x_axis, y_axis, color='silver')
    plt.xlabel(X)
    plt.ylabel(Y)
    plt.title(title)
    plt.tight_layout()
    plt.grid(True, linestyle='--', alpha=0.6)
    # Create a bar chart

    # fig, ax = plt.subplots()
    # ax.bar(x_axis, y_axis, color='skyblue')

    # # Set custom y-axis limits
    # if y_limit is not None:
    #     ax.set_ylim(y_limit[0], y_limit[1])

    # # Add labels and title
    # ax.set_xlabel(X)
    # ax.set_ylabel(Y)
    # ax.set_title(title)
    
    # Save the plot to a BytesIO object
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    # Encode the image to base64
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()

    return image_base64


def interactive_bar_chart(x_axis, y_axis, Y='Y', X='X', title='Interactive Bar Chart'):
    
    # Create a bar chart
    fig, ax = plt.subplots()
    ax.plot_date(x_axis, y_axis, color='gold')
    ax.set_xlabel(X)
    ax.set_ylabel(Y)
    ax.set_title(title)

    # Convert to interactive HTML
    html_fig = mpld3.fig_to_html(fig)
    plt.close(fig)

    return html_fig
