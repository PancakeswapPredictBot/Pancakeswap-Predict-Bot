import pandas as pd
import time
import seaborn as sns
import matplotlib.pyplot as plt
from tabulate import tabulate
from core.pancake_prediction import *
from tg_bot import tg_message_bot


def result_stats(pp, start_epoch=None, show=False):
    df = result_analysis(pp)
    gas_fee = 0.0006 * 2
    bet_size = 0.02
    if start_epoch is not None:
        df = df[df['epoch'] >= start_epoch].reset_index(drop=True)
    if not show:
        pnl = 0
        pnl -= len(df)
        pnl += df[df['win'] & (df['direction'] == 'bull')]['bull_odds'].sum() * 0.97
        pnl += df[df['win'] & (df['direction'] == 'bear')]['bear_odds'].sum() * 0.97
        logger.Logger.log_message('win rate: %s' % str(round(len(df[df['win']]) / len(df) * 100, 2)))
        logger.Logger.log_message('pnl (BNB): %s' % str(round(pnl, 2)))
    else:
        pnl = 0
        pnl_list = [0]
        for game in df.iterrows():
            pnl -= bet_size
            pnl -= gas_fee
            if game[1]['win']:
                if game[1]['direction'] == 'bull':
                    pnl += game[1]['bull_odds'] * 0.97 * bet_size
                if game[1]['direction'] == 'bear':
                    pnl += game[1]['bear_odds'] * 0.97 * bet_size
            pnl_list.append(pnl)
        plt.plot(pnl_list)
        plt.show()
    return pnl


def blast_pnl_book(pp, length=10, heartbeat=1800):
    while True:
        try:
            df = result_analysis(pp).tail(length)
            msg = ':closed_book: PCS Prediction PnL Book (Latest %s) \n\n' % str(length)
            msg += ':money_bag: BNB Balance: %s' % str(round(pp.get_balance(), 4))
            msg += '\n:bullseye: Hit Rate: %s  \n\n' % str(round(len(df[df['win']]) / len(df) * 100, 2))
            msg += tabulate(df[['epoch', 'direction', 'bull_odds', 'bear_odds', 'win', 'bet_size']],
                            ['epoch', 'direction', 'bull_odds', 'bear_odds', 'win', 'bet_size'], tablefmt='github',
                            showindex=False)
            tg_message_bot.tg_send(msg, with_emoji=True)
        except:
            pass
        time.sleep(heartbeat)


def record_parser(pp, thres=0.01):
    df = logger.all_logs_parser(log='pancake_bnb_status.log', columns=['datetime', 'type', 'level', 'action', 'resp'])
    game_list = {}
    current_epoch = None
    for row in df.iterrows():
        if row[1]['action'] == 'epoch':
            current_epoch = row[1]['resp']
            game_list[current_epoch] = []
        if current_epoch is not None and row[1]['action'] == 'premium':
            game_list[current_epoch].append(float(row[1]['resp']))
    bet_count = 0
    win_count = 0
    capital = 0
    capital_list = []

    for game in game_list:
        if len(game_list[game]) > 0:
            detail_dict = pp.round_details(int(game))
            print(detail_dict)
            try:
                bear_odds = float(detail_dict['total_amount'] / detail_dict['bear_amount'])
            except:
                bear_odds = 0
            try:
                bull_odds = float(detail_dict['total_amount'] / detail_dict['bull_amount'])
            except:
                bull_odds = 0
            detail_dict['result'] = 'bull' if detail_dict['close_price'] > detail_dict['lock_price'] else 'bear'
            if max(game_list[game]) >= thres:
                capital -= 1
                capital -= (0.0006 * 2)
                bet_count += 1
                if detail_dict['result'] == 'bull':
                    capital += bull_odds * 0.97
                    win_count += 1
            elif min(game_list[game]) <= -thres:
                capital -= 1
                bet_count += 1
                if detail_dict['result'] == 'bear':
                    capital += bear_odds * 0.97
                    win_count += 1
            capital_list.append(capital)

    plt.title('thres: %s, wins: %s, bets: %s, win rate: %s' % (
        str(thres), str(win_count), str(bet_count), str(round(win_count / bet_count * 100, 2))))
    plt.plot(capital_list)
    plt.show()
    return capital_list


if __name__ == '__main__':
    pred = PancakePrediction(abi_name='pancake_bnb_prediction.abi',
                             config='pancake_bnb_prediction.ini',
                             address=address_dict['pancake_bnb_prediction_address'],
                             logging=False)

    # pnl10 = record_parser(pred, thres=0.010)
    # pnl9 = record_parser(pred, thres=0.009)
    # pnl8 = record_parser(pred, thres=0.008)
    # pnl7 = record_parser(pred, thres=0.007)
    # pnl6 = record_parser(pred, thres=0.006)
    # pnl5 = record_parser(pred, thres=0.005)

    # resp = {'strategy_5': pnl5, 'strategy_6': pnl6, 'strategy_7': pnl7, 'strategy_8': pnl8, 'strategy_9': pnl9,
            # 'strategy_10': pnl10}

    # record_parser(pred, thres=0.007)
    # record_parser(pred, thres=0.008)
    # record_parser(pred, thres=0.009)
    # record_parser(pred, thres=0.01)

    result_stats(pred, 5464, True)