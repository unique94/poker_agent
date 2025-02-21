from datetime import datetime
import os
# import openai

class PokerService:
    def __init__(self):
        self.current_game = None
        self.isNewHand = True
        self.positions = []
        self.action_history = []  # 添加行动历史存储
        # 初始化 OpenAI API key
        self.endpoint = "https://onlypokerai.openai.azure.com/"
        self.deployment = "gpt-4"
        self.subKey = ""

    def setup_game(self, players):
        """
        设置新的游戏
        """
        try:
            # 验证玩家数据
            self._validate_players(players)
            
            # 处理玩家数据
            processed_players = self._process_players(players)
            
            # 创建新游戏
            self.current_game = {
                'players': processed_players,
                'pot': 0,
                'current_round': 'preflop',
                # 其他游戏状态...
            }
            
            return self.current_game
            
        except Exception as e:
            raise Exception(f"设置游戏失败: {str(e)}")

    def _validate_players(self, players):
        """
        验证玩家数据
        """
        if not players:
            raise ValueError("没有玩家数据")
        
        # 验证玩家数量
        if not (2 <= len(players) <= 9):
            raise ValueError("玩家数量必须在2-9之间")
        
        # 验证庄家
        dealer_count = sum(1 for p in players if p.get('isDealer'))
        if dealer_count != 1:
            raise ValueError("必须且只能有一个庄家")

    def _process_players(self, players):
        """
        处理玩家数据
        """
        processed = []
        for player in players:
            processed_player = {
                'name': player['name'],
                'chips': player['chips'],
                'position': player['position'],
                'is_dealer': player['isDealer'],
                'action': player['action'],
                'status': player['status'],
                'bets': player['bets'],
                'hole_cards': player['holeCards'] if player['position'] == 1 else None,
                'total_bet': sum(player['bets'].values()),
                'in_hand': player['status'] == 'active',
                'action_history': player.get('actionHistory', [])
            }
            processed.append(processed_player)
        
        return processed

    @staticmethod
    def validate_table_setup(players):
        """验证牌桌设置"""
        if not 2 <= len(players) <= 9:
            raise ValueError("牌桌人数必须在2-9人之间")
        
        for player in players:
            if player['chips'] <= 0:
                raise ValueError(f"玩家 {player['name']} 的筹码必须大于0")
            if not player['name'].strip():
                raise ValueError("玩家名称不能为空")
        
        return True

    @staticmethod
    def initialize_table(players):
        """初始化牌桌"""
        return {
            'players': players,
            'total_players': len(players),
            'total_chips': sum(player['chips'] for player in players)
        }

    def _get_llm_advice(self, prompt):
        """
        调用 LLM 获取策略建议
        
        Args:
            prompt (str): 包含游戏场景描述的提示文本
            
        Returns:
            str: LLM 返回的策略建议
        """
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一位专业的德州扑克教练，精通GTO理论和实战策略。你需要根据场景信息，给出详细的策略建议。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # 提取建议内容
            advice = response.choices[0].message.content.strip()
            
            return advice
            
        except Exception as e:
            print(f"获取 LLM 建议时出错: {str(e)}")
            raise Exception(f"获取策略建议失败: {str(e)}")

    def get_advice(self, players, cards):
        """
        根据玩家信息和牌面信息生成策略建议
        """
        try:
            # 分析当前阶段
            stage = self._get_current_stage(cards)
            
            # 生成完整的场景描述
            prompt = self._get_bet_prompt(players, cards, stage)
            
            # 获取 LLM 建议
            # advice = self._get_llm_advice(prompt)
            
            # 打印详细信息用于调试
            print("\n" + "="*50)
            print("德州扑克策略分析")
            print("="*50)
            print("\n【生成的 Prompt】")
            print("-"*50)
            print(prompt)
            # print("\n【LLM 建议】")
            # print("-"*50)
            # print(advice)
            
            # 返回结果
            data = {
                'prompt': prompt
            }
            
            return data
            
        except Exception as e:
            print(f"\n错误: 生成建议时出错 - {str(e)}")
            raise Exception(f"生成建议时出错: {str(e)}")
    
    def _get_position(self, players):
        """
        确定主玩家的位置
        """
        player_count = len(players)
        # 获取该玩家数量下的位置列表
        positions = self._get_position_names(player_count)
        
        dealer_index = next((i for i, p in enumerate(players) if p['isDealer']), -1)
        
        # 返回dealer_index
        return positions, dealer_index

    def _get_position_names(self, player_count):
        """
        根据玩家数量返回位置名称列表
        从庄家位置(BTN)开始逆时针排列
        
        3人桌：SB, BB, BTN
        4人桌：SB, BB, UTG, BTN
        5人桌：SB, BB, UTG, CO, BTN
        6人桌：SB, BB, UTG, HJ, CO, BTN
        7人桌：SB, BB, UTG, MP, HJ, CO, BTN
        8人桌：SB, BB, UTG, UTG+1, MP, HJ, CO, BTN
        9人桌：SB, BB, UTG, UTG+1, UTG+2, MP, HJ, CO, BTN
        """
        if player_count < 3 or player_count > 9:
            return []

        if player_count == 3:
            positions = ['SB', 'BB', 'BTN']
        elif player_count == 4:
            positions = ['SB', 'BB', 'UTG', 'BTN']
        elif player_count == 5:
            positions = ['SB', 'BB', 'UTG', 'CO', 'BTN']
        elif player_count == 6:
            positions = ['SB', 'BB', 'UTG', 'HJ', 'CO', 'BTN']
        elif player_count == 7:
            positions = ['SB', 'BB', 'UTG', 'MP', 'HJ', 'CO', 'BTN']
        elif player_count == 8:
            positions = ['SB', 'BB', 'UTG', 'UTG+1', 'MP', 'HJ', 'CO', 'BTN']
        elif player_count == 9:
            positions = ['SB', 'BB', 'UTG', 'UTG+1', 'UTG+2', 'MP', 'HJ', 'CO', 'BTN']
        
        # 确保返回的位置数量与玩家数量相匹配
        return positions
    
    def _get_current_stage(self, cards):
        """确定当前游戏阶段"""
        if not any(cards['flop']):
            return 'preflop'
        elif not cards['turn']:
            return 'flop'
        elif not cards['river']:
            return 'turn'
        return 'river'

    def _get_bet_prompt(self, players, cards, stage):
        """
        生成用于大模型的 prompt，描述当前游戏场景
        
        Args:
            players (list): 玩家信息列表
            cards (dict): 公共牌信息
            stage (str): 当前游戏阶段
        
        Returns:
            str: 格式化的场景描述
        """
        try:
            # 获取主要信息
            player_count = len(players)

            positions, dealer_index = self._get_position(players)
            print(f"庄家位置：{dealer_index}")
            sb_player_idx = (dealer_index + 1) % len(players)
            rotated_players = players[sb_player_idx:] + players[:sb_player_idx]

            for i, player in enumerate(rotated_players):
                player['position_name'] = positions[i]
                        

            main_player_new_idx = player_count - sb_player_idx
            print(f"主玩家位置：{main_player_new_idx}")
            name = rotated_players[main_player_new_idx]['name']
            
            # 构建场景描述
            if (self.isNewHand):
                prompt = f"""我希望你扮演一个经验老道的德州扑克职业玩家，参与我们的带有娱乐性质的德州扑克现金局。
以下是一些牌局信息：
1. 参与的玩家有一个特点，在翻牌前，大家非常喜欢limp。翻前行动4倍以下的加注大多数都是无效的，大家都会call。
2. 参与的玩家在河牌的行动会相对保守，在河牌阶段，大尺度的bluff行为会相对较少。
3. 因为有你的加入，大家都知道你是AI玩家，大家可能会更多的bluff你。

我希望你能采取正确的策略，剥削其他玩家，赢得游戏。

现在的游戏人数是：{player_count}人：

1. 基本信息：
- 你扮演的玩家姓名：{name}
- 你的位置：{rotated_players[main_player_new_idx]['position_name']}
- 你的筹码：{rotated_players[main_player_new_idx]['chips']}
- 你的底牌：{rotated_players[main_player_new_idx]['holeCards']['card1']} {rotated_players[main_player_new_idx]['holeCards']['card2']}

2. 其他玩家信息："""

            # 添加其他玩家信息
            for i, player in enumerate(rotated_players):
                if (i == main_player_new_idx):
                    prompt += f"""
- 位置：{positions[i]}
  这个玩家是你"""
                else:
                    prompt += f"""
- 位置：{positions[i]}
  玩家姓名：{player['name']}
  筹码：{player['chips']}"""

            # 添加公共牌信息
            prompt += "\n\n3. 当前牌面信息："
            if stage == 'preflop':
                prompt += "\n现在是翻前下注"
            else:
                if cards['flop']:
                    flop_cards = ' '.join(cards['flop'])
                    prompt += f"\n翻牌：{flop_cards}"
                if cards['turn']:
                    prompt += f"\n转牌：{cards['turn']}"
                if cards['river']:
                    prompt += f"\n河牌：{cards['river']}"
            

            # 添加玩家行动信息
            prompt += "\n\n4. 玩家行动信息(对于已经fold的玩家，之后的行动信息会留空)："
            if stage == 'preflop':
                prompt += "\n翻前下注"
                for i, player in enumerate(rotated_players):
                    actionInfo = player['bets']['preflop']
                    prompt += f"\n- 位置：{player['position_name']}, 玩家姓名：{player['name']}, 行动：{actionInfo}"

            elif stage == 'flop':
                prompt += "\n翻前下注"
                for i, player in enumerate(rotated_players):
                    actionInfo = player['bets']['preflop']
                    prompt += f"\n- 位置：{player['position_name']}, 玩家姓名：{player['name']}, 行动：{actionInfo}"
                prompt += "\n\n翻牌后下注"
                for i, player in enumerate(rotated_players):
                    actionInfo = player['bets']['flop']
                    prompt += f"\n- 位置：{player['position_name']}, 玩家姓名：{player['name']}, 行动：{actionInfo}"

            elif stage == 'turn':
                prompt += "\n翻前下注"
                for i, player in enumerate(rotated_players):
                    actionInfo = player['bets']['preflop']
                    prompt += f"\n- 位置：{player['position_name']}, 玩家姓名：{player['name']}, 行动：{actionInfo}"
                prompt += "\n\n转牌后下注"
                for i, player in enumerate(rotated_players):
                    actionInfo = player['bets']['flop']
                    prompt += f"\n- 位置：{player['position_name']}, 玩家姓名：{player['name']}, 行动：{actionInfo}"
                prompt += "\n\n河牌后下注"
                for i, player in enumerate(rotated_players):
                    actionInfo = player['bets']['turn']
                    prompt += f"\n- 位置：{player['position_name']}, 玩家姓名：{player['name']}, 行动：{actionInfo}"

            elif stage == 'river':
                prompt += "\n翻前下注"
                for i, player in enumerate(rotated_players):
                    actionInfo = player['bets']['preflop']
                    prompt += f"\n- 位置：{player['position_name']}, 玩家姓名：{player['name']}, 行动：{actionInfo}"
                prompt += "\n\n翻牌后下注"
                for i, player in enumerate(rotated_players):
                    actionInfo = player['bets']['flop']
                    prompt += f"\n- 位置：{player['position_name']}, 玩家姓名：{player['name']}, 行动：{actionInfo}"
                prompt += "\n\n转牌后下注"
                for i, player in enumerate(rotated_players):
                    actionInfo = player['bets']['turn']
                    prompt += f"\n- 位置：{player['position_name']}, 玩家姓名：{player['name']}, 行动：{actionInfo}"
                prompt += "\n\n河牌后下注"
                for i, player in enumerate(rotated_players):
                    actionInfo = player['bets']['river']
                    prompt += f"\n- 位置：{player['position_name']}, 玩家姓名：{player['name']}, 行动：{actionInfo}"



            prompt += f"\n\n5. 你扮演的玩家姓名是：{name}，现在行动到你，应该怎么做？"

            # 添加提问
            if (self.isNewHand):
                prompt += """\n\n请根据以上信息，给出详细的策略建议，包括：
1. 这手牌在当前位置的打法建议
2. 考虑其他玩家的筹码深度，建议的加注尺度
3. 需要注意的关键点
4. 如果遇到加注或反加注，应该如何应对

最终总结，给我一个明确的行动。如果是下注，基于当前的底池大小，告诉我要下注多少？
"""

            self.isNewHand = False

            # 在返回prompt之前，保存到日志文件
            self._save_prompt_to_log(prompt, stage)
            
            return prompt

        except Exception as e:
            raise Exception(f"生成 prompt 时出错: {str(e)}")

    def _save_prompt_to_log(self, prompt, stage):
        """
        将prompt保存到日志文件
        
        Args:
            prompt (str): 要保存的prompt
            stage (str): 当前游戏阶段
        """
        try:
            # 创建logs目录（如果不存在）
            if not os.path.exists('logs'):
                os.makedirs('logs')
            
            # 使用固定的日志文件名
            filename = 'logs/poker_prompts.log'
            
            # 追加模式写入日志文件
            with open(filename, 'a', encoding='utf-8') as f:
                f.write("\n" + "="*80 + "\n")
                f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Stage: {stage}\n")
                f.write("-"*80 + "\n")
                f.write(prompt + "\n")
            
        except Exception as e:
            print(f"保存prompt到日志文件时出错: {str(e)}")

    def reset_game(self):
        """
        重置游戏状态
        """
        self.isNewHand = True
        self.current_game = None
        self.action_history = [] 