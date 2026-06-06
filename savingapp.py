import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import math

# ==========================================
# 页面基础设置
# ==========================================
st.set_page_config(page_title="自律记账通", page_icon="🦉", layout="centered")

# ==========================================
# 状态初始化 (Session State)
# ==========================================
if 'setup_done' not in st.session_state:
    st.session_state.setup_done = False

if not st.session_state.setup_done:    st.title("🦉 欢迎来到你的专属自律记账系统")
st.write("在这里，本金会自动生息（年化 1.01%），但花钱大手大脚可是要被骂的哦！")
    
init_p = st.number_input("请输入你的初始本金 (¥)", min_value=0.0, value=10000.0, step=100.0)
if st.button("开始我的理财之旅 🚀"):
        # 初始账单记录
        st.session_state.transactions = pd.DataFrame([{
            'ID': 0,
            'Date': date.today(),
            'Type': 'Income',
            'Amount': init_p,
            'Reason': '初始本金投入'
        }])
        st.session_state.vouchers = []      # 用户的奖励券库存
        st.session_state.spent_coins = 0    # 已花费的金币
        st.session_state.start_date = date.today()
        st.session_state.setup_done = True
        st.rerun()

else:
    # ==========================================
    # 核心算法与数据处理
    # ==========================================
    today = date.today()
    delta_days = (today - st.session_state.start_date).days
    
    df = st.session_state.transactions
    daily_income = df[df['Type'] == 'Income'].groupby('Date')['Amount'].sum().to_dict()
    daily_expense = df[df['Type'] == 'Expense'].groupby('Date')['Amount'].sum().to_dict()
    
    current_principal = 0.0
    current_coins = 20.0  # 初始赠送20金币
    reward_days_this_month = 0
    punish_days_this_month = 0
    
    # 按照天数推演，计算复利和每日金币变动
    for i in range(delta_days + 1):
        curr_date = st.session_state.start_date + timedelta(days=i)
        
        # 1. 每日利息结算 (年化 1.01% -> 日利率 0.0101 / 365)
        if current_principal > 0:
            current_principal += current_principal * (0.0101 / 365)
            
        # 2. 加上当日收入 (如存入本金)
        current_principal += daily_income.get(curr_date, 0.0)
        
        # 3. 减去当日花销
        day_exp = daily_expense.get(curr_date, 0.0)
        current_principal -= day_exp
        
        # 4. 金币奖惩机制 (基于每日总花销)
        if curr_date in daily_expense:
            if day_exp < 50:
                # 奖励机制：低于50的部分转化为金币
                current_coins += (50 - day_exp)
                if curr_date.month == today.month: 
                    reward_days_this_month += 1
            elif day_exp > 60:
                # 惩罚机制：超过60的部分除以2扣除金币
                current_coins -= (day_exp - 60) / 2.0
                if curr_date.month == today.month: 
                    punish_days_this_month += 1

    # 减去商城里已经花掉的金币
    current_coins -= st.session_state.spent_coins

    # ==========================================
    # UI 布局与展示
    # ==========================================
    st.title("🦉 自律记账通")
    
    # 顶部指标大盘
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="实时本金 (含利息)", value=f"¥ {current_principal:.4f}", delta="年化利率 1.01%")
    with col2:
        st.metric(label="当前拥有金币 🪙", value=f"{current_coins:.1f}")

    # 导航选项卡
    tab1, tab2, tab3, tab4 = st.tabs(["📝 记一笔", "🛒 金币商城", "📊 账单历史", "🦉 月度总结"])

    # ------------------------------------------
    # Tab 1: 记账
    # ------------------------------------------
    with tab1:
        st.subheader("记录今日花销 / 存入本金")
        with st.form("add_transaction_form"):
            t_type = st.radio("类型", ["花销 (Expense)", "存入 (Income)"], horizontal=True)
            t_amount = st.number_input("金额 (¥)", min_value=0.1, step=10.0)
            t_reason = st.text_input("用途说明", placeholder="例如：午饭、打车、发工资...")
            t_date = st.date_input("日期", value=today, max_value=today)
            
            submitted = st.form_submit_button("确认记录")
            if submitted:
                new_id = len(st.session_state.transactions)
                real_type = "Expense" if "花销" in t_type else "Income"
                
                new_row = pd.DataFrame([{
                    'ID': new_id,
                    'Date': t_date,
                    'Type': real_type,
                    'Amount': t_amount,
                    'Reason': t_reason
                }])
                st.session_state.transactions = pd.concat([st.session_state.transactions, new_row], ignore_index=True)
                st.success("记录成功！快去看看你的本金和金币变化吧！")
                st.rerun()

    # ------------------------------------------
    # Tab 2: 商城
    # ------------------------------------------
    with tab2:
        st.subheader("🛍️ 奖励兑换商城")
        st.info("努力省钱赚金币，来兑换犒劳自己的礼物吧！")
        
        products = [
            {"name": "☕ 奶茶/咖啡兑换券", "price": 50, "icon": "☕"},
            {"name": "💆 舒适按摩券", "price": 120, "icon": "💆"},
            {"name": "🎬 电影通兑券", "price": 300, "icon": "🎬"},
            {"name": "✈️ 周边游旅游券", "price": 1000, "icon": "✈️"}
        ]
        
        for p in products:
            col_icon, col_info, col_btn = st.columns([1, 4, 2])
            with col_icon:
                st.markdown(f"## {p['icon']}")
            with col_info:
                st.markdown(f"**{p['name']}**")
                st.caption(f"售价: {p['price']} 金币")
            with col_btn:
                if st.button("兑换", key=f"buy_{p['name']}"):
                    if current_coins >= p['price']:
                        st.session_state.spent_coins += p['price']
                        st.session_state.vouchers.append(f"{p['icon']} {p['name']} ({today.strftime('%Y-%m-%d')})")
                        st.success(f"兑换成功！获得了 {p['name']}！")
                        st.rerun()
                    else:
                        st.error("金币不足，快去省钱吧！")
                        
        st.divider()
        st.write("🎒 **我的背包 (已兑换的券)**")
        if not st.session_state.vouchers:
            st.caption("背包空空如也~")
        else:
            for v in st.session_state.vouchers:
                st.write(f"- {v}")

    # ------------------------------------------
    # Tab 3: 账单历史
    # ------------------------------------------
    with tab3:
        st.subheader("📅 历史账单")
        display_df = st.session_state.transactions.copy()
        display_df.sort_values(by='Date', ascending=False, inplace=True)
        # 汉化表头展示
        display_df.rename(columns={'Date': '日期', 'Type': '类型', 'Amount': '金额', 'Reason': '用途说明'}, inplace=True)
        st.dataframe(display_df[['日期', '类型', '金额', '用途说明']], use_container_width=True, hide_index=True)

    # ------------------------------------------
    # Tab 4: 多邻国式月度总结
    # ------------------------------------------
    with tab4:
        st.subheader("🦉 本月消费习惯总结")
        st.write(f"当前月份：{today.month}月")
        st.markdown(f"- 🏆 **控制极佳 (花销<50) 天数**: {reward_days_this_month} 天")
        st.markdown(f"- ⚠️ **严重超标 (花销>60) 天数**: {punish_days_this_month} 天")
        
        st.divider()
        if st.button("查看本月评价"):
            if punish_days_this_month > reward_days_this_month and punish_days_this_month >= 3:
                st.error("""
                ### 😡 你这个月是怎么回事？！
                我看过你的账单了。你是不是每天都在外面大手大脚？
                低于50块很难吗？金币都要被你扣成负数了！
                再这样下去，你的本金全都要被你败光了！下个月给我好好反省，收敛一点！听见没有？！
                """)
            elif punish_days_this_month > 0 and punish_days_this_month <= reward_days_this_month:
                st.warning("""
                ### 🧐 勉勉强强吧
                这个月虽然有几天没管住手，但总体来说控制得还算可以。
                不过不要骄傲，下个月请务必减少超过60块的开销，你的金币在召唤你！
                """)
            elif reward_days_this_month > 0 and punish_days_this_month == 0:
                st.success("""
                ### 💖 完美！你简直是理财大师！
                我太为你骄傲了！本月居然**没有任何一天**被扣除金币！
                你的自控力简直无敌，看着稳步增长的本金和金币，是不是非常有成就感？
                拿着你的金币去商城犒劳一下自己吧，继续保持哦！
                """)
            elif reward_days_this_month == 0 and punish_days_this_month == 0:
                st.info("🦉 这个月好像还没怎么记账呢，快去输入你的花销吧！")
            else:
                st.success("🦉 这个月表现不错，继续努力攒金币吧！")