# Poolmap GUI

This is a Python tool for analyzing liquidity pools on the BitShares decentralized exchange (DEX). It calculates token prices, finds optimal trading paths between tokens, and visualizes the liquidity pool network. The tool includes a Tkinter-based graphical user interface (GUI) for easy interaction, allowing users to input token pairs, run analyses, and generate transactions.

## Features
- **Price Calculation**: Computes token prices relative to a base token using liquidity pool data.
- **Trading Path Finder**: Identifies the best trading path between two tokens based on pool liquidity.
- **Network Visualization**: Generates an interactive HTML visualization of the liquidity pool network using PyVis.
- **GUI Interface**: Provides a user-friendly Tkinter GUI to input token pairs, view results, and save transactions.
- **Mock and Live Data**: Supports mock data for testing and live data via BitShares RPC and web requests.
- **Transaction Building**: Generates JSON-formatted transactions for trading along the identified path.

## Prerequisites
- Python 3.8+
- Required Python packages:
  - `networkx`
  - `pyvis`
  - `requests`
  - `bitshares`
  - `numpy`
- BitShares node access (for live data mode)
- A modern web browser (for viewing PyVis visualizations)

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/usefuljohn/liquidity_pool_map.git
   cd liquidity_pool_map
   ```
2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the GUI script:
   ```bash
   python gui.py
   ```
2. In the GUI:
   - Enter the source token (e.g., `BTWTY.EOS`) in the "From Token" field.
   - Enter the target token (e.g., `IOB.XRP`) in the "To Token" field.
   - Click "Run Analysis" to compute the trading path and price.
   - View the results in the text area.
   - Click "Save Transaction" to generate a JSON transaction (currently only displayed in the GUI).
3. If the `plot=True` option is enabled in `poolmap.py`, an HTML file (`liquidity_pool_map.html`) will be generated and displayed with an interactive network visualization.


### Example Output
For a trading path from `BTWTY.EOS` to `IOB.XRP` using mock data:
```
PATHS
Symbol           Price        Path
IOB.XRP          0.123456     BTWTY.EOS -> BTS -> IOB.XRP
```

The GUI will display similar output, and clicking "Save Transaction" will produce a JSON transaction like:
```json
[
  {
    "amount_to_sell": 1,
    "min_to_receive": 0.5,
    "pool": "1.19.4"
  },
  {
    "amount_to_sell": 0.5,
    "min_to_receive": 0.123456,
    "pool": "1.19.5"
  }
]
final price: 8.097165
```

## Project Structure
- `poolmap.py`: Core logic for graph construction, price calculation, and pathfinding.
- `gui.py`: Tkinter GUI for user interaction.
- `rpc.py`: RPC and WebSocket utilities for BitShares node communication.
- `min_to_receive.py`: Transaction calculation logic.
- `liquidity_pool_map.html`: Generated visualization file (when `plot=True`).

## Mock Data
The project includes mock data for testing without a BitShares node:
- Mock pools: BTS-USD, USD-EUR, EUR-GOLD, XBTSX.USDT-BTS, BTS-HONEST.MONEY.
- Mock precisions: Token symbols and their precision values.

To use this data, set `mock=True` when calling the `main` function in `poolmap.py`.

## Limitations
- The `argparse` section in `poolmap.py` is commented out; re-enable for command-line use.
- Live data requires a stable BitShares node connection.
- The GUI currently prints transactions to the console; saving to a file is a TODO.
- Visualization is limited to PyVis network graphs; embedding this into the tkinter GUI is not yet implemented.
