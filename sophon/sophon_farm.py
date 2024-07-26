from web3 import Web3
from datetime import datetime, timezone

# RPC 
rpc_url = "https://eth.llamarpc.com"
web3 = Web3(Web3.HTTPProvider(rpc_url))

# List of addresses to check
addresses = [
    "0x2daabb7d7d8114EE334D5A141A97ef181e565e69",
    "0x686779932A7c12C279940f6987cE408204863465"
]

contract_address = "0xEfF8E65aC06D7FE70842A4d54959e8692d6AE064"
contract_abi = [
    {
        "constant": True,
        "inputs": [{"name": "addresses", "type": "address[]"}],
        "name": "getPendingPoints",
        "outputs": [{"name": "pendings", "type": "uint256[][]"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "getPoolInfo",
        "outputs": [{"type": "tuple[]", "components": [
            {"type": "address", "name": "lpToken"},
            {"type": "address", "name": "l2Farm"},
            {"type": "uint256", "name": "amount"},
            {"type": "uint256", "name": "boostAmount"},
            {"type": "uint256", "name": "depositAmount"},
            {"type": "uint256", "name": "allocPoint"},
            {"type": "uint256", "name": "lastRewardBlock"},
            {"type": "uint256", "name": "accPointsPerShare"},
            {"type": "uint256", "name": "totalRewards"},
            {"type": "string", "name": "description"}
        ]}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "users", "type": "address[]"}],
        "name": "getOptimizedUserInfo",
        "outputs": [{"name": "userInfos", "type": "uint256[4][][]"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "pointsPerBlock",
        "outputs": [{"name": "", "type": "uint256"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]


contract = web3.eth.contract(address=contract_address, abi=contract_abi)
pool_info = contract.functions.getPoolInfo().call()
user_info = contract.functions.getOptimizedUserInfo(addresses).call()
pending_points = contract.functions.getPendingPoints(addresses).call()
total_rewards = 0
rewards_per_wallet = {}
daily_sp_emission_per_pool = []
total_alloc_point = sum(pool[5] for pool in pool_info)  # allocPoint is at index 5
total_points_per_block = contract.functions.pointsPerBlock().call()
blocks_per_day = 7150  # Ethereum averages about 7150 blocks per day

for pool in pool_info:
    daily_sp_emission = (pool[5] / total_alloc_point) * total_points_per_block * blocks_per_day / 1e18
    daily_sp_emission_per_pool.append(daily_sp_emission)

total_daily_sp_all_wallets = 0

print("\n" + "="*70)
print("Rewards per wallet (in SP):")
print("="*70)
print(f"{'Address':<42} {'Rewards':>12} {'Daily':>12}")
print("-"*70)
for idx, address in enumerate(addresses):
    rewards_wei = sum(pending_points[idx])
    rewards_sp = rewards_wei / 10**18
    rewards_per_wallet[address] = rewards_sp
    total_rewards += rewards_sp

    user_daily_sp = []
    for pid, pool in enumerate(pool_info):
        user_amount = user_info[idx][pid][0]
        pool_amount = pool[2]  # amount is at index 2
        if pool_amount > 0:
            user_share = user_amount / pool_amount
            user_daily_sp.append(user_share * daily_sp_emission_per_pool[pid])
    total_user_daily_sp = sum(user_daily_sp)
    total_daily_sp_all_wallets += total_user_daily_sp
    print(f"{address:<42} {rewards_sp:>12.1f} {total_user_daily_sp:>12.1f}")

total_sp_points = sum(pool[8] for pool in pool_info) / 1e18  # totalRewards is at index 8

sp_percentage = (total_rewards / total_sp_points) * 100 if total_sp_points > 0 else 0
daily_sp_percentage = (total_daily_sp_all_wallets / sum(daily_sp_emission_per_pool)) * 100 if sum(daily_sp_emission_per_pool) > 0 else 0

print("\n" + "="*70)
print("Summary")
print("="*70)
print(f"SP combined (%): {total_rewards:,.0f} SP ({sp_percentage:.2f}%)")
print(f"Total SP Points : {total_sp_points:,.0f} SP")
print()
print(f"Daily SP combined (%): {total_daily_sp_all_wallets:,.0f} SP ({daily_sp_percentage:.2f}%)")
print(f"Total Daily SP: {sum(daily_sp_emission_per_pool):,.0f} SP")
print("="*70)

forecast_dates = [
    datetime(2024, 10, 1, tzinfo=timezone.utc),
    datetime(2024, 11, 1, tzinfo=timezone.utc),
    datetime(2024, 12, 1, tzinfo=timezone.utc),
    datetime(2025, 1, 1, tzinfo=timezone.utc)
]

now = datetime.now(timezone.utc)
total_daily_sp_emission = sum(daily_sp_emission_per_pool)

print("\nForecast")
print("="*70)
print(f"{'Date':<12} {'My SP Total':>15} {'% of My SP':>12} {'Total SP Emitted':>20}")
print("-"*70)

for date in forecast_dates:
    days = (date - now).days
    total_sp_emitted = total_sp_points + (total_daily_sp_emission * days)
    my_sp_total = total_rewards + (total_daily_sp_all_wallets * days)
    my_sp_percentage = (my_sp_total / total_sp_emitted) * 100

    print(f"{date.strftime('%Y-%m-%d'):12} {my_sp_total:15,.0f} {my_sp_percentage:11.2f}% {total_sp_emitted:20,.0f}")

print("="*70)
