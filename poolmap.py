import math
import heapq
import itertools
import json
import requests
import argparse
import ssl
from bitshares import BitShares
import networkx as nx
import numpy as np
from pyvis.network import Network


def constant_product_output(dx, x_reserve, y_reserve):
    """Uniswap-style formula"""
    return (y_reserve / x_reserve) * dx


def build_graph(pools):
    """
    Builds a MultiGraph where each edge represents a liquidity pool between two assets.
    """
    G = nx.MultiGraph()
    for pool_id, (bal_a, bal_b, asset_a, asset_b, _, _) in pools.items():
        if bal_a and bal_b:
            G.add_edge(
                asset_a,
                asset_b,
                pool=pool_id,
                bal_a=bal_a,
                bal_b=bal_b,
                asset_a=asset_a,
                asset_b=asset_b,
            )
    return G


def bootstrap_prices_from_core(G, base_token="BTS"):
    """
    Bootstraps token prices by propagating outward from a base token.
    """
    prices = {base_token: 1.0}
    token_paths = {base_token: [base_token]}
    pool_paths = {base_token: []}
    visited_pools = set()
    heap = []

    for u, v, data in G.edges(data=True):
        if base_token not in (data["asset_a"], data["asset_b"]):
            continue
        pool_id = data["pool"]
        if pool_id in visited_pools:
            continue
        visited_pools.add(pool_id)

        known_token = base_token
        unknown_token = (
            data["asset_b"] if data["asset_a"] == known_token else data["asset_a"]
        )
        known_balance = (
            data["bal_a"] if data["asset_a"] == known_token else data["bal_b"]
        )
        unknown_balance = (
            data["bal_b"] if data["asset_a"] == known_token else data["bal_a"]
        )

        if unknown_balance == 0:
            continue

        implied_price = prices[known_token] * known_balance / unknown_balance
        pool_value_in_bts = (
            known_balance * prices[known_token] + unknown_balance * implied_price
        )

        heapq.heappush(
            heap,
            (
                -pool_value_in_bts,
                pool_id,
                known_token,
                unknown_token,
                implied_price,
                [base_token, unknown_token],
                [pool_id],
            ),
        )

    while heap:
        (
            neg_value,
            pool_id,
            known_token,
            unknown_token,
            implied_price,
            token_path,
            pool_path,
        ) = heapq.heappop(heap)

        if unknown_token in prices:
            continue

        prices[unknown_token] = implied_price
        token_paths[unknown_token] = token_path
        pool_paths[unknown_token] = pool_path

        for u, v, data in G.edges(data=True):
            if data["pool"] in visited_pools:
                continue
            if unknown_token not in (data["asset_a"], data["asset_b"]):
                continue

            visited_pools.add(data["pool"])

            known = unknown_token
            other = data["asset_b"] if data["asset_a"] == known else data["asset_a"]
            known_balance = (
                data["bal_a"] if data["asset_a"] == known else data["bal_b"]
            )
            unknown_balance = (
                data["bal_b"] if data["asset_a"] == known else data["bal_a"]
            )

            if unknown_balance == 0 or other in prices:
                continue

            implied_price = prices[known] * known_balance / unknown_balance
            pool_value = (
                known_balance * prices[known] + unknown_balance * implied_price
            )

            heapq.heappush(
                heap,
                (
                    -pool_value,
                    data["pool"],
                    known,
                    other,
                    implied_price,
                    token_path + [other],
                    pool_path + [data["pool"]],
                ),
            )

    return prices, token_paths, pool_paths


def load_pool_data():
    data = requests.get(
        "https://raw.githubusercontent.com/squidKid-deluxe/bitshares-networks/refs/heads/gh-pages/pools/pipe/pool_cache.txt"
    ).text
    data = data.split("<<< JSON IPC >>>")[1]
    data = json.loads(data)
    data = [
        (pool_id, info["share_asset"], info["asset_a"], info["asset_b"])
        for pool_id, info in data.items()
    ]
    return data


