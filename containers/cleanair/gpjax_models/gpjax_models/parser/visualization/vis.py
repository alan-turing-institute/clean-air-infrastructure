import typer
from pathlib import Path
from ...results.vis import (
    Visualization,
)

app = typer.Typer(help="Visualazation for model results")
app = typer.Typer()


def run_visualization_process(input_dir: Path, data_type: str):
    """
    Run the entire visualization process (loading, preparing, and visualizing).

    Args:
        input_dir (Path): Path to the input data directory.
        data_type (str): Type of data to visualize, e.g., 'with_satellite', 'with_traffic', etc.
    """
    try:
        typer.echo(
            f"Initializing visualization for {data_type} with data from {input_dir}"
        )

        # Initialize the visualization object
        vis = Visualization(input_dir, data_type)

        # Load data and results
        vis.load_data()
        vis.load_results()

        # Prepare data
        vis.prepare_data()

        # Call the appropriate visualization method based on data_type
        if data_type == "with_traffic":
            vis.visualize_with_traffic_data()
        elif data_type == "with_satellite":
            vis.visualize_with_sat_data()
        elif data_type == "test_data":
            vis.visualize_with_test_data()
        elif data_type == "default":
            vis.visualize_default()
        else:
            raise ValueError(f"Unsupported data_type: {data_type}")

    except AttributeError as e:
        typer.echo(
            f"AttributeError: {e}. Check if the correct visualization method exists."
        )
        raise
    except FileNotFoundError as e:
        typer.echo(f"FileNotFoundError: {e}. Check if files exist in {input_dir}")
        raise
    except ValueError as ve:
        typer.echo(f"Error during visualization process: {ve}")
        raise
    except Exception as e:
        typer.echo(f"Error visualizing the results: {e}")
        raise


@app.command()
def satellite(
    input_dir: Path = typer.Option(
        ..., help="Input directory containing the data files"
    ),
):
    """
    Visualize satellite data.
    """
    typer.echo(f"Visualizing satellite data from {input_dir}")
    run_visualization_process(input_dir, "with_satellite")


@app.command()
def traffic(
    input_dir: Path = typer.Option(
        ..., help="Input directory containing the data files"
    ),
):
    """
    Visualize traffic data.
    """
    typer.echo(f"Visualizing traffic data from {input_dir}")
    run_visualization_process(input_dir, "with_traffic")


@app.command()
def test_data(
    input_dir: Path = typer.Option(
        ..., help="Input directory containing the data files"
    ),
):
    """
    Visualize test data.
    """
    typer.echo(f"Visualizing test data from {input_dir}")
    run_visualization_process(input_dir, "test_data")


@app.command()
def default(
    input_dir: Path = typer.Option(
        ..., help="Input directory containing the data files"
    ),
):
    """
    Run default visualization.
    """
    typer.echo(f"Running default visualization from {input_dir}")
    run_visualization_process(input_dir, "default")


if __name__ == "__main__":
    app()
