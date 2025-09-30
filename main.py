import random

# 生成伪造数据
def generate_data(days=30):
    data = [100]
    for _ in range(1, days):
        change = random.uniform(-5, 5)
        data.append(data[-1] * (1 + change / 100))
    return data

# 回测逻辑
def backtest(prices, buy_threshold=2, sell_threshold=-2):
    cash = 1000
    shares = 0
    positions = []

    for i in range(1, len(prices)):
        if prices[i] >= prices[i-1] * (1 + buy_threshold / 100):
            shares += cash // prices[i]
            cash -= shares * prices[i]
            positions.append((i, 'buy', prices[i]))
        elif prices[i] <= prices[i-1] * (1 + sell_threshold / 100):
            cash += shares * prices[i]
            shares = 0
            positions.append((i, 'sell', prices[i]))

    final_value = cash + shares * prices[-1]
    return positions, final_value - 1000

# 输出交易曲线和收益
def output_results(prices, positions):
    for pos in positions:
        if pos[1] == 'buy':
            print(f"Buy at day {pos[0]}, price {pos[2]:.2f}")
        elif pos[1] == 'sell':
            print(f"Sell at day {pos[0]}, price {pos[2]:.2f}")

# 主函数
def main():
    prices = generate_data()
    positions, profit = backtest(prices)
    output_results(prices, positions)
    if profit > 0:
        print(f"Profit: {profit:.2f}")
    else:
        print("No profit")

if __name__ == "__main__":
    main()