def load_precisions():
    data = requests.get(
        "https://raw.githubusercontent.com/squidKid-deluxe/bitshares-networks/refs/heads/gh-pages/pools/pipe/name_cache.txt"
    ).text
    data = data.split("<<< JSON IPC >>>")[1]
    data = json.loads(data)
    return data


def rpc_chunk_objects(rpc, ids, limit=100):
    chunks = [ids[i : i + limit] for i in range(0, len(ids), limit)]
    results = {}
    print(f"Requesting {len(chunks)} chunks...\n")
    for chunk_num, chunk in enumerate(chunks, start=1):
        print(f"\033[A{chunk_num}")
        try:
            objects = rpc.rpc.get_objects(chunk)
            for obj in objects:
                if obj:
                    results[obj["id"]] = obj
        except Exception as e:
            print(f"An error occurred processing chunk {chunk_num}: {e}")
    return results


def parse_pool_data(data, cache):
    results = {}
    for info in data.values():
        results[info["id"]] = (
            int(info["balance_a"]) / 10 ** cache[info["asset_a"]]["precision"],
            int(info["balance_b"]) / 10 ** cache[info["asset_b"]]["precision"],
            int(info["taker_fee_percent"]) / 100,
            int(info["withdrawal_fee_percent"]) / 100,
            info["asset_a"],
            info["asset_b"],
        )
    return results


def format_thousands(number):
    return f"{number:,}"

def sigfig(number, precision=6):
    if number == 0:
        return "0"
    return format_thousands(
        round(number, precision - int(math.floor(math.log10(abs(number)))))
    )

def generate_all_prices(rpc, pools, cache, core, mock=False):
    if mock:
        pool_data = parse_pool_data(mock_rpc_chunk_objects(pools), cache)
    else:
        pool_data = parse_pool_data(rpc_chunk_objects(rpc, pools), cache)

    balance_data = {
        pool_id: (
            balance_info[0],
            balance_info[1],
            int(balance_info[4].rsplit(".", 1)[1]),
            int(balance_info[5].rsplit(".", 1)[1]),
            balance_info[2],
            balance_info[3],
        )
        for pool_id, balance_info in zip(pool_data.keys(), pool_data.values())
    }
    graph = build_graph(balance_data)
    return bootstrap_prices_from_core(graph, core), balance_data, graph

def load_mock_pool_data():
    return [
        ("1.19.1", "LP_SHARE_1", "1.3.0", "1.3.1"),
        ("1.19.2", "LP_SHARE_2", "1.3.1", "1.3.2"),
        ("1.19.3", "LP_SHARE_3", "1.3.2", "1.3.3"),
        ("1.19.4", "LP_SHARE_4", "1.3.121", "1.3.0"), # XBTSX.USDT-BTS
        ("1.19.5", "LP_SHARE_5", "1.3.0", "1.3.861"), # BTS-HONEST.MONEY
    ]

def load_mock_precisions():
    return {
        "1.3.0": {"symbol": "BTS", "precision": 5},
        "1.3.1": {"symbol": "USD", "precision": 4},
        "1.3.2": {"symbol": "EUR", "precision": 4},
        "1.3.3": {"symbol": "GOLD", "precision": 6},
        "1.3.121": {"symbol": "XBTSX.USDT", "precision": 6},
        "1.3.861": {"symbol": "HONEST.MONEY", "precision": 6},
    }

def mock_rpc_chunk_objects(ids):
    return {
        "1.19.1": {
            "id": "1.19.1", "balance_a": "100000000", "balance_b": "10000000",
            "asset_a": "1.3.0", "asset_b": "1.3.1", "taker_fee_percent": "10", "withdrawal_fee_percent": "0",
        },
        "1.19.2": {
            "id": "1.19.2", "balance_a": "50000000", "balance_b": "4500000",
            "asset_a": "1.3.1", "asset_b": "1.3.2", "taker_fee_percent": "10", "withdrawal_fee_percent": "0",
        },
        "1.19.3": {
            "id": "1.19.3", "balance_a": "20000000", "balance_b": "100000",
            "asset_a": "1.3.2", "asset_b": "1.3.3", "taker_fee_percent": "10", "withdrawal_fee_percent": "0",
        },
        "1.19.4": { # XBTSX.USDT-BTS
            "id": "1.19.4", "balance_a": "1000000000", "balance_b": "100000000",
            "asset_a": "1.3.121", "asset_b": "1.3.0", "taker_fee_percent": "10", "withdrawal_fee_percent": "0",
        },
        "1.19.5": { # BTS-HONEST.MONEY
            "id": "1.19.5", "balance_a": "500000000", "balance_b": "50000000",
            "asset_a": "1.3.0", "asset_b": "1.3.861", "taker_fee_percent": "10", "withdrawal_fee_percent": "0",
        },
    }

