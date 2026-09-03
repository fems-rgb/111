import asyncio, sys, os
sys.path.insert(0, r'D:\AI_Scientist\AI_Scientist\backend')
os.chdir(r'D:\AI_Scientist\AI_Scientist\backend')

from app.database.session import AsyncSessionLocal
from app.database.models import ScienceQuestion

# Science杂志2005年创刊125周年 - 125个最具挑战性科学问题
# 前25个为最重要问题，后100个为重要问题
SEED_QUESTIONS = [
    # ═══ 前25个最重要问题 ═══
    {"question_id": 1, "title": "宇宙由什么构成？", "title_en": "What is the universe made of?", "category": "天文学/物理学", "description": "暗物质和暗能量占宇宙总质量能量的95%以上，但它们的本质仍是未解之谜。", "keywords": ["暗物质", "暗能量", "宇宙学"], "difficulty": "hard"},
    {"question_id": 2, "title": "意识的生物学基础是什么？", "title_en": "What is the biological basis of consciousness?", "category": "神经科学", "description": "主观体验如何从大脑的神经活动中产生？这是心灵哲学和神经科学的终极问题。", "keywords": ["意识", "神经相关物", "主观体验"], "difficulty": "hard"},
    {"question_id": 3, "title": "为什么人类基因会如此之少？", "title_en": "Why do humans have so few genes?", "category": "遗传学", "description": "人类仅有约2万个蛋白编码基因，与线虫相当，远低于预期。基因调控的复杂性如何解释人类的复杂性？", "keywords": ["基因组", "基因调控", "非编码RNA"], "difficulty": "medium"},
    {"question_id": 4, "title": "遗传变异与人类健康的相关程度如何？", "title_en": "To what extent are genetic variations and personal health correlated?", "category": "医学/遗传学", "description": "全基因组关联研究能否真正实现精准医疗？基因-环境互作如何影响疾病风险？", "keywords": ["GWAS", "精准医疗", "基因-环境互作"], "difficulty": "medium"},
    {"question_id": 5, "title": "基本物理定律能否统一？", "title_en": "Can the laws of physics be unified?", "category": "物理学", "description": "广义相对论与量子力学的统一是理论物理学的圣杯。弦理论和圈量子引力哪个方向更有前景？", "keywords": ["统一理论", "量子引力", "弦理论"], "difficulty": "hard"},
    {"question_id": 6, "title": "生命如何在地球上起源？", "title_en": "How did life begin on Earth?", "category": "生命科学", "description": "从无机分子到自我复制的生命系统，化学演化到生物演化的关键跃迁是如何发生的？", "keywords": ["生命起源", "化学演化", "RNA世界"], "difficulty": "hard"},
    {"question_id": 7, "title": "物种多样性为何如此丰富？", "title_en": "What makes species diversity so rich?", "category": "生态学", "description": "热带雨林和珊瑚礁中极高的物种多样性是如何形成和维持的？中性理论与生态位理论之争。", "keywords": ["生物多样性", "物种形成", "群落生态学"], "difficulty": "medium"},
    {"question_id": 8, "title": "哪些遗传变化使我们成为独特的人类？", "title_en": "What genetic changes made us uniquely human?", "category": "进化生物学", "description": "人与黑猩猩基因组相似度达99%，哪些关键遗传差异导致了语言、文化和抽象思维能力的出现？", "keywords": ["人类进化", "FOXP2", "脑进化"], "difficulty": "medium"},
    {"question_id": 9, "title": "疾病的生理基础如何被追踪？", "title_en": "How are physiological foundations of disease traced?", "category": "医学", "description": "从分子水平到器官系统，疾病的因果链条如何被完整解析以指导靶向治疗？", "keywords": ["病理机制", "转化医学", "生物标志物"], "difficulty": "medium"},
    {"question_id": 10, "title": "衰老的内在机制是什么？", "title_en": "What is the underlying mechanism of aging?", "category": "生命科学", "description": "端粒缩短、表观遗传漂变、蛋白质稳态失衡等衰老标志之间是否存在统一的驱动因素？", "keywords": ["衰老", "端粒", "表观遗传"], "difficulty": "medium"},
    {"question_id": 11, "title": "地球内部如何运作？", "title_en": "How does Earth's interior work?", "category": "地球科学", "description": "地核对流、板块运动和地磁场的精确机制仍有大量未知。深部地球探测技术面临极限挑战。", "keywords": ["地球内部", "板块构造", "地核"], "difficulty": "medium"},
    {"question_id": 12, "title": "地球上的水从何而来？", "title_en": "Where does Earth's water come from?", "category": "地球科学", "description": "地球水是原始星云残留还是后期彗星/小行星输送？水的来源决定了宜居行星的形成条件。", "keywords": ["水的起源", "行星形成", "挥发分"], "difficulty": "medium"},
    {"question_id": 13, "title": "什么控制了地球的冰期循环？", "title_en": "What controls ice age cycles?", "category": "气候科学", "description": "米兰科维奇轨道周期如何触发冰期-间冰期旋回？CO2反馈和海洋环流的放大作用有多大？", "keywords": ["冰期", "米兰科维奇循环", "古气候"], "difficulty": "medium"},
    {"question_id": 14, "title": "什么引发了寒武纪大爆发？", "title_en": "What triggered the Cambrian explosion?", "category": "古生物学", "description": "约5.4亿年前多细胞动物门类在极短时间内大量出现，氧气、基因工具包和生态竞争哪个是主因？", "keywords": ["寒武纪大爆发", "动物演化", "埃迪卡拉纪"], "difficulty": "medium"},
    {"question_id": 15, "title": "灭绝事件为何反复发生？", "title_en": "Why do mass extinctions recur?", "category": "古生物学", "description": "五次大灭绝的触发机制各不相同，是否存在周期性规律？第六次大灭绝是否已经开始？", "keywords": ["大灭绝", "生物危机", "地质灾变"], "difficulty": "medium"},
    {"question_id": 16, "title": "太阳能何时能取代化石燃料？", "title_en": "When will solar energy replace fossil fuels?", "category": "能源科学", "description": "光伏效率提升、储能技术和电网改造的瓶颈在哪里？经济可行性时间表如何预测？", "keywords": ["太阳能", "可再生能源", "能源转型"], "difficulty": "medium"},
    {"question_id": 17, "title": "全球变暖将走向何方？", "title_en": "Where is global warming heading?", "category": "气候科学", "description": "气候敏感度的不确定性、碳循环反馈和临界点风险使长期预测充满挑战。", "keywords": ["气候变化", "温室效应", "气候模型"], "difficulty": "medium"},
    {"question_id": 18, "title": "人口增长何时停止？", "title_en": "When will population growth stop?", "category": "人口学", "description": "生育率下降、老龄化和城市化如何共同决定全球人口的峰值和稳定时间？", "keywords": ["人口增长", "生育率", "人口转型"], "difficulty": "medium"},
    {"question_id": 19, "title": "贫困的根源是什么？", "title_en": "What are the roots of poverty?", "category": "社会科学", "description": "制度缺陷、地理劣势、文化因素和历史遗产在贫困陷阱中各自扮演什么角色？", "keywords": ["贫困", "发展经济学", "不平等"], "difficulty": "medium"},
    {"question_id": 20, "title": "恐怖主义的根源是什么？", "title_en": "What are the roots of terrorism?", "category": "政治学", "description": "意识形态、社会经济剥夺、政治压迫和心理因素如何交织催生极端暴力行为？", "keywords": ["恐怖主义", "极端主义", "冲突"], "difficulty": "medium"},
    {"question_id": 21, "title": "宗教的起源和功能是什么？", "title_en": "What are the origins and functions of religion?", "category": "人类学", "description": "宗教信仰是适应性进化的产物还是认知副产物？它在社会凝聚和个人心理中发挥什么作用？", "keywords": ["宗教", "进化心理学", "文化演化"], "difficulty": "medium"},
    {"question_id": 22, "title": "语言的起源是什么？", "title_en": "What is the origin of language?", "category": "语言学/认知科学", "description": "人类语言能力是基因突变的结果还是渐进文化演化的产物？手势理论和歌唱理论哪个更可信？", "keywords": ["语言起源", "FOXP2", "符号系统"], "difficulty": "hard"},
    {"question_id": 23, "title": "合作行为的进化基础是什么？", "title_en": "What is the evolutionary basis of cooperation?", "category": "进化生物学", "description": "利他行为和互惠合作如何在自然选择的框架下演化？亲缘选择、互惠利他和群体选择的相对贡献。", "keywords": ["合作", "利他主义", "博弈论"], "difficulty": "medium"},
    {"question_id": 24, "title": "记忆的存储和提取机制是什么？", "title_en": "How are memories stored and retrieved?", "category": "神经科学", "description": "突触可塑性、记忆巩固和海马体-皮层对话的分子与环路机制仍有大量空白。", "keywords": ["记忆", "突触可塑性", "海马体"], "difficulty": "medium"},
    {"question_id": 25, "title": "计算机能否像人一样思考？", "title_en": "Can computers think like humans?", "category": "计算机科学/AI", "description": "通用人工智能是否可能实现？符号主义、连接主义和具身认知哪条路径更接近人类智能？", "keywords": ["人工智能", "AGI", "图灵测试"], "difficulty": "hard"},

    # ═══ 后100个问题 (26-125) ═══
    # --- 宇宙与天文学 ---
    {"question_id": 26, "title": "暗物质的本质是什么？", "title_en": "What is dark matter?", "category": "物理学", "description": "WIMP、轴子还是修正引力理论？直接探测实验为何至今未发现信号？", "keywords": ["暗物质", "WIMP", "粒子物理"], "difficulty": "hard"},
    {"question_id": 27, "title": "暗能量的本质是什么？", "title_en": "What is dark energy?", "category": "物理学", "description": "宇宙加速膨胀的驱动力是宇宙学常数、精质场还是修改引力？", "keywords": ["暗能量", "宇宙加速膨胀", "宇宙学常数"], "difficulty": "hard"},
    {"question_id": 28, "title": "黑洞信息悖论如何解决？", "title_en": "How is the black hole information paradox resolved?", "category": "物理学", "description": "霍金辐射是否导致信息丢失？全息原理和火墙假说的争论焦点是什么？", "keywords": ["黑洞", "信息悖论", "霍金辐射"], "difficulty": "hard"},
    {"question_id": 29, "title": "宇宙是否有额外的维度？", "title_en": "Are there extra dimensions?", "category": "物理学", "description": "弦理论预言的高维空间能否通过粒子对撞或引力波观测得到验证？", "keywords": ["额外维度", "弦理论", "高维物理"], "difficulty": "hard"},
    {"question_id": 30, "title": "宇宙的命运是什么？", "title_en": "What is the fate of the universe?", "category": "天文学", "description": "大撕裂、热寂还是大坍缩？暗能量状态方程的精确测量是关键。", "keywords": ["宇宙命运", "热寂", "大撕裂"], "difficulty": "medium"},
    {"question_id": 31, "title": "系外行星上是否存在生命？", "title_en": "Is there life on exoplanets?", "category": "天文学", "description": "生物标志气体的探测技术和宜居带定义如何影响我们对地外生命的判断？", "keywords": ["系外行星", "生物标志", "宜居性"], "difficulty": "medium"},
    {"question_id": 32, "title": "第一代恒星和星系如何形成？", "title_en": "How did the first stars and galaxies form?", "category": "天文学", "description": "JWST的早期观测结果是否挑战了现有的星系形成模型？", "keywords": ["第一代恒星", "再电离", "JWST"], "difficulty": "medium"},
    {"question_id": 33, "title": "引力波能揭示什么新物理？", "title_en": "What new physics can gravitational waves reveal?", "category": "物理学", "description": "多信使天文学时代，引力波如何检验强场引力和中子星物态方程？", "keywords": ["引力波", "LIGO", "多信使天文学"], "difficulty": "medium"},
    {"question_id": 34, "title": "太阳系的形成过程是怎样的？", "title_en": "How did the solar system form?", "category": "天文学", "description": "行星迁移、晚期重轰炸和小行星带的动力学历史仍有许多争议。", "keywords": ["太阳系形成", "行星迁移", "原行星盘"], "difficulty": "medium"},
    {"question_id": 35, "title": "超新星爆发的机制是什么？", "title_en": "What triggers supernova explosions?", "category": "天体物理", "description": "核心坍缩超新星的爆炸机制和中微子驱动的延迟爆炸模型仍存争议。", "keywords": ["超新星", "核心坍缩", "核合成"], "difficulty": "hard"},

    # --- 物理学与物质科学 ---
    {"question_id": 36, "title": "高温超导的机制是什么？", "title_en": "What is the mechanism of high-Tc superconductivity?", "category": "凝聚态物理", "description": "铜氧化物和铁基超导体的配对机制是否相同？室温超导是否可能实现？", "keywords": ["高温超导", "铜氧化物", "BCS理论"], "difficulty": "hard"},
    {"question_id": 37, "title": "量子纠缠的非定域性意味着什么？", "title_en": "What does quantum nonlocality imply?", "category": "量子物理", "description": "贝尔不等式违背是否排除了所有局域隐变量理论？量子信息与量子引力的联系。", "keywords": ["量子纠缠", "贝尔不等式", "非定域性"], "difficulty": "hard"},
    {"question_id": 38, "title": "拓扑物态的分类和应用前景？", "title_en": "Classification and applications of topological phases?", "category": "凝聚态物理", "description": "拓扑绝缘体、外尔半金属和拓扑超导体如何推动容错量子计算？", "keywords": ["拓扑物态", "拓扑绝缘体", "马约拉纳费米子"], "difficulty": "hard"},
    {"question_id": 39, "title": "湍流的普适规律是什么？", "title_en": "What are the universal laws of turbulence?", "category": "流体力学", "description": "纳维-斯托克斯方程的全局正则性和湍流能量级联的精确描述仍是千禧年难题。", "keywords": ["湍流", "N-S方程", "能量级联"], "difficulty": "hard"},
    {"question_id": 40, "title": "玻璃态转变的本质是什么？", "title_en": "What is the nature of glass transition?", "category": "材料科学", "description": "过冷液体到非晶固体的转变是热力学相变还是动力学冻结？", "keywords": ["玻璃化转变", "非晶态", "动力学"], "difficulty": "hard"},
    {"question_id": 41, "title": "纳米材料的奇异性质源于什么？", "title_en": "What causes exotic properties in nanomaterials?", "category": "纳米科学", "description": "量子限域效应、表面效应和尺寸效应如何协同决定纳米材料的光电磁性质？", "keywords": ["纳米材料", "量子限域", "表面效应"], "difficulty": "medium"},
    {"question_id": 42, "title": "催化反应的活性位点如何精确表征？", "title_en": "How to precisely characterize active sites in catalysis?", "category": "化学", "description": "原位表征技术和理论计算如何协同揭示催化剂在工作条件下的真实活性中心？", "keywords": ["催化", "活性位点", "原位表征"], "difficulty": "medium"},
    {"question_id": 43, "title": "光合作用的量子效率为何如此之高？", "title_en": "Why is photosynthetic quantum efficiency so high?", "category": "生物物理", "description": "量子相干性在光合能量传递中的作用有多大？人工光合作用能否模拟这一机制？", "keywords": ["光合作用", "量子相干", "能量传递"], "difficulty": "medium"},
    {"question_id": 44, "title": "手性的起源是什么？", "title_en": "What is the origin of chirality?", "category": "化学", "description": "生命分子的同手性是偶然对称破缺还是宇宙物理因素的必然结果？", "keywords": ["手性", "对称破缺", "生命起源"], "difficulty": "medium"},
    {"question_id": 45, "title": "新材料的设计能否完全依靠计算？", "title_en": "Can new materials be designed purely by computation?", "category": "材料科学", "description": "高通量筛选、机器学习和第一性原理计算的结合能否替代试错法？", "keywords": ["材料设计", "高通量筛选", "机器学习"], "difficulty": "medium"},

    # --- 生命科学 ---
    {"question_id": 46, "title": "蛋白质折叠的密码是什么？", "title_en": "What is the code of protein folding?", "category": "结构生物学", "description": "AlphaFold的成功是否意味着蛋白质折叠问题已解决？动态构象和分子伴侣的作用呢？", "keywords": ["蛋白质折叠", "AlphaFold", "分子伴侣"], "difficulty": "medium"},
    {"question_id": 47, "title": "基因表达调控的网络逻辑是什么？", "title_en": "What is the network logic of gene regulation?", "category": "分子生物学", "description": "转录因子、增强子和三维基因组结构如何协同实现精确的时空表达模式？", "keywords": ["基因调控", "增强子", "三维基因组"], "difficulty": "medium"},
    {"question_id": 48, "title": "细胞命运决定的分子开关是什么？", "title_en": "What are the molecular switches of cell fate determination?", "category": "发育生物学", "description": "干细胞分化、转分化和去分化的表观遗传重编程机制如何被精确控制？", "keywords": ["细胞命运", "干细胞", "表观遗传重编程"], "difficulty": "medium"},
    {"question_id": 49, "title": "免疫系统如何区分自我与非我？", "title_en": "How does the immune system distinguish self from non-self?", "category": "免疫学", "description": "中枢和外周耐受机制的失败如何导致自身免疫病？免疫检查点的调控网络。", "keywords": ["免疫耐受", "自身免疫", "T细胞"], "difficulty": "medium"},
    {"question_id": 50, "title": "癌症的根本原因是什么？", "title_en": "What is the fundamental cause of cancer?", "category": "肿瘤学", "description": "体细胞突变、表观遗传异常和微环境失调在肿瘤发生中的相对权重和时序关系。", "keywords": ["癌症", "致癌突变", "肿瘤微环境"], "difficulty": "medium"},
    {"question_id": 51, "title": "微生物组如何影响宿主健康？", "title_en": "How does the microbiome affect host health?", "category": "微生物学", "description": "肠-脑轴、代谢调节和免疫训练的具体分子通路和因果关系链。", "keywords": ["微生物组", "肠-脑轴", "共生菌"], "difficulty": "medium"},
    {"question_id": 52, "title": "抗生素耐药性如何遏制？", "title_en": "How to curb antibiotic resistance?", "category": "微生物学", "description": "新型抗菌策略（噬菌体、CRISPR、抗毒力因子）的临床转化前景和挑战。", "keywords": ["抗生素耐药", "噬菌体", "AMR"], "difficulty": "medium"},
    {"question_id": 53, "title": "病毒的跨物种传播机制是什么？", "title_en": "What drives viral cross-species transmission?", "category": "病毒学", "description": "受体兼容性、宿主因子和生态接触界面在新发传染病预警中的关键作用。", "keywords": ["跨物种传播", "新发传染病", "人畜共患"], "difficulty": "medium"},
    {"question_id": 54, "title": "表观遗传信息的遗传机制是什么？", "title_en": "What is the inheritance mechanism of epigenetic information?", "category": "表观遗传学", "description": "DNA甲基化、组蛋白修饰和非编码RNA的跨代传递证据和分子基础。", "keywords": ["表观遗传", "跨代遗传", "DNA甲基化"], "difficulty": "medium"},
    {"question_id": 55, "title": "细胞器的起源和内共生理论的细节？", "title_en": "Details of organelle origin and endosymbiosis theory?", "category": "进化生物学", "description": "线粒体和叶绿体的内共生事件的时间线和基因转移过程的精确重建。", "keywords": ["内共生", "线粒体", "细胞器进化"], "difficulty": "medium"},
    {"question_id": 56, "title": "生物钟的分子机制如何与环境同步？", "title_en": "How do circadian clocks synchronize with environment?", "category": "生理学", "description": "核心时钟基因的转录-翻译反馈环如何被光、温度和进食信号校准？", "keywords": ["生物钟", "昼夜节律", "时钟基因"], "difficulty": "medium"},
    {"question_id": 57, "title": "再生能力的分子基础是什么？", "title_en": "What is the molecular basis of regeneration?", "category": "发育生物学", "description": "蝾螈和斑马鱼的完美再生能力为何在哺乳动物中丧失？能否重新激活？", "keywords": ["再生", "去分化", "再生医学"], "difficulty": "medium"},
    {"question_id": 58, "title": "植物如何感知和响应环境胁迫？", "title_en": "How do plants sense and respond to environmental stress?", "category": "植物学", "description": "干旱、盐碱和病原体信号的整合网络和系统性获得性抗性的长距离传导。", "keywords": ["植物胁迫", "信号转导", "抗逆性"], "difficulty": "medium"},
    {"question_id": 59, "title": "RNA的多功能性边界在哪里？", "title_en": "Where are the boundaries of RNA versatility?", "category": "分子生物学", "description": "lncRNA、circRNA和RNA修饰在基因调控、疾病和进化中的功能图谱。", "keywords": ["非编码RNA", "RNA修饰", "表观转录组"], "difficulty": "medium"},
    {"question_id": 60, "title": "合成生物学能否创造全新生命？", "title_en": "Can synthetic biology create entirely new life?", "category": "合成生物学", "description": "最小基因组、人工碱基对和非天然氨基酸扩展了生命的化学可能性到什么程度？", "keywords": ["合成生物学", "人工生命", "最小基因组"], "difficulty": "medium"},

    # --- 神经科学与认知 ---
    {"question_id": 61, "title": "大脑如何编码和处理信息？", "title_en": "How does the brain encode and process information?", "category": "神经科学", "description": "神经编码是速率编码、时间编码还是群体编码？不同脑区的信息处理范式有何差异？", "keywords": ["神经编码", "信息处理", "脑功能"], "difficulty": "hard"},
    {"question_id": 62, "title": "情绪的生物化学基础是什么？", "title_en": "What is the biochemical basis of emotions?", "category": "神经科学", "description": "单胺类递质、肽类和激素在情绪回路中的精确作用和个体差异的来源。", "keywords": ["情绪", "神经递质", "边缘系统"], "difficulty": "medium"},
    {"question_id": 63, "title": "睡眠的功能是什么？", "title_en": "What is the function of sleep?", "category": "神经科学", "description": "记忆巩固、代谢废物清除和突触稳态恢复假说的整合框架。", "keywords": ["睡眠", "记忆巩固", "类淋巴系统"], "difficulty": "medium"},
    {"question_id": 64, "title": "成瘾的神经回路机制是什么？", "title_en": "What are the neural circuit mechanisms of addiction?", "category": "神经科学", "description": "奖赏系统、习惯系统和执行控制系统的失衡如何导致强迫性用药行为？", "keywords": ["成瘾", "奖赏系统", "多巴胺"], "difficulty": "medium"},
    {"question_id": 65, "title": "精神疾病的生物学标记是什么？", "title_en": "What are the biological markers of mental illness?", "category": "精神医学", "description": "精神分裂症、抑郁症和自闭症的客观生物标志物为何难以确立？RDoC框架的前景。", "keywords": ["精神疾病", "生物标志物", "RDoC"], "difficulty": "medium"},
    {"question_id": 66, "title": "大脑如何实现学习和可塑性？", "title_en": "How does the brain achieve learning and plasticity?", "category": "神经科学", "description": "LTP/LTD、结构可塑性和成人神经发生在不同学习类型中的贡献。", "keywords": ["学习", "突触可塑性", "LTP"], "difficulty": "medium"},
    {"question_id": 67, "title": "注意力的神经机制是什么？", "title_en": "What are the neural mechanisms of attention?", "category": "认知神经科学", "description": "自上而下和自下而上注意力选择的神经基底和网络动力学模型。", "keywords": ["注意力", "选择性注意", "前额叶"], "difficulty": "medium"},
    {"question_id": 68, "title": "决策的神经经济学基础是什么？", "title_en": "What is the neuroeconomic basis of decision-making?", "category": "认知神经科学", "description": "价值评估、风险评估和时间折扣的神经计算模型及其偏差来源。", "keywords": ["决策", "神经经济学", "价值计算"], "difficulty": "medium"},
    {"question_id": 69, "title": "社会认知的神经基础是什么？", "title_en": "What is the neural basis of social cognition?", "category": "社会神经科学", "description": "心智理论、镜像神经元系统和催产素在社会互动中的作用和争议。", "keywords": ["社会认知", "心智理论", "镜像神经元"], "difficulty": "medium"},
    {"question_id": 70, "title": "脑机接口的极限在哪里？", "title_en": "What are the limits of brain-computer interfaces?", "category": "神经工程", "description": "侵入式和非侵入式BCI的信息传输率上限、长期稳定性和伦理边界。", "keywords": ["脑机接口", "BCI", "神经解码"], "difficulty": "medium"},

    # --- 地球与环境科学 ---
    {"question_id": 71, "title": "地震能否被可靠预测？", "title_en": "Can earthquakes be reliably predicted?", "category": "地球物理", "description": "前兆信号的可靠性争议和概率预报vs确定性预报的方法论之争。", "keywords": ["地震预测", "前兆", "断层力学"], "difficulty": "hard"},
    {"question_id": 72, "title": "海洋环流如何影响全球气候？", "title_en": "How do ocean currents affect global climate?", "category": "海洋学", "description": "AMOC减弱对北大西洋气候和全球热量分配的潜在影响及临界点风险。", "keywords": ["海洋环流", "AMOC", "气候系统"], "difficulty": "medium"},
    {"question_id": 73, "title": "碳循环的反馈机制有多强？", "title_en": "How strong are carbon cycle feedbacks?", "category": "气候科学", "description": "永久冻土融化、森林退化和海洋酸化对大气CO2浓度的正反馈量化。", "keywords": ["碳循环", "气候反馈", "碳汇"], "difficulty": "medium"},
    {"question_id": 74, "title": "生物地球化学循环如何被人类改变？", "title_en": "How have biogeochemical cycles been altered by humans?", "category": "地球化学", "description": "氮磷循环的人为扰动对水体富营养化、温室气体排放和生态系统的影响。", "keywords": ["生物地球化学", "氮循环", "人类世"], "difficulty": "medium"},
    {"question_id": 75, "title": "地下水的可持续管理策略是什么？", "title_en": "What are sustainable groundwater management strategies?", "category": "水文学", "description": "含水层补给、咸淡水界面管理和跨界地下水治理的制度与技术挑战。", "keywords": ["地下水", "水资源", "可持续性"], "difficulty": "medium"},
    {"question_id": 76, "title": "极端天气事件的归因方法可靠吗？", "title_en": "Are extreme event attribution methods reliable?", "category": "气候科学", "description": "气候变化对特定极端事件的贡献度量化方法和不确定性传播。", "keywords": ["极端天气", "归因分析", "气候变化"], "difficulty": "medium"},
    {"question_id": 77, "title": "深海生态系统的功能和脆弱性？", "title_en": "Functions and vulnerability of deep-sea ecosystems?", "category": "海洋生物学", "description": "热液喷口、冷泉和海山生物群落的能量基础和采矿活动的生态风险。", "keywords": ["深海", "热液喷口", "深海采矿"], "difficulty": "medium"},
    {"question_id": 78, "title": "土壤退化如何逆转？", "title_en": "How to reverse soil degradation?", "category": "土壤科学", "description": "侵蚀、盐渍化和有机质流失的修复技术及生态农业的实践效果。", "keywords": ["土壤退化", "土地修复", "可持续农业"], "difficulty": "medium"},
    {"question_id": 79, "title": "北极变化的全球影响是什么？", "title_en": "What are the global impacts of Arctic change?", "category": "极地科学", "description": "海冰消退、甲烷释放和中纬度天气异常之间的遥相关机制。", "keywords": ["北极", "海冰", "极地放大"], "difficulty": "medium"},
    {"question_id": 80, "title": "火山喷发的预警时间能延长多久？", "title_en": "How far can volcanic eruption warning time be extended?", "category": "火山学", "description": "岩浆上升信号的多参数监测和机器学习预警模型的精度提升空间。", "keywords": ["火山预警", "岩浆动力学", "灾害预防"], "difficulty": "medium"},

    # --- 数学与计算机科学 ---
    {"question_id": 81, "title": "P=NP问题能否被解决？", "title_en": "Can P=NP be resolved?", "category": "计算机科学", "description": "计算复杂性理论的核心问题，对密码学、优化和人工智能有深远影响。", "keywords": ["P vs NP", "计算复杂性", "算法"], "difficulty": "hard"},
    {"question_id": 82, "title": "黎曼猜想是否成立？", "title_en": "Is the Riemann hypothesis true?", "category": "数学", "description": "素数分布规律的核心猜想，其证明将深刻影响数论和密码学。", "keywords": ["黎曼猜想", "素数", "解析数论"], "difficulty": "hard"},
    {"question_id": 83, "title": "纳维-斯托克斯方程是否有光滑解？", "title_en": "Do Navier-Stokes equations have smooth solutions?", "category": "数学/流体力学", "description": "千禧年大奖难题之一，三维不可压缩流体方程的正则性问题。", "keywords": ["N-S方程", "千禧年问题", "偏微分方程"], "difficulty": "hard"},
    {"question_id": 84, "title": "量子计算的优势边界在哪里？", "title_en": "Where are the boundaries of quantum advantage?", "category": "量子计算", "description": "哪些实际问题能从量子加速中获益？纠错码和容错阈值的工程挑战。", "keywords": ["量子计算", "量子优势", "量子纠错"], "difficulty": "hard"},
    {"question_id": 85, "title": "深度学习的理论基础是什么？", "title_en": "What is the theoretical foundation of deep learning?", "category": "AI/机器学习", "description": "过参数化网络的泛化能力、损失景观几何和优化动力学的数学解释。", "keywords": ["深度学习", "泛化理论", "神经网络"], "difficulty": "hard"},
    {"question_id": 86, "title": "随机性的本质是什么？", "title_en": "What is the nature of randomness?", "category": "数学/哲学", "description": "算法随机性、物理随机性和认识论不确定性的统一框架。", "keywords": ["随机性", "概率论", "混沌"], "difficulty": "hard"},
    {"question_id": 87, "title": "连续统假设是否为真？", "title_en": "Is the continuum hypothesis true?", "category": "数学", "description": "哥德尔和科恩证明了CH在ZFC中的独立性，是否需要新的公理？", "keywords": ["连续统假设", "集合论", "公理系统"], "difficulty": "hard"},
    {"question_id": 88, "title": "网络安全能否被数学保证？", "title_en": "Can cybersecurity be mathematically guaranteed?", "category": "计算机科学", "description": "形式化验证、同态加密和后量子密码在实际系统中的可行性和性能代价。", "keywords": ["网络安全", "形式化验证", "密码学"], "difficulty": "medium"},
    {"question_id": 89, "title": "复杂系统的涌现行为能否被预测？", "title_en": "Can emergent behavior of complex systems be predicted?", "category": "复杂系统", "description": "从微观规则到宏观模式的映射是否存在普适的计算方法？", "keywords": ["涌现", "复杂系统", "自组织"], "difficulty": "hard"},
    {"question_id": 90, "title": "自然语言理解的极限在哪里？", "title_en": "What are the limits of natural language understanding?", "category": "AI/NLP", "description": "统计模式匹配是否能达到真正的语义理解？常识推理和世界知识的瓶颈。", "keywords": ["NLU", "语义理解", "常识推理"], "difficulty": "medium"},

    # --- 能源与技术 ---
    {"question_id": 91, "title": "可控核聚变何时能实现商用？", "title_en": "When will commercial fusion power be achieved?", "category": "能源科学", "description": "托卡马克、仿星器和惯性约束的技术路线比较和经济可行性时间表。", "keywords": ["核聚变", "ITER", "清洁能源"], "difficulty": "hard"},
    {"question_id": 92, "title": "高效储能技术的突破方向？", "title_en": "Breakthrough directions for efficient energy storage?", "category": "能源科学", "description": "固态电池、液流电池、氢储能和重力储能的能量密度、寿命和成本权衡。", "keywords": ["储能", "电池", "氢能"], "difficulty": "medium"},
    {"question_id": 93, "title": "碳捕获与封存技术是否可行？", "title_en": "Is carbon capture and sequestration viable?", "category": "环境工程", "description": "直接空气捕获、矿物碳化和生物固碳的成本、规模和长期安全性评估。", "keywords": ["CCS", "碳中和", "负排放"], "difficulty": "medium"},
    {"question_id": 94, "title": "氢经济的瓶颈在哪里？", "title_en": "Where are the bottlenecks of hydrogen economy?", "category": "能源科学", "description": "绿氢制备效率、储运安全和燃料电池成本的系统性障碍分析。", "keywords": ["氢能", "电解水", "燃料电池"], "difficulty": "medium"},
    {"question_id": 95, "title": "核废料的安全处置方案？", "title_en": "Safe disposal solutions for nuclear waste?", "category": "核工程", "description": "深层地质处置库的长期安全性和公众接受度的双重挑战。", "keywords": ["核废料", "地质处置", "放射性"], "difficulty": "medium"},

    # --- 医学与健康 ---
    {"question_id": 96, "title": "阿尔茨海默病的病因和治疗靶点？", "title_en": "Etiology and therapeutic targets of Alzheimer's disease?", "category": "神经退行性疾病", "description": "淀粉样蛋白假说的困境和tau蛋白、神经炎症、代谢等新方向的进展。", "keywords": ["阿尔茨海默", "Aβ", "tau蛋白"], "difficulty": "hard"},
    {"question_id": 97, "title": "个性化癌症疫苗能否实现？", "title_en": "Can personalized cancer vaccines be realized?", "category": "肿瘤免疫", "description": "新抗原预测、mRNA疫苗平台和联合免疫治疗的临床验证进展。", "keywords": ["癌症疫苗", "新抗原", "mRNA疫苗"], "difficulty": "medium"},
    {"question_id": 98, "title": "基因编辑的脱靶效应如何消除？", "title_en": "How to eliminate off-target effects of gene editing?", "category": "基因治疗", "description": "CRISPR-Cas9的高保真变体和碱基编辑器的精确性和安全性评估。", "keywords": ["CRISPR", "基因编辑", "脱靶"], "difficulty": "medium"},
    {"question_id": 99, "title": "器官移植短缺如何解决？", "title_en": "How to solve organ transplant shortage?", "category": "再生医学", "description": "异种移植、3D生物打印和类器官培养的技术成熟度和免疫排斥挑战。", "keywords": ["器官移植", "异种移植", "生物打印"], "difficulty": "medium"},
    {"question_id": 100, "title": "心理健康的客观诊断标准？", "title_en": "Objective diagnostic criteria for mental health?", "category": "精神医学", "description": "影像学和电生理标志物能否替代主观量表实现精神疾病的精准分类？", "keywords": ["精神健康", "诊断标准", "生物标志物"], "difficulty": "medium"},

    # --- 社会科学与技术交叉 ---
    {"question_id": 101, "title": "人工智能的对齐问题如何解决？", "title_en": "How to solve AI alignment problem?", "category": "AI安全", "description": "如何确保超级智能的目标函数与人类价值观一致？可解释性和价值学习的瓶颈。", "keywords": ["AI对齐", "价值学习", "AI安全"], "difficulty": "hard"},
    {"question_id": 102, "title": "隐私保护与数据利用如何平衡？", "title_en": "How to balance privacy protection and data utilization?", "category": "信息技术/法学", "description": "差分隐私、联邦学习和安全多方计算在实际应用中的效用-隐私权衡。", "keywords": ["隐私计算", "差分隐私", "数据治理"], "difficulty": "medium"},
    {"question_id": 103, "title": "社交媒体的信息茧房如何打破？", "title_en": "How to break filter bubbles in social media?", "category": "信息科学/社会学", "description": "推荐算法的多样性干预和用户自主性的制度保障方案。", "keywords": ["信息茧房", "推荐算法", "信息多样性"], "difficulty": "medium"},
    {"question_id": 104, "title": "自动驾驶的道德决策框架？", "title_en": "Ethical decision framework for autonomous driving?", "category": "AI伦理", "description": "电车难题的现实版本：事故不可避免时算法应如何分配风险？", "keywords": ["自动驾驶", "AI伦理", "道德决策"], "difficulty": "medium"},
    {"question_id": 105, "title": "全球化与本土化的张力如何调和？", "title_en": "How to reconcile globalization-localization tension?", "category": "社会科学", "description": "技术标准统一与文化多样性的共存机制和国际治理框架改革。", "keywords": ["全球化", "本土化", "国际治理"], "difficulty": "medium"},

    # --- 更多跨学科问题 ---
    {"question_id": 106, "title": "时间的箭头从何而来？", "title_en": "Where does the arrow of time come from?", "category": "物理学/哲学", "description": "热力学第二定律、宇宙初始条件和量子测量之间的深层联系。", "keywords": ["时间箭头", "熵", "热力学"], "difficulty": "hard"},
    {"question_id": 107, "title": "自由意志是否存在？", "title_en": "Does free will exist?", "category": "神经科学/哲学", "description": "Libet实验的解读争议和相容论在神经科学时代的重新定位。", "keywords": ["自由意志", "决定论", "神经科学"], "difficulty": "hard"},
    {"question_id": 108, "title": "数学是被发现的还是被发明的？", "title_en": "Is mathematics discovered or invented?", "category": "数学哲学", "description": "柏拉图主义、形式主义和建构主义在当代数学实践中的证据。", "keywords": ["数学哲学", "柏拉图主义", "数学实在论"], "difficulty": "medium"},
    {"question_id": 109, "title": "意识的硬问题能否被科学解答？", "title_en": "Can the hard problem of consciousness be solved scientifically?", "category": "心灵哲学/神经科学", "description": "Chalmers的硬问题vs软问题区分是否有效？整合信息理论的检验。", "keywords": ["意识硬问题", "Chalmers", "IIT"], "difficulty": "hard"},
    {"question_id": 110, "title": "道德判断是否有普遍的生物学基础？", "title_en": "Is there a universal biological basis for moral judgment?", "category": "进化伦理学", "description": "跨文化道德直觉的共同模式和双过程道德判断模型的实证检验。", "keywords": ["道德", "进化伦理", "道德心理学"], "difficulty": "medium"},
    {"question_id": 111, "title": "创造力可以被理解和培养吗？", "title_en": "Can creativity be understood and cultivated?", "category": "认知科学/教育学", "description": "发散思维、远距离联想和默认网络的神经基础及教育干预效果。", "keywords": ["创造力", "发散思维", "创新教育"], "difficulty": "medium"},
    {"question_id": 112, "title": "集体智慧超越个体智慧的条件？", "title_en": "Conditions under which collective intelligence surpasses individual?", "category": "复杂系统/管理学", "description": "多样性、独立性和聚合机制在群体决策和问题求解中的最优配置。", "keywords": ["集体智慧", "群体决策", "众包"], "difficulty": "medium"},
    {"question_id": 113, "title": "经济增长的物理极限是什么？", "title_en": "What are the physical limits of economic growth?", "category": "生态经济学", "description": "热力学约束、资源耗竭和生态承载力对无限增长范式的挑战。", "keywords": ["增长极限", "生态经济学", "可持续性"], "difficulty": "medium"},
    {"question_id": 114, "title": "教育的本质目标应该是什么？", "title_en": "What should be the essential goal of education?", "category": "教育学/哲学", "description": "知识传授、能力培养和人格塑造的优先序在AI时代的重新审视。", "keywords": ["教育目标", "核心素养", "AI时代教育"], "difficulty": "medium"},
    {"question_id": 115, "title": "公平与效率的永恒权衡能否被超越？", "title_en": "Can the eternal equity-efficiency tradeoff be transcended?", "category": "经济学/政治哲学", "description": "制度创新和技术进步是否创造了同时改善公平与效率的新可能？", "keywords": ["公平效率", "制度设计", "分配正义"], "difficulty": "medium"},
    {"question_id": 116, "title": "文化的进化遵循什么规律？", "title_en": "What laws govern cultural evolution?", "category": "文化进化", "description": "文化传播的选择压力、漂变和创新机制能否建立类似生物进化的定量理论？", "keywords": ["文化进化", "模因", "文化选择"], "difficulty": "medium"},
    {"question_id": 117, "title": "城市的最佳规模是多少？", "title_en": "What is the optimal size of cities?", "category": "城市科学", "description": "规模报酬递增与拥挤成本的平衡点和智慧城市技术的调节作用。", "keywords": ["城市规模", "规模法则", "城市规划"], "difficulty": "medium"},
    {"question_id": 118, "title": "食物系统如何实现可持续转型？", "title_en": "How to achieve sustainable food system transformation?", "category": "农业/环境", "description": "减少浪费、替代蛋白和再生农业的综合路径和政策杠杆。", "keywords": ["食物系统", "可持续农业", "食品安全"], "difficulty": "medium"},
    {"question_id": 119, "title": "淡水资源危机如何应对？", "title_en": "How to address freshwater crisis?", "category": "水资源", "description": "海水淡化、废水回用和虚拟水贸易的技术经济分析和地缘政治影响。", "keywords": ["水资源", "海水淡化", "水安全"], "difficulty": "medium"},
    {"question_id": 120, "title": "塑料污染的终极解决方案？", "title_en": "Ultimate solution to plastic pollution?", "category": "环境科学", "description": "可降解材料、化学回收和循环经济模式的系统集成和规模化障碍。", "keywords": ["塑料污染", "循环经济", "可降解材料"], "difficulty": "medium"},
    {"question_id": 121, "title": "太空探索的伦理边界在哪里？", "title_en": "Where are the ethical boundaries of space exploration?", "category": "太空伦理", "description": "行星保护、太空资源开采权和太空殖民的道德框架。", "keywords": ["太空伦理", "行星保护", "太空治理"], "difficulty": "medium"},
    {"question_id": 122, "title": "长寿研究的伦理和社会影响？", "title_en": "Ethical and social implications of longevity research?", "category": "生物伦理学", "description": "寿命延长对人口结构、资源分配和代际公平的冲击及政策应对。", "keywords": ["长寿", "抗衰老", "生物伦理"], "difficulty": "medium"},
    {"question_id": 123, "title": "人机融合的界限应该划在哪里？", "title_en": "Where should the boundary of human-machine integration be drawn?", "category": "技术伦理", "description": "脑机接口、基因增强和外骨骼技术对人类身份认同和社会公平的挑战。", "keywords": ["人机融合", "增强技术", "后人类"], "difficulty": "medium"},
    {"question_id": 124, "title": "科学本身是否有方法论的极限？", "title_en": "Does science itself have methodological limits?", "category": "科学哲学", "description": "还原论的适用边界、观察者的嵌入性和不可计算现象对科学方法的挑战。", "keywords": ["科学方法", "还原论", "科学哲学"], "difficulty": "hard"},
    {"question_id": 125, "title": "人类文明的长期存续取决于什么？", "title_en": "What determines the long-term survival of human civilization?", "category": "未来学/跨学科", "description": "存在性风险的识别、全球治理能力的提升和多行星备份的可行性综合评估。", "keywords": ["文明存续", "存在性风险", "全球治理"], "difficulty": "hard"},
]

