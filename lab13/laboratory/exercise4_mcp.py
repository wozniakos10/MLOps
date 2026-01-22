import base64
import io
from typing import Annotated

import matplotlib.pyplot as plt
from fastmcp import FastMCP

mcp = FastMCP("Visualization Server")


@mcp.tool(description="Create a line plot from given data and return it as a base64-encoded PNG image")
def line_plot(
    data: Annotated[list[list[float]], "One or more lists of numbers to plot as lines"],
    title: Annotated[str | None, "Title of the plot"] = None,
    x_label: Annotated[str | None, "Label for the X axis"] = None,
    y_label: Annotated[str | None, "Label for the Y axis"] = None,
    legend: Annotated[bool, "Whether to show the legend"] = False,
) -> str:
    """Creates a line plot from the provided data and returns it as a base64-encoded PNG."""
    
    # Create the figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot each data series
    for i, series in enumerate(data):
        ax.plot(series, label=f"Series {i + 1}")
    
    # Apply optional parameters
    if title:
        ax.set_title(title)
    if x_label:
        ax.set_xlabel(x_label)
    if y_label:
        ax.set_ylabel(y_label)
    if legend:
        ax.legend()
    
    ax.grid(True, alpha=0.3)
    
    # Save plot to a bytes buffer
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=100, bbox_inches="tight")
    buffer.seek(0)
    
    # Encode as base64
    image_base64 = base64.b64encode(buffer.read()).decode("utf-8")
    
    # Clean up
    plt.close(fig)
    
    return image_base64


if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8004)
