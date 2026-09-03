import asyncio, sys, os, json
sys.path.insert(0, r'D:\AI_Scientist\AI_Scientist\backend')
os.chdir(r'D:\AI_Scientist\AI_Scientist\backend')

from app.database.session import AsyncSessionLocal
from app.database.models import ScienceQuestion

# 125道种子题目 - 覆盖多个学科领域
SEED_QUESTIONS = [
    # === 哲学 (1-15) ===
    {"question_id": 1, "title": "人工智能是否具有意识？", "title_en": "Does Artificial Intelligence Possess Consciousness?", "category": "哲学", "description": "探讨强人工智能是否可能产生主观体验和自我意识，涉及中文房间论证、功能主义等经典哲学问题。", "keywords": ["人工智能", "意识", "心灵哲学", "图灵测试"], "difficulty": "hard"},
    {"question_id": 2, "title": "自由意志与决定论的相容性问题", "title_en": "Compatibilism of Free Will and Determinism", "category": "哲学", "description": "在物理决定论框架下，人类是否仍拥有道德责任所需的自由意志？分析相容论与不相容论的核心争论。", "keywords": ["自由意志", "决定论", "道德责任", "相容论"], "difficulty": "hard"},
    {"question_id": 3, "title": "知识的证成理论：内在主义vs外在主义", "title_en": "Justification Theories: Internalism vs Externalism", "category": "哲学", "description": "知识的确证究竟依赖于主体的内在认知状态，还是外部可靠的认知过程？比较两种认识论立场。", "keywords": ["认识论", "证成", "内在主义", "外在主义"], "difficulty": "medium"},
    {"question_id": 4, "title": "功利主义的困境：电车难题的伦理分析", "title_en": "Trolley Problem: Ethical Analysis of Utilitarianism", "category": "哲学", "description": "通过电车难题及其变体，检验功利主义、义务论和美德伦理学在极端情境下的道德判断差异。", "keywords": ["功利主义", "电车难题", "伦理学", "道德判断"], "difficulty": "medium"},
    {"question_id": 5, "title": "语言的意义：指称论与使用论之争", "title_en": "Meaning of Language: Reference Theory vs Use Theory", "category": "哲学", "description": "词语的意义是由其指称对象决定，还是由其在语言游戏中的使用方式决定？比较弗雷格、罗素与维特根斯坦的观点。", "keywords": ["语言哲学", "意义", "指称", "维特根斯坦"], "difficulty": "medium"},
    {"question_id": 6, "title": "社会契约论的现代适用性", "title_en": "Modern Applicability of Social Contract Theory", "category": "哲学", "description": "霍布斯、洛克、卢梭的社会契约理论在数字时代和国家治理现代化中是否仍然有效？", "keywords": ["社会契约", "政治哲学", "正义", "国家合法性"], "difficulty": "medium"},
    {"question_id": 7, "title": "存在先于本质：萨特存在主义的核心命题", "title_en": "Existence Precedes Essence: Sartre's Existentialism", "category": "哲学", "description": "分析萨特'存在先于本质'命题的含义，以及它对个人自由、选择和责任的影响。", "keywords": ["存在主义", "萨特", "自由", "本质"], "difficulty": "medium"},
    {"question_id": 8, "title": "科学实在论与反实在论之争", "title_en": "Scientific Realism vs Anti-Realism Debate", "category": "哲学", "description": "科学理论是否描述了独立于观察者的客观实在？评估无奇迹论证与悲观归纳论证。", "keywords": ["科学哲学", "实在论", "真理", "科学理论"], "difficulty": "hard"},
    {"question_id": 9, "title": "儒家仁学与西方美德伦理的比较", "title_en": "Confucian Ren and Western Virtue Ethics Comparison", "category": "哲学", "description": "比较儒家以'仁'为核心的德性传统与亚里士多德美德伦理学的异同，探讨跨文化伦理对话的可能。", "keywords": ["儒家", "美德伦理", "仁", "跨文化比较"], "difficulty": "medium"},
    {"question_id": 10, "title": "技术异化：马克思理论的当代阐释", "title_en": "Technological Alienation: Contemporary Marx Interpretation", "category": "哲学", "description": "在算法推荐、平台经济和AI自动化背景下，重新审视马克思的异化劳动理论。", "keywords": ["马克思", "异化", "技术", "劳动"], "difficulty": "medium"},
    {"question_id": 11, "title": "后现代主义对宏大叙事的批判", "title_en": "Postmodern Critique of Grand Narratives", "category": "哲学", "description": "利奥塔对元叙事的怀疑如何影响了当代知识生产、历史书写和文化批评？", "keywords": ["后现代主义", "利奥塔", "叙事", "知识"], "difficulty": "medium"},
    {"question_id": 12, "title": "身心问题的当代解决方案", "title_en": "Contemporary Solutions to Mind-Body Problem", "category": "哲学", "description": "评估属性二元论、功能主义、消除唯物主义等对笛卡尔身心问题的回应。", "keywords": ["身心问题", "二元论", "功能主义", "意识"], "difficulty": "hard"},
    {"question_id": 13, "title": "正义论：罗尔斯与诺齐克的分歧", "title_en": "Theory of Justice: Rawls vs Nozick", "category": "哲学", "description": "比较罗尔斯的差异原则与诺齐克的资格理论在分配正义问题上的根本分歧。", "keywords": ["正义", "罗尔斯", "诺齐克", "分配"], "difficulty": "medium"},
    {"question_id": 14, "title": "中国哲学中的天人关系", "title_en": "Heaven-Human Relationship in Chinese Philosophy", "category": "哲学", "description": "从先秦到宋明理学，梳理'天人合一'思想在不同学派中的演变及其生态哲学意涵。", "keywords": ["天人合一", "中国哲学", "生态", "理学"], "difficulty": "medium"},
    {"question_id": 15, "title": "现象学方法在社会科学中的应用", "title_en": "Phenomenological Method in Social Sciences", "category": "哲学", "description": "胡塞尔的现象学还原和舒茨的生活世界概念如何为社会科学研究提供方法论基础？", "keywords": ["现象学", "胡塞尔", "方法论", "社会科学"], "difficulty": "hard"},

    # === 社会学 (16-30) ===
    {"question_id": 16, "title": "数字鸿沟与社会不平等的再生产", "title_en": "Digital Divide and Reproduction of Social Inequality", "category": "社会学", "description": "互联网接入和使用能力的差异如何加剧既有的阶级、种族和性别不平等？", "keywords": ["数字鸿沟", "社会不平等", "阶层", "信息技术"], "difficulty": "medium"},
    {"question_id": 17, "title": "城市化进程中的社区认同变迁", "title_en": "Community Identity Change in Urbanization", "category": "社会学", "description": "快速城市化如何重塑居民的地方认同、邻里关系和社会资本？以中国新型城镇化为案例。", "keywords": ["城市化", "社区", "认同", "社会资本"], "difficulty": "medium"},
    {"question_id": 18, "title": "老龄化社会的代际关系重构", "title_en": "Intergenerational Relationship Restructuring in Aging Society", "category": "社会学", "description": "人口老龄化背景下，家庭养老模式、代际资源分配和社会政策面临哪些结构性挑战？", "keywords": ["老龄化", "代际关系", "养老", "人口"], "difficulty": "medium"},
    {"question_id": 19, "title": "社交媒体与青年政治参与", "title_en": "Social Media and Youth Political Participation", "category": "社会学", "description": "社交平台如何改变了青年的政治表达方式、动员机制和公民参与模式？", "keywords": ["社交媒体", "青年", "政治参与", "公民社会"], "difficulty": "medium"},
    {"question_id": 20, "title": "性别角色的社会建构与变迁", "title_en": "Social Construction and Change of Gender Roles", "category": "社会学", "description": "从波伏瓦到巴特勒，分析性别作为社会建构物的理论演进及当代性别平等的实践路径。", "keywords": ["性别", "社会建构", "女性主义", "平等"], "difficulty": "medium"},
    {"question_id": 21, "title": "教育分层与社会流动性的关系", "title_en": "Educational Stratification and Social Mobility", "category": "社会学", "description": "布迪厄的文化资本理论如何解释教育系统在社会再生产中的作用？中国教育扩张是否促进了社会流动？", "keywords": ["教育", "社会流动", "文化资本", "布迪厄"], "difficulty": "medium"},
    {"question_id": 22, "title": "风险社会理论在全球危机中的验证", "title_en": "Risk Society Theory Validation in Global Crises", "category": "社会学", "description": "贝克的风险社会理论能否有效解释新冠疫情、气候变化等全球性风险的治理困境？", "keywords": ["风险社会", "贝克", "全球化", "危机治理"], "difficulty": "medium"},
    {"question_id": 23, "title": "乡村振兴中的文化资本转化", "title_en": "Cultural Capital Conversion in Rural Revitalization", "category": "社会学", "description": "乡村传统文化资源如何通过旅游开发、非遗保护等方式转化为经济发展动力？", "keywords": ["乡村振兴", "文化资本", "非遗", "发展"], "difficulty": "medium"},
    {"question_id": 24, "title": "平台经济下的劳动关系变革", "title_en": "Labor Relations Transformation in Platform Economy", "category": "社会学", "description": "外卖骑手、网约车司机等平台劳动者的权益保障困境反映了怎样的制度性问题？", "keywords": ["平台经济", "劳动", "零工经济", "权益"], "difficulty": "medium"},
    {"question_id": 25, "title": "移民融入与文化适应的双向模型", "title_en": "Bidirectional Model of Immigrant Integration", "category": "社会学", "description": "超越单向同化模型，探讨移民群体与接收社会之间的互动适应过程。", "keywords": ["移民", "文化适应", "融入", "多元文化"], "difficulty": "medium"},
    {"question_id": 26, "title": "消费文化与身份认同的符号建构", "title_en": "Symbolic Construction of Identity in Consumer Culture", "category": "社会学", "description": "鲍德里亚的消费社会理论如何揭示商品符号价值对现代人身份认同的塑造作用？", "keywords": ["消费文化", "符号", "身份认同", "鲍德里亚"], "difficulty": "medium"},
    {"question_id": 27, "title": "网络社群的集体行动逻辑", "title_en": "Collective Action Logic in Online Communities", "category": "社会学", "description": "奥尔森的集体行动理论在网络时代是否需要修正？分析在线社群的组织动员机制。", "keywords": ["集体行动", "网络社群", "动员", "奥尔森"], "difficulty": "medium"},
    {"question_id": 28, "title": "健康不平等的社会决定因素", "title_en": "Social Determinants of Health Inequality", "category": "社会学", "description": "社会经济地位、居住环境和种族歧视如何系统性地影响人群健康结果？", "keywords": ["健康不平等", "社会决定因素", "公共卫生", "社会梯度"], "difficulty": "medium"},
    {"question_id": 29, "title": "家庭结构的多元化趋势及其影响", "title_en": "Diversification of Family Structure and Its Impact", "category": "社会学", "description": "单亲家庭、丁克家庭、同居伴侣等非传统家庭形式的增长对社会政策和儿童发展有何影响？", "keywords": ["家庭", "多元化", "社会政策", "儿童发展"], "difficulty": "medium"},
    {"question_id": 30, "title": "全球化背景下的民族主义复兴", "title_en": "Nationalism Revival in Globalization Context", "category": "社会学", "description": "为何全球化并未消解民族认同，反而在某些地区激发了民族主义的强势回归？", "keywords": ["全球化", "民族主义", "认同政治", "民粹主义"], "difficulty": "medium"},

    # === 经济学 (31-45) ===
    {"question_id": 31, "title": "行为经济学对理性人假设的挑战", "title_en": "Behavioral Economics Challenge to Rational Agent Hypothesis", "category": "经济学", "description": "卡尼曼的前景理论和塞勒的助推理论如何修正了新古典经济学的完全理性假设？", "keywords": ["行为经济学", "有限理性", "前景理论", "决策"], "difficulty": "medium"},
    {"question_id": 32, "title": "数字经济时代的GDP核算困境", "title_en": "GDP Accounting Dilemma in Digital Economy Era", "category": "经济学", "description": "免费数字服务、数据资产和平台交易如何纳入国民经济核算体系？现有方法有哪些局限？", "keywords": ["数字经济", "GDP", "核算", "数据资产"], "difficulty": "medium"},
    {"question_id": 33, "title": "碳定价机制的效率与公平权衡", "title_en": "Efficiency-Equity Tradeoff in Carbon Pricing", "category": "经济学", "description": "碳税与碳排放交易体系在减排效率、收入分配和产业竞争力方面各有何优劣？", "keywords": ["碳定价", "碳税", "排放交易", "气候政策"], "difficulty": "medium"},
    {"question_id": 34, "title": "产业政策的有效性争论：东亚经验", "title_en": "Industrial Policy Effectiveness: East Asian Experience", "category": "经济学", "description": "日本、韩国和中国台湾的产业政策成功是市场失灵矫正的结果，还是特定历史条件的产物？", "keywords": ["产业政策", "东亚模式", "发展经济学", "政府干预"], "difficulty": "medium"},
    {"question_id": 35, "title": "货币政策传导机制的非对称效应", "title_en": "Asymmetric Effects of Monetary Policy Transmission", "category": "经济学", "description": "紧缩性与扩张性货币政策对产出、就业和物价的影响是否存在非对称性？原因何在？", "keywords": ["货币政策", "传导机制", "非对称", "宏观经济"], "difficulty": "hard"},
    {"question_id": 36, "title": "普惠金融与农村减贫的因果关系", "title_en": "Causal Relationship Between Inclusive Finance and Rural Poverty Reduction", "category": "经济学", "description": "小额信贷、移动支付等普惠金融工具是否真正促进了农村贫困人口的收入增长？", "keywords": ["普惠金融", "减贫", "小额信贷", "农村发展"], "difficulty": "medium"},
    {"question_id": 37, "title": "贸易保护主义的政治经济学分析", "title_en": "Political Economy Analysis of Trade Protectionism", "category": "经济学", "description": "为何明知自由贸易的总体福利收益，各国仍频繁采取关税和非关税壁垒？", "keywords": ["贸易保护", "政治经济学", "关税", "利益集团"], "difficulty": "medium"},
    {"question_id": 38, "title": "人力资本投资的回报率测算方法", "title_en": "Return Rate Measurement of Human Capital Investment", "category": "经济学", "description": "明瑟方程和工具变量法在教育收益率估计中各有什么优缺点？最新研究有何突破？", "keywords": ["人力资本", "教育回报", "明瑟方程", "计量方法"], "difficulty": "hard"},
    {"question_id": 39, "title": "房地产泡沫的形成机制与预警指标", "title_en": "Formation Mechanism and Early Warning Indicators of Housing Bubbles", "category": "经济学", "description": "房价收入比、租售比等指标在中国房地产市场泡沫识别中的适用性和局限性。", "keywords": ["房地产", "泡沫", "预警", "金融风险"], "difficulty": "medium"},
    {"question_id": 40, "title": "公共品供给中的搭便车问题解决方案", "title_en": "Solutions to Free-Rider Problem in Public Goods Provision", "category": "经济学", "description": "除了政府强制征税，还有哪些机制可以有效解决公共品供给中的集体行动困境？", "keywords": ["公共品", "搭便车", "集体行动", "制度设计"], "difficulty": "medium"},
    {"question_id": 41, "title": "加密货币对传统货币体系的冲击", "title_en": "Cryptocurrency Impact on Traditional Monetary System", "category": "经济学", "description": "比特币和央行数字货币(CBDC)分别从哪些方面挑战和重塑了现有货币银行体系？", "keywords": ["加密货币", "CBDC", "货币体系", "金融科技"], "difficulty": "medium"},
    {"question_id": 42, "title": "收入分配的库兹涅茨曲线再检验", "title_en": "Re-examination of Kuznets Curve for Income Distribution", "category": "经济学", "description": "皮凯蒂《21世纪资本论》的数据是否推翻了库兹涅茨倒U型假说？中国数据呈现何种形态？", "keywords": ["收入分配", "库兹涅茨曲线", "不平等", "皮凯蒂"], "difficulty": "medium"},
    {"question_id": 43, "title": "供应链韧性与效率的权衡策略", "title_en": "Tradeoff Strategy Between Supply Chain Resilience and Efficiency", "category": "经济学", "description": "后疫情时代企业如何在just-in-time效率与just-in-case韧性之间寻找最优平衡点？", "keywords": ["供应链", "韧性", "风险管理", "全球化"], "difficulty": "medium"},
    {"question_id": 44, "title": "实验经济学中的社会偏好测量", "title_en": "Social Preference Measurement in Experimental Economics", "category": "经济学", "description": "最后通牒博弈、信任博弈等实验范式揭示了人类哪些偏离自利假设的社会偏好？", "keywords": ["实验经济学", "社会偏好", "公平", "博弈论"], "difficulty": "medium"},
    {"question_id": 45, "title": "绿色金融支持碳中和的路径设计", "title_en": "Green Finance Path Design for Carbon Neutrality", "category": "经济学", "description": "绿色债券、ESG投资和转型金融如何协同推动高碳行业的低碳转型？", "keywords": ["绿色金融", "碳中和", "ESG", "转型金融"], "difficulty": "medium"},

    # === 心理学 (46-60) ===
    {"question_id": 46, "title": "依恋类型对成人亲密关系的影响", "title_en": "Attachment Styles Impact on Adult Intimate Relationships", "category": "心理学", "description": "安全型、焦虑型和回避型依恋风格如何预测恋爱满意度、冲突处理和关系稳定性？", "keywords": ["依恋理论", "亲密关系", "成人依恋", "关系质量"], "difficulty": "medium"},
    {"question_id": 47, "title": "认知偏差在临床诊断中的作用", "title_en": "Cognitive Biases in Clinical Diagnosis", "category": "心理学", "description": "确认偏误、锚定效应和可得性启发如何导致心理治疗师的误诊？有哪些去偏差策略？", "keywords": ["认知偏差", "临床诊断", "决策", "心理治疗"], "difficulty": "medium"},
    {"question_id": 48, "title": "正念冥想对情绪调节的神经机制", "title_en": "Neural Mechanisms of Mindfulness Meditation for Emotion Regulation", "category": "心理学", "description": "fMRI研究显示正念训练如何改变前额叶-杏仁核回路的连接强度和情绪反应模式？", "keywords": ["正念", "情绪调节", "神经科学", "冥想"], "difficulty": "hard"},
    {"question_id": 49, "title": "创伤后成长的预测因素与干预", "title_en": "Predictors and Interventions for Post-Traumatic Growth", "category": "心理学", "description": "哪些个体和环境因素促进了创伤后的积极心理变化？PTG与PTSD的关系是什么？", "keywords": ["创伤后成长", "PTSD", "韧性", "心理干预"], "difficulty": "medium"},
    {"question_id": 50, "title": "工作倦怠的JD-R模型验证与扩展", "title_en": "JD-R Model Validation and Extension for Burnout", "category": "心理学", "description": "工作要求-资源模型在不同职业群体中的适用性如何？个人资源应否纳入模型？", "keywords": ["工作倦怠", "JD-R模型", "职业健康", "组织心理学"], "difficulty": "medium"},
    {"question_id": 51, "title": "儿童执行功能发展的影响因素", "title_en": "Factors Influencing Children's Executive Function Development", "category": "心理学", "description": "家庭SES、亲子互动质量和早期教育经历如何共同塑造儿童的抑制控制和工作记忆？", "keywords": ["执行功能", "儿童发展", "认知发展", "家庭教育"], "difficulty": "medium"},
    {"question_id": 52, "title": "社交媒体使用与青少年心理健康", "title_en": "Social Media Use and Adolescent Mental Health", "category": "心理学", "description": "被动浏览vs主动互动、使用时间vs内容质量，哪个维度更能预测青少年的抑郁和焦虑症状？", "keywords": ["社交媒体", "青少年", "心理健康", "抑郁焦虑"], "difficulty": "medium"},
    {"question_id": 53, "title": "内隐态度测量的信效度问题", "title_en": "Reliability and Validity Issues in Implicit Attitude Measurement", "category": "心理学", "description": "IAT的重测信度和预测效度争议反映了内隐社会认知研究的哪些方法论困境？", "keywords": ["内隐态度", "IAT", "测量", "社会认知"], "difficulty": "hard"},
    {"question_id": 54, "title": "积极心理学干预的效果量与持久性", "title_en": "Effect Size and Durability of Positive Psychology Interventions", "category": "心理学", "description": "感恩日记、优势运用等PPIs的meta分析显示多大的效果量？哪些调节变量影响长期效果？", "keywords": ["积极心理学", "干预", "效果量", "幸福感"], "difficulty": "medium"},
    {"question_id": 55, "title": "文化对自我构念的塑造作用", "title_en": "Culture's Shaping Role on Self-Construal", "category": "心理学", "description": "Markus和Kitayama的独立/互依自我构念理论在跨文化研究中得到了怎样的支持和修正？", "keywords": ["文化心理学", "自我构念", "跨文化", " Markus"], "difficulty": "medium"},
    {"question_id": 56, "title": "睡眠障碍与认知功能的因果链", "title_en": "Causal Chain Between Sleep Disorders and Cognitive Function", "category": "心理学", "description": "失眠、睡眠呼吸暂停等障碍通过何种神经生物学通路损害注意力、记忆和执行功能？", "keywords": ["睡眠", "认知功能", "神经生物学", "失眠"], "difficulty": "hard"},
    {"question_id": 57, "title": "群体极化的信息影响与规范影响", "title_en": "Informational and Normative Influence in Group Polarization", "category": "心理学", "description": "说服论证理论和社会比较理论哪个更能解释群体讨论后态度极端化的现象？", "keywords": ["群体极化", "社会影响", "态度", "群体决策"], "difficulty": "medium"},
    {"question_id": 58, "title": "心理弹性测量的多维模型", "title_en": "Multidimensional Models of Psychological Resilience Measurement", "category": "心理学", "description": "CD-RISC、RSA等量表是否充分捕捉了心理弹性的动态过程特征？过程取向测量有何进展？", "keywords": ["心理弹性", "测量", "CD-RISC", "动态过程"], "difficulty": "medium"},
    {"question_id": 59, "title": "具身认知理论的实证支持与争议", "title_en": "Empirical Support and Controversies of Embodied Cognition", "category": "心理学", "description": "身体状态影响认知加工的经典实验（如握力-道德判断）的可重复性危机说明了什么？", "keywords": ["具身认知", "可重复性", "认知科学", "身体"], "difficulty": "hard"},
    {"question_id": 60, "title": "成瘾行为的双过程模型", "title_en": "Dual-Process Model of Addictive Behavior", "category": "心理学", "description": "冲动系统和反思系统的失衡如何解释物质成瘾和行为成瘾的发展与维持？", "keywords": ["成瘾", "双过程", "冲动控制", "行为成瘾"], "difficulty": "medium"},

    # === 历史学 (61-75) ===
    {"question_id": 61, "title": "丝绸之路文化交流的物质证据", "title_en": "Material Evidence of Silk Road Cultural Exchange", "category": "历史学", "description": "考古出土的织物、器物和文书如何揭示古代欧亚大陆的技术传播和艺术交融？", "keywords": ["丝绸之路", "考古", "文化交流", "物质文化"], "difficulty": "medium"},
    {"question_id": 62, "title": "明清海禁政策的经济后果再评估", "title_en": "Reassessment of Ming-Qing Maritime Ban Economic Consequences", "category": "历史学", "description": "朝贡贸易体系和私人海上走私的实际规模是否被官方记载严重低估？", "keywords": ["海禁", "明清", "朝贡贸易", "海洋史"], "difficulty": "medium"},
    {"question_id": 63, "title": "法国大革命中的舆论动员机制", "title_en": "Public Opinion Mobilization in French Revolution", "category": "历史学", "description": "小册子、咖啡馆和政治俱乐部如何构建了革命前的公共领域并推动了政权更迭？", "keywords": ["法国大革命", "舆论", "公共领域", "政治文化"], "difficulty": "medium"},
    {"question_id": 64, "title": "冷战时期第三世界的代理人战争", "title_en": "Proxy Wars in Third World During Cold War", "category": "历史学", "description": "美苏在非洲、东南亚和拉美的代理冲突如何塑造了这些地区的国家建设和发展轨迹？", "keywords": ["冷战", "代理人战争", "第三世界", "地缘政治"], "difficulty": "medium"},
    {"question_id": 65, "title": "宋代科举制度与社会流动性", "title_en": "Song Dynasty Civil Service Exam and Social Mobility", "category": "历史学", "description": "糊名誊录制度是否真正实现了'取士不问家世'？量化史料显示了怎样的社会流动率？", "keywords": ["科举", "宋代", "社会流动", "选官制度"], "difficulty": "medium"},
    {"question_id": 66, "title": "工业革命中技术与制度的协同演化", "title_en": "Co-evolution of Technology and Institutions in Industrial Revolution", "category": "历史学", "description": "专利法、公司制度和金融创新如何与蒸汽机、纺织机械等技术突破相互促进？", "keywords": ["工业革命", "技术", "制度", "协同演化"], "difficulty": "medium"},
    {"question_id": 67, "title": "口述史方法在底层历史研究中的价值", "title_en": "Value of Oral History in Subaltern Studies", "category": "历史学", "description": "当文字记录缺失或带有精英偏见时，口述史料如何重建普通人的生活经验和集体记忆？", "keywords": ["口述史", "底层研究", "记忆", "方法论"], "difficulty": "medium"},
    {"question_id": 68, "title": "晚清洋务运动的失败原因辨析", "title_en": "Analysis of Self-Strengthening Movement Failure Causes", "category": "历史学", "description": "'中体西用'的思想局限、官僚体制的掣肘和国际环境的制约，哪个是洋务运动失败的主因？", "keywords": ["洋务运动", "晚清", "现代化", "改革"], "difficulty": "medium"},
    {"question_id": 69, "title": "环境史视角下的黄河治理与国家能力", "title_en": "Yellow River Governance and State Capacity from Environmental History Perspective", "category": "历史学", "description": "历代治黄工程的成败如何反映了中央集权国家的资源动员能力和地方治理水平？", "keywords": ["环境史", "黄河", "国家能力", "水利"], "difficulty": "medium"},
    {"question_id": 70, "title": "殖民遗产对非洲国家建构的影响", "title_en": "Colonial Legacy Impact on African State Building", "category": "历史学", "description": "人为划定的边界、间接统治和经济依附如何持续影响着撒哈拉以南非洲的政治稳定？", "keywords": ["殖民主义", "非洲", "国家建构", "后殖民"], "difficulty": "medium"},
    {"question_id": 71, "title": "印刷术传播与宗教改革的关系", "title_en": "Printing Press Dissemination and Reformation Relationship", "category": "历史学", "description": "古腾堡印刷术的普及在多大程度上是新教改革成功的必要条件而非充分条件？", "keywords": ["印刷术", "宗教改革", "媒介", "欧洲史"], "difficulty": "medium"},
    {"question_id": 72, "title": "唐代长安城的规划理念与社会秩序", "title_en": "Planning Concepts and Social Order of Tang Chang'an", "category": "历史学", "description": "坊市制度和城市中轴线布局如何体现了唐代的等级秩序和宇宙观？", "keywords": ["长安", "城市规划", "唐代", "空间秩序"], "difficulty": "medium"},
    {"question_id": 73, "title": "大萧条的国际传导与政策响应差异", "title_en": "International Transmission and Policy Response Differences in Great Depression", "category": "历史学", "description": "金本位制的约束如何导致了各国在大萧条中采取了截然不同的财政和货币政策？", "keywords": ["大萧条", "金本位", "国际传导", "经济史"], "difficulty": "hard"},
    {"question_id": 74, "title": "数字人文方法在古代文本分析中的应用", "title_en": "Digital Humanities Methods in Ancient Text Analysis", "category": "历史学", "description": "文本挖掘、网络分析和GIS如何为传统文献学研究带来新的问题和发现？", "keywords": ["数字人文", "文本分析", "方法论", "古代文献"], "difficulty": "medium"},
    {"question_id": 75, "title": "五四新文化运动的思想谱系重绘", "title_en": "Remapping Intellectual Genealogy of May Fourth Movement", "category": "历史学", "description": "超越'启蒙与救亡'的二元叙事，重新梳理五四时期多元并存的思想资源和话语竞争。", "keywords": ["五四运动", "新文化", "思想史", "现代性"], "difficulty": "medium"},

    # === 法学 (76-90) ===
    {"question_id": 76, "title": "算法决策的法律规制框架", "title_en": "Legal Regulatory Framework for Algorithmic Decision-Making", "category": "法学", "description": "自动化行政决定和司法辅助系统中的算法黑箱问题如何通过正当程序和透明度要求加以约束？", "keywords": ["算法治理", "正当程序", "透明度", "人工智能法"], "difficulty": "hard"},
    {"question_id": 77, "title": "个人信息保护的权利基础辨析", "title_en": "Rights Foundation Analysis of Personal Information Protection", "category": "法学", "description": "个人信息权究竟是人格权、财产权还是新型复合权利？不同定性对立法模式有何影响？", "keywords": ["个人信息", "权利基础", "隐私权", "数据保护"], "difficulty": "medium"},
    {"question_id": 78, "title": "宪法审查模式的比较研究", "title_en": "Comparative Study of Constitutional Review Models", "category": "法学", "description": "美国式分散审查、德国式集中审查和法国式事前审查各自的制度优势和运行条件是什么？", "keywords": ["宪法审查", "违宪审查", "比较宪法", "司法审查"], "difficulty": "medium"},
    {"question_id": 79, "title": "环境公益诉讼的原告资格扩展", "title_en": "Standing Expansion in Environmental Public Interest Litigation", "category": "法学", "description": "检察机关和社会组织作为环境公益诉讼原告的实践效果和制度完善方向是什么？", "keywords": ["环境诉讼", "公益诉讼", "原告资格", "环境保护"], "difficulty": "medium"},
    {"question_id": 80, "title": "刑法中因果关系理论的演进", "title_en": "Evolution of Causation Theory in Criminal Law", "category": "法学", "description": "从条件说到相当因果关系再到客观归责，刑法因果关系的判断标准经历了怎样的理论变迁？", "keywords": ["因果关系", "刑法", "归责", "犯罪构成"], "difficulty": "hard"},
    {"question_id": 81, "title": "国际商事仲裁的司法监督边界", "title_en": "Judicial Supervision Boundaries of International Commercial Arbitration", "category": "法学", "description": "《纽约公约》框架下法院对仲裁裁决的审查应在支持仲裁与维护公共政策之间如何平衡？", "keywords": ["国际仲裁", "司法监督", "纽约公约", "商事争议"], "difficulty": "hard"},
    {"question_id": 82, "title": "反垄断法在数字平台领域的适用", "title_en": "Antitrust Law Application in Digital Platform Sector", "category": "法学", "description": "传统相关市场界定和市场支配地位认定方法在面对零价格服务和网络效应时面临哪些挑战？", "keywords": ["反垄断", "数字平台", "市场竞争", "监管"], "difficulty": "medium"},
    {"question_id": 83, "title": "认罪认罚从宽制度的实践检视", "title_en": "Practical Review of Lenient Punishment for Guilty Plea System", "category": "法学", "description": "该制度在提高诉讼效率的同时，是否有效保障了被告人的自愿性和律师的有效辩护？", "keywords": ["认罪认罚", "刑事诉讼", "司法改革", "权利保障"], "difficulty": "medium"},
    {"question_id": 84, "title": "知识产权惩罚性赔偿的适用条件", "title_en": "Application Conditions of Punitive Damages in IP Law", "category": "法学", "description": "故意侵权和情节严重的认定标准在司法实践中如何统一？赔偿倍数的裁量因素有哪些？", "keywords": ["知识产权", "惩罚性赔偿", "侵权", "损害赔偿"], "difficulty": "medium"},
    {"question_id": 85, "title": "劳动法中竞业限制条款的合理性审查", "title_en": "Reasonableness Review of Non-compete Clauses in Labor Law", "category": "法学", "description": "竞业限制的期限、范围和补偿标准如何在保护商业秘密与保障劳动者择业自由之间取得平衡？", "keywords": ["竞业限制", "劳动法", "商业秘密", "择业自由"], "difficulty": "medium"},
    {"question_id": 86, "title": "行政协议纠纷的救济路径选择", "title_en": "Remedy Path Selection for Administrative Agreement Disputes", "category": "法学", "description": "PPP合同、土地出让合同等行政协议的争议应走行政诉讼还是民事诉讼？混合性质如何处理？", "keywords": ["行政协议", "PPP", "救济", "公私法"], "difficulty": "medium"},
    {"question_id": 87, "title": "跨境数据流动的法律冲突与协调", "title_en": "Legal Conflicts and Coordination of Cross-border Data Flow", "category": "法学", "description": "GDPR、中国数据安全法和美国CLOUD Act之间的管辖权冲突如何通过国际合作机制化解？", "keywords": ["数据跨境", "GDPR", "数据安全", "国际法"], "difficulty": "hard"},
    {"question_id": 88, "title": "家事审判改革中的未成年人利益最大化", "title_en": "Best Interests of Child in Family Trial Reform", "category": "法学", "description": "离婚案件中子女抚养权判定如何从父母权利本位转向儿童利益本位？社会调查报告的作用如何发挥？", "keywords": ["家事审判", "儿童利益", "抚养权", "司法改革"], "difficulty": "medium"},
    {"question_id": 89, "title": "法律人工智能的伦理边界", "title_en": "Ethical Boundaries of Legal AI", "category": "法学", "description": "AI法官助手、智能量刑建议和法律检索系统在提升司法效率的同时引发了哪些伦理风险？", "keywords": ["法律AI", "司法伦理", "智能审判", "技术治理"], "difficulty": "medium"},
    {"question_id": 90, "title": "习惯法在国家法体系中的地位", "title_en": "Status of Customary Law in National Legal System", "category": "法学", "description": "少数民族习惯法和行业惯例在民法典实施背景下如何获得国家法的承认和规范？", "keywords": ["习惯法", "国家法", "法律多元", "民法典"], "difficulty": "medium"},

    # === 教育学 (91-105) ===
    {"question_id": 91, "title": "项目式学习对学生高阶思维的影响", "title_en": "Impact of Project-Based Learning on Higher-Order Thinking", "category": "教育学", "description": "PBL在培养批判性思维、创造力和问题解决能力方面的实证效果如何？哪些实施条件最关键？", "keywords": ["项目式学习", "高阶思维", "批判性思维", "教学改革"], "difficulty": "medium"},
    {"question_id": 92, "title": "教师专业发展的校本研修模式", "title_en": "School-Based Research Model for Teacher Professional Development", "category": "教育学", "description": "课例研究、同伴互助和行动研究等校本研修形式对教师教学改进的实际效果有多大？", "keywords": ["教师发展", "校本研修", "课例研究", "专业成长"], "difficulty": "medium"},
    {"question_id": 93, "title": "在线教育的学习者参与度提升策略", "title_en": "Strategies to Enhance Learner Engagement in Online Education", "category": "教育学", "description": "游戏化、社交学习和自适应技术哪种策略对MOOC完成率和学习深度的提升最有效？", "keywords": ["在线教育", "学习者参与", "MOOC", "教学设计"], "difficulty": "medium"},
    {"question_id": 94, "title": "核心素养导向的课程评价体系构建", "title_en": "Competency-Oriented Curriculum Assessment System Construction", "category": "教育学", "description": "表现性评价、档案袋评价和增值评价如何替代标准化测试来衡量学生的核心素养发展？", "keywords": ["核心素养", "课程评价", "表现性评价", "教育改革"], "difficulty": "medium"},
    {"question_id": 95, "title": "双语教育对认知发展的影响研究", "title_en": "Bilingual Education Impact on Cognitive Development Research", "category": "教育学", "description": "早期双语教育是否真的增强了执行功能和元语言意识？关键期和语言阈值假说的证据如何？", "keywords": ["双语教育", "认知发展", "执行功能", "语言习得"], "difficulty": "medium"},
    {"question_id": 96, "title": "STEM教育中的性别差距成因与对策", "title_en": "Gender Gap in STEM Education: Causes and Countermeasures", "category": "教育学", "description": "刻板印象威胁、榜样缺失和课程设计偏见如何共同导致了女性在STEM领域的低参与率？", "keywords": ["STEM", "性别差距", "教育公平", "刻板印象"], "difficulty": "medium"},
    {"question_id": 97, "title": "职业教育产教融合的体制机制障碍", "title_en": "Institutional Barriers to Industry-Education Integration in Vocational Education", "category": "教育学", "description": "校企合作中企业参与动力不足、课程标准脱节和质量监控缺位的深层原因是什么？", "keywords": ["职业教育", "产教融合", "校企合作", "体制改革"], "difficulty": "medium"},
    {"question_id": 98, "title": "特殊教育融合教育的实施挑战", "title_en": "Implementation Challenges of Inclusive Special Education", "category": "教育学", "description": "随班就读政策在实践中面临的师资不足、资源教室匮乏和同伴接纳困难如何系统性解决？", "keywords": ["融合教育", "特殊教育", "随班就读", "教育公平"], "difficulty": "medium"},
    {"question_id": 99, "title": "高等教育国际化与本土化的张力", "title_en": "Tension Between Internationalization and Localization in Higher Education", "category": "教育学", "description": "大学排名驱动的国际化学术标准是否挤压了本土知识体系和教学传统的生存空间？", "keywords": ["高等教育", "国际化", "本土化", "学术评价"], "difficulty": "medium"},
    {"question_id": 100, "title": "形成性评价在课堂教学中的实施策略", "title_en": "Formative Assessment Implementation Strategies in Classroom Teaching", "category": "教育学", "description": "课堂提问、即时反馈和学生自评等形成性评价技术对学业成就的提升效果有多大？", "keywords": ["形成性评价", "课堂教学", "反馈", "学业成就"], "difficulty": "medium"},
    {"question_id": 101, "title": "农村小规模学校的生存与发展策略", "title_en": "Survival and Development Strategies for Rural Small Schools", "category": "教育学", "description": "撤点并校政策调整后，农村小规模学校如何通过复式教学、远程教育和社区合作实现优质发展？", "keywords": ["农村教育", "小规模学校", "教育公平", "乡村振兴"], "difficulty": "medium"},
    {"question_id": 102, "title": "研究生导师指导关系的权力与伦理", "title_en": "Power and Ethics in Graduate Supervisor-Mentee Relationships", "category": "教育学", "description": "导学关系中的权力不对等如何影响了研究生的学术发展和心理健康？制度化保障措施有哪些？", "keywords": ["研究生教育", "导师制", "学术伦理", "权力关系"], "difficulty": "medium"},
    {"question_id": 103, "title": "教育数字化转型的伦理风险", "title_en": "Ethical Risks of Education Digital Transformation", "category": "教育学", "description": "学习分析、面部识别和AI评分等技术在教育应用中引发了哪些隐私、公平和自主性担忧？", "keywords": ["教育数字化", "伦理", "学习分析", "技术治理"], "difficulty": "medium"},
    {"question_id": 104, "title": "终身学习体系建设的制度障碍", "title_en": "Institutional Barriers to Lifelong Learning System Construction", "category": "教育学", "description": "学分银行、资历框架和非正规学习认证在打通学历与非学历教育通道中面临哪些瓶颈？", "keywords": ["终身学习", "学分银行", "资历框架", "制度建设"], "difficulty": "medium"},
    {"question_id": 105, "title": "校园欺凌的生态系统干预模型", "title_en": "Ecological Systems Intervention Model for School Bullying", "category": "教育学", "description": "超越个体层面的惩戒，如何从班级氛围、学校文化和家校社协同角度构建反欺凌长效机制？", "keywords": ["校园欺凌", "生态系统", "干预", "学校安全"], "difficulty": "medium"},

    # === 文学/语言学 (106-115) ===
    {"question_id": 106, "title": "叙事医学在临床实践中的应用价值", "title_en": "Narrative Medicine Application Value in Clinical Practice", "category": "文学", "description": "疾病叙事和文学阅读如何帮助医学生培养共情能力和反思性实践？", "keywords": ["叙事医学", "共情", "临床实践", "人文关怀"], "difficulty": "medium"},
    {"question_id": 107, "title": "网络文学的类型化生产机制", "title_en": "Genre Production Mechanism of Web Literature", "category": "文学", "description": "付费阅读、读者反馈和平台算法如何共同塑造了网络文学的类型分化和叙事套路？", "keywords": ["网络文学", "类型化", "平台", "文学生产"], "difficulty": "medium"},
    {"question_id": 108, "title": "隐喻认知的跨语言比较研究", "title_en": "Cross-Linguistic Comparative Study of Metaphorical Cognition", "category": "语言学", "description": "Lakoff的概念隐喻理论在不同语言文化中是否具有普遍性？汉语隐喻系统有何独特性？", "keywords": ["隐喻", "认知语言学", "跨语言", "概念隐喻"], "difficulty": "medium"},
    {"question_id": 109, "title": "方言保护与普通话推广的平衡", "title_en": "Balance Between Dialect Preservation and Mandarin Promotion", "category": "语言学", "description": "在推广国家通用语言文字的同时，如何通过语言生态规划和数字化手段保存方言多样性？", "keywords": ["方言", "普通话", "语言政策", "语言多样性"], "difficulty": "medium"},
    {"question_id": 110, "title": "翻译中的文化不可译性问题", "title_en": "Cultural Untranslatability in Translation", "category": "语言学", "description": "成语、典故和文化负载词的翻译策略如何在忠实原文与目标语可读性之间取舍？", "keywords": ["翻译", "文化", "不可译性", "跨文化传播"], "difficulty": "medium"},
    {"question_id": 111, "title": "二语习得中的母语迁移效应", "title_en": "L1 Transfer Effects in Second Language Acquisition", "category": "语言学", "description": "正迁移和负迁移在语音、词汇、语法和语用层面各有哪些典型表现？教学如何应对？", "keywords": ["二语习得", "母语迁移", "语言教学", "对比分析"], "difficulty": "medium"},
    {"question_id": 112, "title": "话语分析在政治传播中的应用", "title_en": "Discourse Analysis Application in Political Communication", "category": "语言学", "description": "批评话语分析和框架理论如何揭示政治演讲和新闻报道中的意识形态运作机制？", "keywords": ["话语分析", "政治传播", "意识形态", "批评语言学"], "difficulty": "medium"},
    {"question_id": 113, "title": "古典诗词意象的现代阐释学解读", "title_en": "Modern Hermeneutic Interpretation of Classical Poetry Imagery", "category": "文学", "description": "伽达默尔的视域融合理论如何为唐诗宋词中月亮、落花等经典意象提供新的理解维度？", "keywords": ["古典诗词", "意象", "阐释学", "文学批评"], "difficulty": "medium"},
    {"question_id": 114, "title": "计算语言学在古籍整理中的应用", "title_en": "Computational Linguistics Application in Ancient Text Collation", "category": "语言学", "description": "NLP技术在校勘、断句、实体识别和知识图谱构建方面为古籍数字化带来了哪些突破？", "keywords": ["计算语言学", "古籍", "NLP", "数字化"], "difficulty": "medium"},
    {"question_id": 115, "title": "儿童语言习得的输入假说检验", "title_en": "Input Hypothesis Testing in Child Language Acquisition", "category": "语言学", "description": "Krashen的可理解输入假说在儿童母语和二语习得中分别获得了怎样的实证支持和反驳？", "keywords": ["语言习得", "输入假说", "儿童", "Krashen"], "difficulty": "medium"},

    # === 管理学/公共管理 (116-125) ===
    {"question_id": 116, "title": "敏捷管理在传统组织中的适应性改造", "title_en": "Adaptive Transformation of Agile Management in Traditional Organizations", "category": "管理学", "description": "Scrum和看板等方法在非IT行业和大型科层组织中落地时需要做哪些本土化和情境化调整？", "keywords": ["敏捷管理", "组织变革", "Scrum", "管理创新"], "difficulty": "medium"},
    {"question_id": 117, "title": "公共服务动机的前因变量与结果变量", "title_en": "Antecedents and Outcomes of Public Service Motivation", "category": "公共管理", "description": "PSM的来源是社会教化还是自我选择？高PSM公务员的工作绩效和组织承诺是否确实更高？", "keywords": ["公共服务动机", "公务员", "绩效管理", "公共部门"], "difficulty": "medium"},
    {"question_id": 118, "title": "危机领导力模型的跨情境比较", "title_en": "Cross-Situational Comparison of Crisis Leadership Models", "category": "管理学", "description": "自然灾害、公共卫生事件和企业危机中有效领导力的核心要素有何共通性和差异性？", "keywords": ["危机领导", "应急管理", "领导力", "比较研究"], "difficulty": "medium"},
    {"question_id": 119, "title": "基层治理中的形式主义生成机制", "title_en": "Generation Mechanism of Formalism in Grassroots Governance", "category": "公共管理", "description": "痕迹管理、过度留痕和迎检文化背后的制度逻辑和行为激励是什么？如何从根源上治理？", "keywords": ["基层治理", "形式主义", "制度逻辑", "行政负担"], "difficulty": "medium"},
    {"question_id": 120, "title": "ESG评级对企业价值的影响机制", "title_en": "ESG Rating Impact Mechanism on Firm Value", "category": "管理学", "description": "ESG表现是通过降低融资成本、提升品牌声誉还是改善运营效率来影响企业财务绩效的？", "keywords": ["ESG", "企业价值", "可持续发展", "公司治理"], "difficulty": "medium"},
    {"question_id": 121, "title": "数字政府建设中的数据孤岛破解", "title_en": "Breaking Data Silos in Digital Government Construction", "category": "公共管理", "description": "部门间数据共享的技术障碍、制度壁垒和利益博弈如何通过顶层设计和激励机制协同解决？", "keywords": ["数字政府", "数据共享", "数据孤岛", "政务信息化"], "difficulty": "medium"},
    {"question_id": 122, "title": "组织沉默的前因与干预策略", "title_en": "Antecedents and Intervention Strategies of Organizational Silence", "category": "管理学", "description": "员工为何选择不表达意见？心理安全感、领导风格和举报渠道如何影响建言行为？", "keywords": ["组织沉默", "建言行为", "心理安全", "组织行为"], "difficulty": "medium"},
    {"question_id": 123, "title": "政策试点扩散的条件与阻滞因素", "title_en": "Conditions and Blocking Factors of Policy Pilot Diffusion", "category": "公共管理", "description": "中国特色的'试点-推广'模式中，哪些因素决定了地方创新能否成功上升为国家政策？", "keywords": ["政策试点", "政策扩散", "制度创新", "中国治理"], "difficulty": "medium"},
    {"question_id": 124, "title": "共享经济平台的信任构建机制", "title_en": "Trust Building Mechanism in Sharing Economy Platforms", "category": "管理学", "description": "评分系统、实名认证和第三方担保等机制如何协同解决了陌生人交易中的信任赤字？", "keywords": ["共享经济", "信任", "平台治理", "数字经济"], "difficulty": "medium"},
    {"question_id": 125, "title": "智库影响力评估的多维指标体系", "title_en": "Multidimensional Indicator System for Think Tank Influence Assessment", "category": "公共管理", "description": "如何超越媒体曝光度和引用次数，建立涵盖政策采纳、议程设置和观念传播的综合评估框架？", "keywords": ["智库", "影响力评估", "政策研究", "知识生产"], "difficulty": "medium"},
]