async def seed():
    print('='*60)
    print(f'🌱 准备插入 {len(SEED_QUESTIONS)} 道 Science 125 科学问题')
    print('='*60)

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select, func
        count = (await db.execute(select(func.count()).select_from(ScienceQuestion))).scalar()
        if count > 0:
            print(f'   ⚠️ science_questions 已有 {count} 条数据，先清空...')
            await db.execute(ScienceQuestion.__table__.delete())
            await db.commit()
            print(f'   ✅ 已清空旧数据')

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
                source="science_125",
                is_active=True,
                sort_order=i,
            )
            questions.append(sq)

        db.add_all(questions)
        await db.commit()
        print(f'   ✅ 成功插入 {len(questions)} 道 Science 125 问题')

        # 按类别统计
        rows = await db.execute(
            select(ScienceQuestion.category, func.count())
            .group_by(ScienceQuestion.category)
            .order_by(func.count().desc())
        )
        print(f'\n   📊 按类别分布:')
        for cat, cnt in rows.fetchall():
            print(f'      {cat}: {cnt} 题')

        # 按难度统计
        rows = await db.execute(
            select(ScienceQuestion.difficulty, func.count())
            .group_by(ScienceQuestion.difficulty)
        )
        print(f'\n   📊 按难度分布:')
        for diff, cnt in rows.fetchall():
            print(f'      {diff}: {cnt} 题')

    print(f'\n✅ Science 125 种子数据插入完成！')

asyncio.run(seed())