def main():
    parser = argparse.ArgumentParser(
        description="Find best trading paths in BitShares DEX."
    )
    parser.add_argument(
        "--from", dest="from_token", default="XBTSX.USDT", help="The token to trade from."
    )
    parser.add_argument(
        "--to", dest="to_token", default="HONEST.MONEY", help="The token to trade to."
    )
    parser.add_argument(
        "--mock", action="store_true", help="Use mock data instead of live data."
    )
    args = parser.parse_args()

    print("\033c")
    if args.mock:
        data = load_mock_pool_data()
        cache = load_mock_precisions()
        rpc = None
    else:
        data = load_pool_data()
        cache = load_precisions()
        rpc = BitShares("wss://api.bts.mobi/ws", nobroadcast=True)

    if not any(v["symbol"] == args.from_token for v in cache.values()):
        print(f"Invalid 'from' token: {args.from_token}")
        return

    if not any(v["symbol"] == args.to_token for v in cache.values()):
        print(f"Invalid 'to' token: {args.to_token}")
        return

    FROM_ID = [
        int(k.split(".")[2]) for k, v in cache.items() if v["symbol"] == args.from_token
    ][0]
    TO_ID = [
        int(k.split(".")[2]) for k, v in cache.items() if v["symbol"] == args.to_token
    ][0]

    pools = [i[0] for i in data]
    core = FROM_ID

    (prices, token_paths, pool_paths), balance_data, graph = generate_all_prices(
        rpc, pools, cache, core, mock=args.mock
    )

    print("\nPATHS\n")
    print("Symbol           Price        Path")

    if TO_ID in token_paths:
        token_path = token_paths[TO_ID]
        pool_path = pool_paths[TO_ID]
        path_str = " -> ".join([cache[f"1.3.{i}"]["symbol"] for i in token_path])
        print(
            cache[f"1.3.{TO_ID}"]["symbol"].ljust(16),
            str(sigfig(prices[TO_ID])).ljust(16),
            path_str,
        )

        # Create a pyvis network
        net = Network(notebook=False, height="750px", width="100%", bgcolor="#222222", font_color="white")
        net.from_nx(graph)

        # Set labels and colors
        for node in net.nodes:
            node_id = node["id"]
            node["label"] = cache.get(f"1.3.{node_id}", {}).get("symbol", str(node_id))
            if node_id in token_path:
                node["color"] = "skyblue"

        path_edges = list(zip(token_path, token_path[1:]))
        for edge in net.edges:
            is_path = (edge['from'], edge['to']) in path_edges or (edge['to'], edge['from']) in path_edges
            if is_path:
                edge["color"] = "lime"
                edge["width"] = 2.0
            else:
                edge["color"] = "gray"
                edge["width"] = 1.0
        
        net.set_options('''
        var options = {
          "nodes": {
            "font": {
              "size": 12
            }
          },
          "edges": {
            "color": {
              "inherit": true
            },
            "smooth": {
              "type": "continuous"
            }
          },
          "physics": {
            "forceAtlas2Based": {
              "gravitationalConstant": -50,
              "centralGravity": 0.01,
              "springLength": 230,
              "springConstant": 0.08,
              "damping": 0.4,
              "avoidOverlap": 0
            },
            "minVelocity": 0.75,
            "solver": "forceAtlas2Based"
          }
        }
        ''')

        net.show(f"liquidity_pool_map_{args.from_token}_to_{args.to_token}.html", notebook=False)

    else:
        print(f"No path found from {args.from_token} to {args.to_token}")


if __name__ == "__main__":
    main()