async def seed():
    print('='*60)
    print(f'🌱 准备插入 {len(SEED_QUESTIONS)} 道种子题目')
    print('='*60)

    async with AsyncSessionLocal() as db:
        # 检查是否已有数据
        from sqlalchemy import select, func
        count = (await db.execute(select(func.count()).select_from(ScienceQuestion))).scalar()
        if count > 0:
            print(f'   ⚠️ science_questions 已有 {count} 条数据，跳过插入')
            return

        # 批量插入
        questions = []
        for i, q in enumerate(SEED_QUESTIONS):
            sq = ScienceQuestion(
                question_id=q["question_id"],
                title=q["title"],
                title_en=q.get("title_en"),
                category=q["category"],
                description=q.get("description", ""),
                keywords=q.get("keywords", []),
                difficulty=q.get("difficulty", "medium"),
                source="seed_v1",
                is_active=True,
                sort_order=i,
            )
            questions.append(sq)

        db.add_all(questions)
        await db.commit()
        print(f'   ✅ 成功插入 {len(questions)} 道题目')

        # 按类别统计
        rows = await db.execute(
            select(ScienceQuestion.category, func.count())
            .group_by(ScienceQuestion.category)
            .order_by(func.count().desc())
        )
        print(f'\n   📊 按类别分布:')
        for cat, cnt in rows.fetchall():
            print(f'      {cat}: {cnt} 题')

    print(f'\n✅ 种子数据插入完成！')

asyncio.run(seed())
